# PGDN Publish

A pure Python library for publishing DePIN scan results to blockchain ledgers and reports.

## Installation

```bash
cd pgdn-publish
pip install -e .
```

Or install from PyPI (once published):
```bash
pip install pgdn-publish
```

## Usage

### Library
```python
from pgdn_publish import publish_to_ledger, publish_report

# Publish to ledger
result = publish_to_ledger(scan_data)

# Publish report
results = publish_report(scan_data)
```

### CLI
```bash
# Use the JSON CLI
pgdn-publish ledger --scan-data '{"host_uid": "test", "trust_score": 85}'
```

## Configuration

Create a `.env` file in your project root or set environment variables:

```bash
# Blockchain configuration (required)
CONTRACT_ADDRESS="0x1234567890abcdef..."
PRIVATE_KEY="0xabcdef1234567890..."
ZKSYNC_RPC_URL="https://sepolia.era.zksync.dev"

# Walrus storage (optional)
WALRUS_API_KEY="your-walrus-api-key"
WALRUS_API_URL="https://publisher-devnet.walrus.space"

# Report output (optional)
REPORTS_OUTPUT_DIR="./reports"

# Gas settings (optional)
GAS_LIMIT="10000000"
GAS_PRICE_GWEI="0.25"
```

The library will automatically load from a `.env` file in the current directory or parent directories.

## Structure

- `pgdn-publish/` - Main package directory
- `pgdn-publish/pgdn_publish/` - Core library
- `pgdn-publish/pgdn_publish/cli.py` - JSON CLI interface 
- `pgdn-publish/contracts/` - Smart contract ABIs
- `pgdn-publish/setup.py` - Package installation configuration