"""
Configuration management for PGDN Publisher.
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class PublisherConfig:
    """Configuration for PGDN Publisher."""
    
    # Network configuration
    network: str = "zksync"
    
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
    def from_env(cls, network: Optional[str] = None) -> 'PublisherConfig':
        """Create configuration from environment variables."""
        # Use provided network or fall back to environment variable
        network_name = network or os.getenv('PGDN_NETWORK', 'zksync')
        
        # Set network-specific defaults
        if network_name == 'sui':
            default_rpc = "https://fullnode.mainnet.sui.io:443"
            default_gas_limit = 1000000
            default_gas_price = 1000.0  # MIST
        else:  # zksync default
            default_rpc = "https://sepolia.era.zksync.dev"
            default_gas_limit = 10000000
            default_gas_price = 0.25  # Gwei
        
        return cls(
            network=network_name,
            rpc_url=os.getenv('ZKSYNC_RPC_URL', default_rpc) if network_name == 'zksync' else os.getenv('SUI_RPC_URL', default_rpc),
            contract_address=os.getenv('CONTRACT_ADDRESS'),
            private_key=os.getenv('PRIVATE_KEY'),
            gas_limit=int(os.getenv('GAS_BUDGET', os.getenv('GAS_LIMIT', default_gas_limit))),
            gas_price_gwei=float(os.getenv('GAS_PRICE_GWEI', default_gas_price)),
            walrus_api_url=os.getenv('WALRUS_API_URL', cls.walrus_api_url),
            walrus_api_key=os.getenv('WALRUS_API_KEY'),
            reports_dir=os.getenv('REPORTS_DIR', cls.reports_dir)
        )
    
    def validate(self) -> None:
        """Validate configuration."""
        if self.network == 'sui':
            # For SUI, we use SUI CLI which doesn't need CONTRACT_ADDRESS or PRIVATE_KEY
            # The SUI CLI handles authentication and the contract addresses are in env vars
            pass
        else:
            # For other networks (zkSync), require CONTRACT_ADDRESS and PRIVATE_KEY
            if not self.contract_address:
                raise ValueError("CONTRACT_ADDRESS is required")
            if not self.private_key:
                raise ValueError("PRIVATE_KEY is required")