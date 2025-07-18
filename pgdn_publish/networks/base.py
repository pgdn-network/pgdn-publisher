"""
Base ledger publisher interface.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..config import PublisherConfig


class BaseLedgerPublisher(ABC):
    """Abstract base class for network-specific ledger publishers."""
    
    def __init__(self, config: PublisherConfig, skip_auth_check: bool = False):
        """Initialize the ledger publisher."""
        self.config = config
        
    @abstractmethod
    def publish_scan(
        self, 
        host_uid: str, 
        trust_score: int, 
        data_hash: str, 
        timestamp: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Publish scan results to the blockchain ledger.
        
        Args:
            host_uid: Unique identifier for the scanned host
            trust_score: Calculated trust score (0-100)
            data_hash: Hash of the scan data
            timestamp: Unix timestamp of the scan (defaults to current time)
            
        Returns:
            Dictionary containing transaction details and success status
        """
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the ledger connection.
        
        Returns:
            Dictionary containing connection and account status
        """
        pass
    
    @abstractmethod
    def diagnose_connection(self) -> Dict[str, Any]:
        """
        Run comprehensive diagnostics on the ledger connection.
        
        Returns:
            Dictionary containing diagnostic results
        """
        pass
    
    @abstractmethod
    def get_network_name(self) -> str:
        """
        Get the name of the network this publisher works with.
        
        Returns:
            String name of the network (e.g., "zksync", "sui")
        """
        pass
