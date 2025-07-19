"""
SUI network ledger implementation.
"""

import os
import json
import time
import hashlib
import subprocess
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from .base import BaseLedgerPublisher
from ..config import PublisherConfig

# Configure logging
logger = logging.getLogger(__name__)


class SuiLedgerError(Exception):
    """Custom exception for SUI ledger publishing errors."""
    pass


@dataclass
class ValidatorData:
    """Data class for validator information"""
    host_uid: str
    trust_score: int
    scan_time: int = None
    summary_hash: bytes = None
    report_pointer: str = ""

    def __post_init__(self):
        if self.scan_time is None:
            self.scan_time = int(time.time() * 1000)
        if self.summary_hash is None:
            data_str = f"{self.host_uid}:{self.trust_score}:{self.scan_time}"
            self.summary_hash = hashlib.sha256(data_str.encode()).digest()
        if not self.report_pointer:
            self.report_pointer = f"validator_{self.host_uid}_{self.scan_time}"


class SuiLedgerPublisher(BaseLedgerPublisher):
    """SUI network ledger publisher."""
    
    def __init__(self, config: PublisherConfig, skip_auth_check: bool = False):
        """Initialize SUI ledger publisher."""
        super().__init__(config, skip_auth_check)
        self.config.validate()
        
        # Get required environment variables for SUI
        self.package_id = os.getenv('PACKAGE_ID')
        self.ledger_id = os.getenv('LEDGER_ID')
        self.publisher_cap_id = os.getenv('PUBLISHER_CAP_ID')
        self.clock_id = os.getenv('CLOCK_ID', '0x6')
        
        # Check required environment variables
        if not skip_auth_check:
            self._check_environment_variables()
    
    def get_network_name(self) -> str:
        """Get the network name."""
        return "sui"
    
    def _check_environment_variables(self):
        """Check if required environment variables are set."""
        if not all([self.package_id, self.ledger_id, self.publisher_cap_id]):
            missing = []
            if not self.package_id:
                missing.append('PACKAGE_ID')
            if not self.ledger_id:
                missing.append('LEDGER_ID')
            if not self.publisher_cap_id:
                missing.append('PUBLISHER_CAP_ID')
            raise SuiLedgerError(f"Missing required environment variables: {', '.join(missing)}")
    
    def _publish_via_cli(self, validator_data: ValidatorData) -> Dict[str, Any]:
        """Publish using sui CLI directly"""
        
        # Convert summary hash to hex string format
        summary_hash_hex = "0x" + validator_data.summary_hash.hex()
        
        # Build sui CLI command
        cmd = [
            "sui", "client", "call",
            "--package", self.package_id,
            "--module", "validator_scanner", 
            "--function", "publish_scan_summary",
            "--args",
            self.ledger_id,
            self.publisher_cap_id,
            validator_data.host_uid,
            str(validator_data.scan_time),
            summary_hash_hex,
            str(min(65535, max(0, validator_data.trust_score))),
            validator_data.report_pointer,
            self.clock_id,
            "--gas-budget", "10000000",
            "--json"
        ]
        
        try:
            logger.info(f"Publishing data for validator {validator_data.host_uid}")
            logger.debug(f"Command: {' '.join(cmd)}")
            
            # Execute the command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # Parse the JSON output
                output = json.loads(result.stdout)
                digest = output.get('digest', 'unknown')
                
                logger.info(f"✅ Successfully published data for validator {validator_data.host_uid}")
                
                return {
                    "success": True,
                    "network": "sui",
                    "transaction_hash": digest,
                    "summary_hash": validator_data.summary_hash.hex(),
                    "host_uid": validator_data.host_uid,
                    "score": validator_data.trust_score,
                    "confirmed": True,
                    "scan_time": validator_data.scan_time,
                    "report_pointer": validator_data.report_pointer
                }
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                logger.error(f"❌ CLI command failed: {error_msg}")
                
                return {
                    "success": False,
                    "network": "sui",
                    "error": error_msg
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "network": "sui",
                "error": "Command timed out after 30 seconds"
            }
        except json.JSONDecodeError:
            return {
                "success": False,
                "network": "sui",
                "error": f"Invalid JSON response: {result.stdout}"
            }
        except Exception as e:
            return {
                "success": False,
                "network": "sui",
                "error": str(e)
            }
    
    def publish_scan(
        self, 
        host_uid: str, 
        trust_score: int, 
        data_hash: str, 
        timestamp: Optional[int] = None
    ) -> Dict[str, Any]:
        """Publish scan results to the SUI ledger."""
        try:
            # Create validator data object
            validator_data = ValidatorData(
                host_uid=host_uid,
                trust_score=trust_score
            )
            
            # Override timestamp if provided
            if timestamp is not None:
                validator_data.scan_time = timestamp * 1000  # Convert to milliseconds for SUI
            
            # Override report pointer with data_hash if provided
            if data_hash:
                validator_data.report_pointer = data_hash[:32]  # Truncate if too long
            
            # Publish via CLI
            result = self._publish_via_cli(validator_data)
            
            if not result["success"]:
                raise SuiLedgerError(result["error"])
            
            return result
            
        except SuiLedgerError:
            raise
        except Exception as e:
            raise SuiLedgerError(f"Publication failed: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get SUI ledger connection status."""
        try:
            # Test sui CLI availability
            result = subprocess.run(
                ["sui", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            sui_available = result.returncode == 0
            sui_version = result.stdout.strip() if sui_available else None
            
            # Check environment variables
            env_status = {
                'package_id': bool(self.package_id),
                'ledger_id': bool(self.ledger_id),
                'publisher_cap_id': bool(self.publisher_cap_id),
                'clock_id': bool(self.clock_id)
            }
            
            # Test basic sui client connection
            client_connected = False
            client_error = None
            try:
                client_result = subprocess.run(
                    ["sui", "client", "active-address"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                client_connected = client_result.returncode == 0
                if not client_connected:
                    client_error = client_result.stderr.strip()
            except Exception as e:
                client_error = str(e)
            
            return {
                'connected': sui_available and client_connected and all(env_status.values()),
                'network': self.get_network_name(),
                'sui_cli': {
                    'available': sui_available,
                    'version': sui_version
                },
                'client_connected': client_connected,
                'client_error': client_error,
                'environment_variables': env_status,
                'rpc_url': self.config.get_network_rpc_url()
            }
            
        except Exception as e:
            return {
                'connected': False,
                'network': self.get_network_name(),
                'error': str(e)
            }
    
    def diagnose_connection(self) -> Dict[str, Any]:
        """Comprehensive diagnostic information for debugging SUI connection issues."""
        diagnostics = {
            'timestamp': time.time(),
            'network': self.get_network_name(),
            'config': {
                'package_id': self.package_id,
                'ledger_id': self.ledger_id,
                'publisher_cap_id': self.publisher_cap_id,
                'clock_id': self.clock_id,
                'rpc_url': self.config.get_network_rpc_url()
            },
            'tests': {}
        }
        
        # Test 1: SUI CLI availability
        try:
            result = subprocess.run(
                ["sui", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            diagnostics['tests']['sui_cli'] = {
                'success': result.returncode == 0,
                'version': result.stdout.strip() if result.returncode == 0 else None,
                'error': result.stderr.strip() if result.returncode != 0 else None
            }
        except Exception as e:
            diagnostics['tests']['sui_cli'] = {
                'success': False,
                'error': str(e)
            }
        
        # Test 2: Environment variables
        env_vars = {
            'PACKAGE_ID': self.package_id,
            'LEDGER_ID': self.ledger_id,
            'PUBLISHER_CAP_ID': self.publisher_cap_id,
            'CLOCK_ID': self.clock_id
        }
        missing_vars = [k for k, v in env_vars.items() if not v]
        diagnostics['tests']['environment_variables'] = {
            'success': len(missing_vars) == 0,
            'variables': env_vars,
            'missing': missing_vars,
            'error': f"Missing variables: {', '.join(missing_vars)}" if missing_vars else None
        }
        
        # Test 3: SUI client connection
        try:
            result = subprocess.run(
                ["sui", "client", "active-address"],
                capture_output=True,
                text=True,
                timeout=10
            )
            diagnostics['tests']['client_connection'] = {
                'success': result.returncode == 0,
                'active_address': result.stdout.strip() if result.returncode == 0 else None,
                'error': result.stderr.strip() if result.returncode != 0 else None
            }
        except Exception as e:
            diagnostics['tests']['client_connection'] = {
                'success': False,
                'error': str(e)
            }
        
        # Test 4: Network connectivity (if we have all required info)
        if all([self.package_id, self.ledger_id, self.publisher_cap_id]):
            try:
                # Try a dry-run call to test network connectivity
                test_cmd = [
                    "sui", "client", "call",
                    "--package", self.package_id,
                    "--module", "validator_scanner",
                    "--function", "publish_scan_summary",
                    "--args",
                    self.ledger_id,
                    self.publisher_cap_id,
                    "test_host",
                    "1000000",
                    "0x1234567890abcdef",
                    "100",
                    "test_pointer",
                    self.clock_id,
                    "--gas-budget", "10000000",
                    "--dry-run"
                ]
                
                result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=30)
                diagnostics['tests']['network_call'] = {
                    'success': result.returncode == 0,
                    'dry_run_output': result.stdout if result.returncode == 0 else None,
                    'error': result.stderr.strip() if result.returncode != 0 else None
                }
            except Exception as e:
                diagnostics['tests']['network_call'] = {
                    'success': False,
                    'error': str(e)
                }
        else:
            diagnostics['tests']['network_call'] = {
                'success': False,
                'error': 'Skipped due to missing environment variables'
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
