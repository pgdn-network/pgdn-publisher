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
    def from_env(cls, env_file: Optional[str] = None) -> 'PublisherConfig':
        """
        Create configuration from environment variables.
        
        Args:
            env_file: Path to .env file to load. If None, looks for .env in current directory and parent directories.
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
        
        return cls(
            rpc_url=os.getenv('ZKSYNC_RPC_URL', cls.rpc_url),
            contract_address=os.getenv('CONTRACT_ADDRESS'),
            private_key=os.getenv('PRIVATE_KEY'),
            gas_limit=int(os.getenv('GAS_LIMIT', cls.gas_limit)),
            gas_price_gwei=float(os.getenv('GAS_PRICE_GWEI', cls.gas_price_gwei)),
            walrus_api_url=os.getenv('WALRUS_API_URL', cls.walrus_api_url),
            walrus_api_key=os.getenv('WALRUS_API_KEY'),
            reports_dir=os.getenv('REPORTS_OUTPUT_DIR', os.getenv('REPORTS_DIR', cls.reports_dir))
        )
    
    def validate(self) -> None:
        """Validate configuration."""
        if not self.contract_address:
            raise ValueError("CONTRACT_ADDRESS is required")
        if not self.private_key:
            raise ValueError("PRIVATE_KEY is required")