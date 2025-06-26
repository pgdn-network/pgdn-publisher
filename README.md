# PGDN Publisher

A pure Python library for publishing DePIN scan results to blockchain ledgers and reports.

## Installation

```bash
cd lib
pip install -e .
```

## Usage

### Library
```python
from pgdn_publisher import publish_to_ledger, publish_report

# Publish to ledger
result = publish_to_ledger(scan_data)

# Publish report
results = publish_report(scan_data)
```

### CLI
```bash
# Use the JSON CLI
python lib/cli.py ledger --scan-data '{"host_uid": "test", "trust_score": 85}'
```

## Configuration

Set environment variables:
- `CONTRACT_ADDRESS` - Smart contract address
- `PRIVATE_KEY` - Private key for publishing
- `WALRUS_API_KEY` - Walrus storage API key (optional)

## Structure

- `lib/pgdn_publisher/` - Core library
- `lib/cli.py` - JSON CLI interface
- `lib/contracts/` - Smart contract ABIs
- `requirements.txt` - Basic dependencies