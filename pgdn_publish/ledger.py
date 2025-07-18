"""
Blockchain ledger publishing functionality.
"""

import json
import time
import os
import importlib.resources
from typing import Dict, Any, Optional
from web3 import Web3
from web3.contract import Contract
from web3.exceptions import ContractLogicError
from eth_account import Account

from .config import PublisherConfig


class LedgerError(Exception):
    """Custom exception for ledger publishing errors."""
    pass


class LedgerPublisher:
    """Publisher for blockchain ledger operations."""
    
    def __init__(self, config: PublisherConfig, skip_auth_check: bool = False):
        """Initialize ledger publisher."""
        self.config = config
        self.config.validate()
        
        # Initialize Web3 connection
        self.w3 = Web3(Web3.HTTPProvider(config.rpc_url))
        if not self.w3.is_connected():
            raise LedgerError(f"Failed to connect to RPC at {config.rpc_url}")
        
        # Initialize account
        self.account = Account.from_key(config.private_key)
        self.contract_address = Web3.to_checksum_address(config.contract_address)
        
        # Load contract ABI
        self.contract_abi = self._load_contract_abi()
        self.contract: Contract = self.w3.eth.contract(
            address=self.contract_address,
            abi=self.contract_abi
        )
        
        # Check authorization (can be skipped for diagnostic purposes)
        if not skip_auth_check:
            self._check_authorization()
    
    def _load_contract_abi(self) -> list:
        """Load contract ABI from package resources."""
        try:
            # Try to load from package resources first
            try:
                with importlib.resources.open_text('pgdn_publish.contracts.ledger', 'abi.json') as f:
                    return json.load(f)
            except (FileNotFoundError, ImportError):
                # Fallback to file system for development
                abi_paths = [
                    'contracts/ledger/abi.json',
                    '../contracts/ledger/abi.json',
                    'pgdn_publish/contracts/ledger/abi.json',
                ]
                
                for abi_path in abi_paths:
                    try:
                        with open(abi_path, 'r') as f:
                            return json.load(f)
                    except FileNotFoundError:
                        continue
                        
        except Exception as e:
            raise LedgerError(f"Failed to load contract ABI: {e}")
        
        raise LedgerError("Contract ABI file not found")
    
    def _check_authorization(self):
        """Check if account is authorized to publish."""
        try:
            # First, verify that the contract exists and has code
            contract_code = self.w3.eth.get_code(self.contract_address)
            if contract_code == b'\x00' or len(contract_code) == 0:
                raise LedgerError(f"No contract deployed at address {self.contract_address}")
            
            # Check if account is owner
            try:
                owner = self.contract.functions.owner().call()
                self.is_owner = self.account.address.lower() == owner.lower()
            except Exception as e:
                raise LedgerError(f"Failed to call owner() function: {e}. Contract may not implement Ownable interface.")
            
            # Check if account is authorized publisher
            try:
                self.is_publisher = self.contract.functions.authorizedPublishers(self.account.address).call()
            except Exception as e:
                raise LedgerError(f"Failed to call authorizedPublishers() function: {e}. Contract may not implement publisher authorization.")
            
            if not (self.is_owner or self.is_publisher):
                raise LedgerError(f"Account {self.account.address} not authorized to publish. Owner: {self.is_owner}, Publisher: {self.is_publisher}")
                
        except LedgerError:
            raise
        except Exception as e:
            raise LedgerError(f"Authorization check failed: {e}")
    
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
        
        summary_hash = self._generate_summary_hash(summary_data)
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
                raise LedgerError("Could not get raw transaction")
            
            tx_hash = self.w3.eth.send_raw_transaction(raw_transaction)
            return tx_hash.hex()
            
        except Exception as e:
            raise LedgerError(f"Transaction failed: {e}")
    
    def _wait_for_confirmation(self, tx_hash: str, timeout: int = 120) -> Dict[str, Any]:
        """Wait for transaction confirmation."""
        try:
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
            
            if receipt.status == 0:
                raise LedgerError(f"Transaction failed: {tx_hash}")
            
            return dict(receipt)
            
        except Exception as e:
            raise LedgerError(f"Transaction confirmation failed: {e}")
    
    def publish(self, scan_result: Dict[str, Any], wait_for_confirmation: bool = True) -> Dict[str, Any]:
        """Publish scan result to blockchain ledger."""
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
                'confirmed': False
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
            raise LedgerError(f"Contract error: {e}")
        except Exception as e:
            raise LedgerError(f"Publication failed: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get ledger connection status."""
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
                'error': str(e)
            }

    def diagnose_connection(self) -> Dict[str, Any]:
        """Comprehensive diagnostic information for debugging connection issues."""
        diagnostics = {
            'timestamp': time.time(),
            'config': {
                'rpc_url': self.config.rpc_url,
                'contract_address': self.contract_address,
                'account_address': self.account.address,
                'gas_limit': self.config.gas_limit,
                'gas_price_gwei': self.config.gas_price_gwei
            },
            'tests': {}
        }
        
        # Test 1: RPC Connection
        try:
            is_connected = self.w3.is_connected()
            latest_block = self.w3.eth.block_number if is_connected else None
            chain_id = self.w3.eth.chain_id if is_connected else None
            
            diagnostics['tests']['rpc_connection'] = {
                'success': is_connected,
                'latest_block': latest_block,
                'chain_id': chain_id,
                'error': None if is_connected else 'RPC connection failed'
            }
        except Exception as e:
            diagnostics['tests']['rpc_connection'] = {
                'success': False,
                'error': str(e)
            }
        
        # Test 2: Account Balance
        try:
            balance = self.w3.eth.get_balance(self.account.address)
            diagnostics['tests']['account_balance'] = {
                'success': True,
                'balance_wei': balance,
                'balance_eth': float(self.w3.from_wei(balance, 'ether')),
                'error': None
            }
        except Exception as e:
            diagnostics['tests']['account_balance'] = {
                'success': False,
                'error': str(e)
            }
        
        # Test 3: Contract Existence
        try:
            contract_code = self.w3.eth.get_code(self.contract_address)
            has_code = len(contract_code) > 0 and contract_code != b'\x00'
            
            diagnostics['tests']['contract_existence'] = {
                'success': has_code,
                'has_code': has_code,
                'code_size': len(contract_code),
                'error': None if has_code else 'No contract code at specified address'
            }
        except Exception as e:
            diagnostics['tests']['contract_existence'] = {
                'success': False,
                'error': str(e)
            }
        
        # Test 4: Contract Interface
        try:
            # Test basic contract calls
            tests = {}
            
            # Test owner() function
            try:
                owner = self.contract.functions.owner().call()
                tests['owner'] = {'success': True, 'value': owner}
            except Exception as e:
                tests['owner'] = {'success': False, 'error': str(e)}
            
            # Test authorizedPublishers() function
            try:
                is_publisher = self.contract.functions.authorizedPublishers(self.account.address).call()
                tests['authorized_publishers'] = {'success': True, 'value': is_publisher}
            except Exception as e:
                tests['authorized_publishers'] = {'success': False, 'error': str(e)}
            
            # Test getContractInfo() function if available
            try:
                if hasattr(self.contract.functions, 'getContractInfo'):
                    info = self.contract.functions.getContractInfo().call()
                    tests['contract_info'] = {'success': True, 'value': info}
                else:
                    tests['contract_info'] = {'success': False, 'error': 'Function not available'}
            except Exception as e:
                tests['contract_info'] = {'success': False, 'error': str(e)}
            
            diagnostics['tests']['contract_interface'] = {
                'success': any(test['success'] for test in tests.values()),
                'function_tests': tests
            }
            
        except Exception as e:
            diagnostics['tests']['contract_interface'] = {
                'success': False,
                'error': str(e)
            }
        
        # Test 5: Authorization
        try:
            self._check_authorization()
            diagnostics['tests']['authorization'] = {
                'success': True,
                'is_owner': getattr(self, 'is_owner', False),
                'is_publisher': getattr(self, 'is_publisher', False),
                'error': None
            }
        except Exception as e:
            diagnostics['tests']['authorization'] = {
                'success': False,
                'error': str(e)
            }
        
        # Overall status
        all_tests = diagnostics['tests']
        diagnostics['overall_status'] = {
            'healthy': all(test.get('success', False) for test in all_tests.values()),
            'total_tests': len(all_tests),
            'passed_tests': sum(1 for test in all_tests.values() if test.get('success', False)),
            'failed_tests': sum(1 for test in all_tests.values() if not test.get('success', False))
        }
        
        return diagnostics


def publish_to_ledger(scan_result: Dict[str, Any], config: Optional[PublisherConfig] = None) -> Dict[str, Any]:
    """
    Convenience function to publish a single scan result to the ledger.
    
    Args:
        scan_result: Scan result data to publish
        config: Publisher configuration (defaults to environment config)
    
    Returns:
        Publication result dictionary
    """
    if config is None:
        config = PublisherConfig.from_env()
    
    publisher = LedgerPublisher(config)
    return publisher.publish(scan_result)


def diagnose_ledger_connection(config: Optional[PublisherConfig] = None) -> Dict[str, Any]:
    """
    Diagnose ledger connection issues without performing authorization checks.
    
    Args:
        config: Publisher configuration (defaults to environment config)
    
    Returns:
        Diagnostic information dictionary
    """
    if config is None:
        config = PublisherConfig.from_env()
    
    try:
        # Create publisher without authorization check for diagnostic purposes
        publisher = LedgerPublisher(config, skip_auth_check=True)
        return publisher.diagnose_connection()
    except Exception as e:
        return {
            'success': False,
            'error': f"Failed to create diagnostic connection: {e}",
            'config': {
                'rpc_url': config.rpc_url,
                'contract_address': config.contract_address,
                'account_address': 'unknown'
            }
        }