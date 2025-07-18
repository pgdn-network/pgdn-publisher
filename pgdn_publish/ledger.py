"""
Blockchain ledger publishing functionality.

This module provides backward compatibility by importing and wrapping
the new network-specific implementations.
"""

from typing import Dict, Any, Optional
from .config import PublisherConfig
from .network_factory import create_ledger_publisher
from .networks.zksync import ZKSyncLedgerPublisher, LedgerError

# For backward compatibility, expose the ZKSync implementation as LedgerPublisher
LedgerPublisher = ZKSyncLedgerPublisher


def publish_to_ledger(
    scan_result: Dict[str, Any], 
    config: Optional[PublisherConfig] = None,
    network: str = "zksync"
) -> Dict[str, Any]:
    """
    Convenience function to publish a single scan result to the ledger.
    
    Args:
        scan_result: Scan result data to publish
        config: Publisher configuration (defaults to environment config)
        network: Network to publish to (default: zksync)
    
    Returns:
        Publication result dictionary
    """
    if config is None:
        config = PublisherConfig.from_env(network=network)
    
    publisher = create_ledger_publisher(network, config)
    
    # Extract required fields with fallbacks
    host_uid = scan_result.get('host_uid') or scan_result.get('validator_id', 'unknown_host')
    trust_score = int(scan_result.get('trust_score', 0))
    
    # Generate data hash from scan data
    import hashlib
    import json
    data_hash = hashlib.sha256(json.dumps(scan_result, sort_keys=True).encode()).hexdigest()
    
    return publisher.publish_scan(
        host_uid=host_uid,
        trust_score=trust_score,
        data_hash=data_hash,
        timestamp=scan_result.get('scan_time')
    )


def diagnose_ledger_connection(
    config: Optional[PublisherConfig] = None,
    network: str = "zksync"
) -> Dict[str, Any]:
    """
    Diagnose ledger connection issues without performing authorization checks.
    
    Args:
        config: Publisher configuration (defaults to environment config)
        network: Network to diagnose (default: zksync)
    
    Returns:
        Diagnostic information dictionary
    """
    if config is None:
        config = PublisherConfig.from_env(network=network)
    
    try:
        # Create publisher without authorization check for diagnostic purposes
        publisher = create_ledger_publisher(network, config, skip_auth_check=True)
        return publisher.diagnose_connection()
    except Exception as e:
        return {
            'success': False,
            'error': f"Failed to create diagnostic connection: {e}",
            'network': network,
            'config': {
                'rpc_url': config.get_network_rpc_url(),
                'contract_address': getattr(config, 'contract_address', None),
                'account_address': 'unknown'
            }
        }