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

Set environment variables:
- `CONTRACT_ADDRESS` - Smart contract address
- `PRIVATE_KEY` - Private key for publishing
- `WALRUS_API_KEY` - Walrus storage API key (optional)

## Structure

- `pgdn-publish/` - Main package directory
- `pgdn-publish/pgdn_publish/` - Core library
- `pgdn-publish/pgdn_publish/cli.py` - JSON CLI interface 
- `pgdn-publish/contracts/` - Smart contract ABIs
- `pgdn-publish/setup.py` - Package installation configuration