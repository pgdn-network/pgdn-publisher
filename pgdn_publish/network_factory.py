"""
Network factory for creating appropriate ledger publishers.
"""

from typing import Optional
from .config import PublisherConfig
from .networks.base import BaseLedgerPublisher
from .networks.zksync import ZKSyncLedgerPublisher
from .networks.sui import SuiLedgerPublisher


class UnsupportedNetworkError(Exception):
    """Exception raised when an unsupported network is specified."""
    pass


def create_ledger_publisher(
    network: str,
    config: Optional[PublisherConfig] = None,
    skip_auth_check: bool = False
) -> BaseLedgerPublisher:
    """
    Create a ledger publisher for the specified network.
    
    Args:
        network: Network name (zksync, sui)
        config: Publisher configuration (defaults to environment config)
        skip_auth_check: Whether to skip authorization checks
        
    Returns:
        Network-specific ledger publisher instance
        
    Raises:
        UnsupportedNetworkError: If the network is not supported
    """
    if config is None:
        config = PublisherConfig.from_env(network=network)
    
    network = network.lower()
    
    if network == "zksync":
        return ZKSyncLedgerPublisher(config, skip_auth_check)
    elif network == "sui":
        return SuiLedgerPublisher(config, skip_auth_check)
    else:
        raise UnsupportedNetworkError(f"Unsupported network: {network}")


def get_supported_networks() -> list[str]:
    """
    Get list of supported networks.
    
    Returns:
        List of supported network names
    """
    return ["zksync", "sui"]
