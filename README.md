# PGDN Publisher

A pure Python library for publishing DePIN scan results to blockchain ledgers and reports.

## Installation

```bash
pip install -e .
```

## Usage

### Library
```python
from pgdn_publisher import create_ledger_publisher, publish_report
import os

# Create publisher for specific network
network_name = os.getenv('PGDN_NETWORK', 'zksync')
publisher = create_ledger_publisher(network_name, config=None)

# Publish to ledger (summary_hash required)
scan_data = {
    "host_uid": "validator_123",
    "trust_score": 85,
    "summary_hash": "0x1234567890abcdef..."  # REQUIRED
}
result = publisher.publish(scan_data)

# Publish report
results = publish_report(scan_data)
```

### CLI
```bash
# Publish to ledger (summary_hash required in JSON)
pgdn-publisher ledger --scan-data '{"host_uid": "validator_123", "trust_score": 85, "summary_hash": "0x1234567890abcdef..."}'

# Publish without waiting for confirmation
pgdn-publisher ledger --scan-data '{"host_uid": "validator_123", "trust_score": 85, "summary_hash": "0x1234567890abcdef..."}' --no-wait

# Publish report
pgdn-publisher report --scan-data '{"scan_id": 123, "trust_score": 85}'

# Check connection status
pgdn-publisher status
```

## Configuration

Set environment variables:
- `CONTRACT_ADDRESS` - Smart contract address (required)
- `PRIVATE_KEY` - Private key for publishing (required)
- `PGDN_NETWORK` - Network name ('zksync', 'sui', etc.)
- `ZKSYNC_RPC_URL` - zkSync RPC URL (optional)
- `SUI_RPC_URL` - Sui RPC URL (optional)
- `WALRUS_API_KEY` - Walrus storage API key (optional for reports)

## Important Notes

- **`summary_hash` is REQUIRED** in all ledger publishing operations
- The library will NOT generate summary hashes automatically
- Include the `summary_hash` field in your scan data JSON
- Network configuration is handled via `PGDN_NETWORK` environment variable or passed to `create_ledger_publisher()`

## Structure

- `pgdn_publisher/` - Core Python package
- `cli.py` - JSON CLI interface  
- `contracts/ledger/abi.json` - Smart contract ABI
- `requirements.txt` - Dependencies