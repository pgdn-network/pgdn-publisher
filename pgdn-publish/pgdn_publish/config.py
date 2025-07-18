"""
Configuration management for PGDN Publisher.
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class PublisherConfig:
    """Configuration for PGDN Publisher."""
    
    # Blockchain configuration
    rpc_url: str = "https://sepolia.era.zksync.dev"
    contract_address: Optional[str] = None
    private_key: Optional[str] = None
    gas_limit: int = 10000000
    gas_price_gwei: float = 0.25
    
    # Walrus configuration
    walrus_api_url: str = "https://publisher-devnet.walrus.space"
    walrus_api_key: Optional[str] = None
    
    # Report configuration
    reports_dir: str = "reports"
    
    @classmethod
    def from_env(cls) -> 'PublisherConfig':
        """Create configuration from environment variables."""
        return cls(
            rpc_url=os.getenv('ZKSYNC_RPC_URL', cls.rpc_url),
            contract_address=os.getenv('CONTRACT_ADDRESS'),
            private_key=os.getenv('PRIVATE_KEY'),
            gas_limit=int(os.getenv('GAS_LIMIT', cls.gas_limit)),
            gas_price_gwei=float(os.getenv('GAS_PRICE_GWEI', cls.gas_price_gwei)),
            walrus_api_url=os.getenv('WALRUS_API_URL', cls.walrus_api_url),
            walrus_api_key=os.getenv('WALRUS_API_KEY'),
            reports_dir=os.getenv('REPORTS_DIR', cls.reports_dir)
        )
    
    def validate(self) -> None:
        """Validate configuration."""
        if not self.contract_address:
            raise ValueError("CONTRACT_ADDRESS is required")
        if not self.private_key:
            raise ValueError("PRIVATE_KEY is required")