"""
SUI blockchain ledger publishing functionality.
"""

import json
import time
import os
import subprocess
from typing import Dict, Any, Optional

from .config import PublisherConfig


class SuiLedgerError(Exception):
    """Custom exception for SUI ledger publishing errors."""
    pass


class SuiLedgerPublisher:
    """Publisher for SUI blockchain ledger operations."""
    
    def __init__(self, config: PublisherConfig):
        """Initialize SUI ledger publisher."""
        self.config = config
        self.config.validate()
        
        # SUI-specific environment variables
        self.package_id = os.getenv('DEPIN_PACKAGE_ID', '0x799a3a025c5c4e8bfd519b3af06b5f9938ee558cabd6d719074d9899204ba9a1')
        self.registry_id = os.getenv('DEPIN_REGISTRY_ID', '0x4b5944372fab52322eb0c81e8badd89ae88258144bf1c39442629fce5a24fe8d')
        self.admin_cap_id = os.getenv('DEPIN_ADMIN_CAP_ID', '0x6450631886eccff4c71390c6eefa0999b31aafaeea64ca4a3e28bed3ad8f7a2e')
        
        # Check if SUI CLI is available
        self._check_sui_cli()
    
    def _check_sui_cli(self):
        """Check if SUI CLI is available and working."""
        try:
            result = subprocess.run(['sui', 'client', 'envs'], capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                raise SuiLedgerError("SUI CLI not properly configured")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            raise SuiLedgerError("SUI CLI not found. Please install and configure the SUI CLI")
    
    def _format_scan_for_ledger(self, scan_result: Dict[str, Any]) -> Dict[str, Any]:
        """Format scan result for SUI blockchain submission."""
        host_uid = scan_result.get('host_uid') or scan_result.get('validator_id', 'unknown_host')
        scan_time = scan_result.get('scan_time')
        if scan_time is None:
            scan_time = int(time.time() * 1000)  # SUI uses milliseconds
        trust_score = max(0, min(65535, int(scan_result.get('trust_score', 0))))
        
        # Require summary_hash to be provided
        summary_hash = scan_result.get('summary_hash')
        if not summary_hash:
            raise SuiLedgerError("summary_hash is required in scan data")
        
        # Convert summary hash to bytes for SUI
        if summary_hash.startswith('0x'):
            summary_hash = summary_hash[2:]
        
        try:
            summary_hash_bytes = bytes.fromhex(summary_hash)
        except ValueError:
            raise SuiLedgerError(f"Invalid summary_hash format: {summary_hash}")
        
        report_pointer = scan_result.get('report_pointer') or f"scan_{scan_result.get('scan_id', 'unknown')}_{int(time.time())}"
        
        return {
            'host_uid': host_uid,
            'scan_time': scan_time,
            'summary_hash_bytes': summary_hash_bytes,
            'score': trust_score,
            'report_pointer': report_pointer
        }
    
    def _build_sui_command(self, ledger_data: Dict[str, Any]) -> list:
        """Build SUI CLI command for publishing scan summary."""
        summary_hash_array = f"[{','.join(str(b) for b in ledger_data['summary_hash_bytes'])}]"
        
        # Use environment variable directly if available, otherwise use config
        gas_budget = os.getenv('GAS_BUDGET', str(self.config.gas_limit))
        
        # Log the gas budget being used
        print(f"DEBUG: Using gas budget: {gas_budget}")
        print(f"DEBUG: Config gas_limit: {self.config.gas_limit}")
        print(f"DEBUG: GAS_BUDGET env var: {os.getenv('GAS_BUDGET')}")
        
        cmd = [
            "sui", "client", "call", "--json",
            "--package", self.package_id,
            "--module", "validator_scanner_registry",
            "--function", "publish_scan_summary",
            "--args", 
            self.registry_id, 
            self.admin_cap_id, 
            ledger_data['host_uid'], 
            str(ledger_data['scan_time']),
            summary_hash_array, 
            str(ledger_data['score']), 
            ledger_data['report_pointer'], 
            "0x6",
            "--gas-budget", gas_budget
        ]
        
        print(f"DEBUG: Full SUI command: {' '.join(cmd)}")
        return cmd
    
    def _execute_sui_transaction(self, cmd: list) -> Dict[str, Any]:
        """Execute SUI CLI transaction and parse result."""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            # Handle stderr warnings (version mismatches, etc.)
            if result.returncode != 0 and "version mismatch" not in result.stderr:
                raise SuiLedgerError(f"SUI command failed: {result.stderr}")
            
            if not result.stdout.strip():
                raise SuiLedgerError("No output from SUI command")
            
            # Handle known error patterns in stdout
            if "aborted within function" in result.stdout:
                if "code 4" in result.stdout:
                    raise SuiLedgerError("Duplicate hash - scan summary already exists")
                else:
                    raise SuiLedgerError(f"Move function aborted: {result.stdout}")
            
            if "Error executing transaction" in result.stdout:
                raise SuiLedgerError(f"Transaction execution error: {result.stdout}")
            
            # Try to parse JSON output
            try:
                output = json.loads(result.stdout)
                
                # Check for transaction failure in JSON
                effects = output.get("effects", {})
                status = effects.get("status", {})
                
                if status.get("status") == "failure":
                    error = status.get("error", "Unknown error")
                    if "MoveAbort" in str(error) and ", 4)" in str(error):
                        raise SuiLedgerError("Duplicate hash - scan summary already exists")
                    else:
                        raise SuiLedgerError(f"Transaction failed: {error}")
                
                return {
                    'success': True,
                    'digest': output.get('digest', 'unknown'),
                    'effects': effects,
                    'raw_output': output
                }
                
            except json.JSONDecodeError:
                # Handle non-JSON success cases
                if ("Transaction executed successfully" in result.stdout or 
                    result.stdout.strip() and "error" not in result.stdout.lower()):
                    return {
                        'success': True,
                        'message': 'Transaction completed',
                        'raw_output': result.stdout
                    }
                else:
                    raise SuiLedgerError(f"Unexpected output format: {result.stdout}")
                    
        except subprocess.TimeoutExpired:
            raise SuiLedgerError("SUI transaction timed out")
        except Exception as e:
            if isinstance(e, SuiLedgerError):
                raise
            raise SuiLedgerError(f"Unexpected error: {e}")
    
    def publish(self, scan_result: Dict[str, Any], wait_for_confirmation: bool = True) -> Dict[str, Any]:
        """Publish scan result to SUI blockchain ledger."""
        try:
            # Format scan data
            ledger_data = self._format_scan_for_ledger(scan_result)
            
            # Build SUI command
            cmd = self._build_sui_command(ledger_data)
            
            # Execute transaction
            sui_result = self._execute_sui_transaction(cmd)
            
            result = {
                'success': True,
                'transaction_hash': sui_result.get('digest', 'unknown'),
                'summary_hash': '0x' + ledger_data['summary_hash_bytes'].hex(),
                'host_uid': ledger_data['host_uid'],
                'score': ledger_data['score'],
                'confirmed': True,  # SUI CLI waits for confirmation by default
                'network': 'sui',
                'scan_time': ledger_data['scan_time']
            }
            
            if 'effects' in sui_result:
                result['effects'] = sui_result['effects']
            
            return result
            
        except Exception as e:
            raise SuiLedgerError(f"Publication failed: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get SUI ledger connection status."""
        try:
            # Check SUI CLI status
            result = subprocess.run(
                ['sui', 'client', 'active-env'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if result.returncode != 0:
                return {
                    'connected': False,
                    'network': 'sui',
                    'error': 'SUI CLI not properly configured'
                }
            
            active_env = result.stdout.strip()
            
            # Get active address
            addr_result = subprocess.run(
                ['sui', 'client', 'active-address'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            active_address = addr_result.stdout.strip() if addr_result.returncode == 0 else 'unknown'
            
            return {
                'connected': True,
                'network': 'sui',
                'active_environment': active_env,
                'active_address': active_address,
                'package_id': self.package_id,
                'registry_id': self.registry_id,
                'admin_cap_id': self.admin_cap_id
            }
            
        except Exception as e:
            return {
                'connected': False,
                'network': 'sui',
                'error': str(e)
            }