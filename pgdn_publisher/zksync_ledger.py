"""
zkSync blockchain ledger publishing functionality.
"""

import json
import time
import os
from typing import Dict, Any, Optional
from web3 import Web3
from web3.contract import Contract
from web3.exceptions import ContractLogicError
from eth_account import Account

from .config import PublisherConfig


class ZkSyncLedgerError(Exception):
    """Custom exception for zkSync ledger publishing errors."""
    pass


class ZkSyncLedgerPublisher:
    """Publisher for zkSync blockchain ledger operations."""
    
    def __init__(self, config: PublisherConfig):
        """Initialize zkSync ledger publisher."""
        self.config = config
        self.config.validate()
        
        # Initialize Web3 connection
        self.w3 = Web3(Web3.HTTPProvider(config.rpc_url))
        if not self.w3.is_connected():
            raise ZkSyncLedgerError(f"Failed to connect to RPC at {config.rpc_url}")
        
        # Initialize account
        self.account = Account.from_key(config.private_key)
        self.contract_address = Web3.to_checksum_address(config.contract_address)
        
        # Load contract ABI
        self.contract_abi = self._load_contract_abi()
        self.contract: Contract = self.w3.eth.contract(
            address=self.contract_address,
            abi=self.contract_abi
        )
        
        # Check authorization
        self._check_authorization()
    
    def _load_contract_abi(self) -> list:
        """Load contract ABI from file."""
        abi_paths = [
            'contracts/ledger/abi.json',
            '../contracts/ledger/abi.json',
            'lib/contracts/ledger/abi.json',
        ]
        
        for abi_path in abi_paths:
            try:
                with open(abi_path, 'r') as f:
                    return json.load(f)
            except FileNotFoundError:
                continue
        
        raise ZkSyncLedgerError("Contract ABI file not found")
    
    def _check_authorization(self):
        """Check if account is authorized to publish."""
        try:
            # Check if account is owner
            owner = self.contract.functions.owner().call()
            self.is_owner = self.account.address.lower() == owner.lower()
            
            # Check if account is authorized publisher
            self.is_publisher = self.contract.functions.authorizedPublishers(self.account.address).call()
            
            if not (self.is_owner or self.is_publisher):
                raise ZkSyncLedgerError(f"Account {self.account.address} not authorized to publish")
                
        except Exception as e:
            raise ZkSyncLedgerError(f"Authorization check failed: {e}")
    
    def _generate_summary_hash(self, scan_data: Dict[str, Any]) -> str:
        """Generate deterministic hash for scan summary."""
        summary_data = {
            'hostUid': scan_data.get('host_uid', ''),
            'scanTime': scan_data.get('scan_time', 0),
            'score': scan_data.get('trust_score', 0),
            'reportPointer': scan_data.get('report_pointer', ''),
            'testData': False
        }
        
        json_str = json.dumps(summary_data, sort_keys=True, separators=(',', ':'))
        hash_bytes = self.w3.keccak(text=json_str)
        return '0x' + hash_bytes.hex()
    
    def _format_scan_for_ledger(self, scan_result: Dict[str, Any]) -> Dict[str, Any]:
        """Format scan result for blockchain submission."""
        host_uid = scan_result.get('host_uid') or scan_result.get('validator_id', 'unknown_host')
        scan_time = scan_result.get('scan_time') or int(time.time())
        trust_score = max(0, min(65535, int(scan_result.get('trust_score', 0))))
        
        summary_data = {
            'host_uid': host_uid,
            'scan_time': scan_time,
            'trust_score': trust_score,
            'vulnerabilities': scan_result.get('vulnerabilities', []),
            'open_ports': scan_result.get('open_ports', []),
            'services': scan_result.get('services', []),
            'ssl_info': scan_result.get('ssl_info', {}),
            'scan_type': scan_result.get('scan_type', 'unknown')
        }
        
        # Require summary_hash to be provided
        summary_hash = scan_result.get('summary_hash')
        if not summary_hash:
            raise ZkSyncLedgerError("summary_hash is required in scan data")
        
        report_pointer = scan_result.get('report_pointer') or f"scan_{scan_result.get('scan_id', 'unknown')}_{int(time.time())}"
        
        return {
            'host_uid': host_uid,
            'scan_time': scan_time,
            'summary_hash': summary_hash,
            'score': trust_score,
            'report_pointer': report_pointer,
            'summary_data': summary_data
        }
    
    def _send_transaction(self, function_call, gas_limit: Optional[int] = None) -> str:
        """Send transaction to contract."""
        try:
            nonce = self.w3.eth.get_transaction_count(self.account.address, 'pending')
            
            if gas_limit is None:
                try:
                    estimated_gas = function_call.estimate_gas({'from': self.account.address})
                    gas_limit = int(estimated_gas * 1.2)  # 20% buffer
                except Exception:
                    gas_limit = self.config.gas_limit
            
            transaction_params = {
                'from': self.account.address,
                'nonce': nonce,
                'gas': gas_limit,
                'gasPrice': self.w3.to_wei(self.config.gas_price_gwei, 'gwei'),
            }
            
            transaction = function_call.build_transaction(transaction_params)
            signed_txn = self.account.sign_transaction(transaction)
            
            raw_transaction = getattr(signed_txn, 'rawTransaction', None) or getattr(signed_txn, 'raw_transaction', None)
            if raw_transaction is None:
                raise ZkSyncLedgerError("Could not get raw transaction")
            
            tx_hash = self.w3.eth.send_raw_transaction(raw_transaction)
            return tx_hash.hex()
            
        except Exception as e:
            raise ZkSyncLedgerError(f"Transaction failed: {e}")
    
    def _wait_for_confirmation(self, tx_hash: str, timeout: int = 120) -> Dict[str, Any]:
        """Wait for transaction confirmation."""
        try:
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
            
            if receipt.status == 0:
                raise ZkSyncLedgerError(f"Transaction failed: {tx_hash}")
            
            return dict(receipt)
            
        except Exception as e:
            raise ZkSyncLedgerError(f"Transaction confirmation failed: {e}")
    
    def publish(self, scan_result: Dict[str, Any], wait_for_confirmation: bool = True) -> Dict[str, Any]:
        """Publish scan result to zkSync blockchain ledger."""
        try:
            # Format scan data
            ledger_data = self._format_scan_for_ledger(scan_result)
            
            # Convert summary hash to bytes32
            summary_hash_bytes = bytes.fromhex(ledger_data['summary_hash'][2:])
            
            # Create function call
            function_call = self.contract.functions.publishScanSummary(
                ledger_data['host_uid'],
                ledger_data['scan_time'],
                summary_hash_bytes,
                ledger_data['score'],
                ledger_data['report_pointer']
            )
            
            # Send transaction
            tx_hash = self._send_transaction(function_call)
            
            result = {
                'success': True,
                'transaction_hash': tx_hash,
                'summary_hash': ledger_data['summary_hash'],
                'host_uid': ledger_data['host_uid'],
                'score': ledger_data['score'],
                'confirmed': False,
                'network': 'zksync'
            }
            
            # Wait for confirmation if requested
            if wait_for_confirmation:
                try:
                    receipt = self._wait_for_confirmation(tx_hash)
                    result.update({
                        'confirmed': True,
                        'block_number': receipt['blockNumber'],
                        'gas_used': receipt['gasUsed']
                    })
                except Exception as e:
                    # Transaction sent but confirmation failed
                    result['confirmation_error'] = str(e)
            
            return result
            
        except ContractLogicError as e:
            raise ZkSyncLedgerError(f"Contract error: {e}")
        except Exception as e:
            raise ZkSyncLedgerError(f"Publication failed: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get zkSync ledger connection status."""
        try:
            balance = self.w3.eth.get_balance(self.account.address)
            
            contract_info = {}
            try:
                if hasattr(self.contract.functions, 'getContractInfo'):
                    result = self.contract.functions.getContractInfo().call()
                    contract_info = {
                        'version': result[0],
                        'is_paused': result[1],
                        'total_summaries': result[2],
                        'publish_cooldown': result[3],
                        'reputation_threshold': result[4],
                        'active_hosts': result[5]
                    }
            except:
                pass
            
            return {
                'connected': True,
                'network': 'zksync',
                'rpc_url': self.config.rpc_url,
                'contract_address': self.contract_address,
                'account_address': self.account.address,
                'balance_wei': balance,
                'balance_eth': float(self.w3.from_wei(balance, 'ether')),
                'is_publisher': getattr(self, 'is_publisher', False),
                'is_owner': getattr(self, 'is_owner', False),
                'contract_info': contract_info
            }
            
        except Exception as e:
            return {
                'connected': False,
                'network': 'zksync',
                'error': str(e)
            }