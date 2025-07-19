"""
Configuration management for PGDN Publisher.
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass

try:
    from dotenv import load_dotenv, find_dotenv
    _DOTENV_AVAILABLE = True
except ImportError:
    _DOTENV_AVAILABLE = False


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
    
    # SUI-specific configuration
    sui_rpc_url: str = "https://fullnode.mainnet.sui.io"
    
    # Walrus configuration
    walrus_api_url: str = "https://publisher-devnet.walrus.space"
    walrus_api_key: Optional[str] = None
    
    # Report configuration
    reports_dir: str = "reports"
    
    @classmethod
    def from_env(cls, env_file: Optional[str] = None, network: Optional[str] = None) -> 'PublisherConfig':
        """
        Create configuration from environment variables.
        
        Args:
            env_file: Path to .env file to load. If None, looks for .env in current directory and parent directories.
            network: Network to use (zksync, sui). If None, uses default or environment variable.
        """
        # Load .env file if available
        if _DOTENV_AVAILABLE:
            if env_file:
                load_dotenv(env_file)
            else:
                # Look for .env file in current directory and parent directories
                env_path = find_dotenv()
                if env_path:
                    load_dotenv(env_path)
        
        # Determine network
        if network is None:
            network = os.getenv('NETWORK', 'zksync')
        
        # Set RPC URL based on network
        if network.lower() == 'sui':
            default_rpc = os.getenv('SUI_RPC_URL', 'https://fullnode.mainnet.sui.io')
        else:
            default_rpc = os.getenv('ZKSYNC_RPC_URL', 'https://sepolia.era.zksync.dev')
        
        return cls(
            network=network.lower(),
            rpc_url=default_rpc,
            contract_address=os.getenv('CONTRACT_ADDRESS'),
            private_key=os.getenv('PRIVATE_KEY'),
            gas_limit=int(os.getenv('GAS_LIMIT', cls.gas_limit)),
            gas_price_gwei=float(os.getenv('GAS_PRICE_GWEI', cls.gas_price_gwei)),
            sui_rpc_url=os.getenv('SUI_RPC_URL', cls.sui_rpc_url),
            walrus_api_url=os.getenv('WALRUS_API_URL', cls.walrus_api_url),
            walrus_api_key=os.getenv('WALRUS_API_KEY'),
            reports_dir=os.getenv('REPORTS_OUTPUT_DIR', os.getenv('REPORTS_DIR', cls.reports_dir))
        )
    
    def validate(self) -> None:
        """Validate configuration."""
        # Only validate contract-specific fields for networks that need them
        if self.network == 'zksync':
            if not self.contract_address:
                raise ValueError("CONTRACT_ADDRESS is required for ZKSync network")
            if not self.private_key:
                raise ValueError("PRIVATE_KEY is required for ZKSync network")
        elif self.network == 'sui':
            # Check for SUI-specific environment variables
            package_id = os.getenv('PACKAGE_ID')
            ledger_id = os.getenv('LEDGER_ID')
            publisher_cap_id = os.getenv('PUBLISHER_CAP_ID')
            
            missing = []
            if not package_id:
                missing.append('PACKAGE_ID')
            if not ledger_id:
                missing.append('LEDGER_ID')
            if not publisher_cap_id:
                missing.append('PUBLISHER_CAP_ID')
            
            if missing:
                raise ValueError(f"SUI network requires these environment variables: {', '.join(missing)}")
        else:
            raise ValueError(f"Unsupported network: {self.network}")
    
    def get_network_rpc_url(self) -> str:
        """Get the appropriate RPC URL for the selected network."""
        if self.network == 'sui':
            return self.sui_rpc_url
        else:
            return self.rpc_url