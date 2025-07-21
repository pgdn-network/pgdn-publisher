"""
Blockchain ledger publishing functionality.
"""

from typing import Dict, Any, Optional

from .config import PublisherConfig
from .zksync_ledger import ZkSyncLedgerPublisher, ZkSyncLedgerError
from .sui_ledger import SuiLedgerPublisher, SuiLedgerError


class LedgerError(Exception):
    """Custom exception for ledger publishing errors."""
    pass


class LedgerPublisher:
    """Multi-network publisher for blockchain ledger operations."""
    
    def __init__(self, config: PublisherConfig):
        """Initialize ledger publisher based on network configuration."""
        self.config = config
        
        # Create network-specific publisher
        if config.network == 'sui':
            self._publisher = SuiLedgerPublisher(config)
        elif config.network == 'zksync':
            self._publisher = ZkSyncLedgerPublisher(config)
        else:
            raise LedgerError(f"Unsupported network: {config.network}")
    
    def publish(self, scan_result: Dict[str, Any], wait_for_confirmation: bool = True) -> Dict[str, Any]:
        """Publish scan result to blockchain ledger."""
        try:
            return self._publisher.publish(scan_result, wait_for_confirmation)
        except (ZkSyncLedgerError, SuiLedgerError) as e:
            raise LedgerError(str(e))
    
    def get_status(self) -> Dict[str, Any]:
        """Get ledger connection status."""
        try:
            return self._publisher.get_status()
        except (ZkSyncLedgerError, SuiLedgerError) as e:
            return {
                'connected': False,
                'network': self.config.network,
                'error': str(e)
            }


def create_ledger_publisher(network_name: str, config: Optional[PublisherConfig] = None) -> LedgerPublisher:
    """
    Factory function to create a ledger publisher for a specific network.
    
    Args:
        network_name: Network name ('zksync', 'sui', etc.)
        config: Optional configuration override
    
    Returns:
        LedgerPublisher instance configured for the specified network
    """
    if config is None:
        config = PublisherConfig.from_env(network=network_name)
    else:
        # Update the network in the provided config
        config.network = network_name
    
    return LedgerPublisher(config)


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