# PGDN Publish

A pure Python library for publ### CLI Usage

````bash
#### CLI Usage

```bash
# Publish to blockchain ledger
pgdn-publish ledger --scan-data '{"host_uid": "validator_123", "trust_score": 85}'

# Publish report to Walrus and local file
pgdn-publish report --scan-data '{"scan_id": 123, "trust_score": 85}'

# Check connection status
pgdn-publish status

# Retrieve report from Walrus
pgdn-publish retrieve --walrus-hash "abc123def456"
```

## Configurationchain ledger
pgdn-publish ledger --scan-data '{"host_uid": "validator_123", "trust_score": 85}'

# Publish report to Walrus and local file
pgdn-publish report --scan-data '{"scan_id": 123, "trust_score": 85}'

# Check connection status
pgdn-publish status

# Retrieve report from Walrus
pgdn-publish retrieve --walrus-hash "abc123def456"
```ish to blockchain ledger
pgdn-publish ledger --scan-data '{"host_uid": "validator_123", "trust_score": 85}'

# Publish report to Walrus and local file
pgdn-publish report --scan-data '{"scan_id": 123, "trust_score": 85}'

# Check connection status
pgdn-publish status

# Retrieve report from Walrus
pgdn-publish retrieve --walrus-hash "abc123def456"
```ecentralized Physical Infrastructure Network) scan results to blockchain ledgers and report storage systems.

## Features

- **Blockchain Ledger Publishing**: Publish scan summaries to zkSync Era blockchain
- **Report Publishing**: Generate and publish detailed security reports to Walrus storage and local files
- **Pure Library Design**: No database dependencies, no agent architecture
- **JSON CLI**: Simple command-line interface that returns only JSON output
- **Configurable**: Environment variable and configuration file support

## Installation

```bash
pip install pgdn-publish
```

## Quick Start

### Library Usage

```python
from pgdn_publish import publish_to_ledger, publish_report, PublisherConfig

# Configure
config = PublisherConfig.from_env()

# Publish to blockchain ledger
scan_data = {
    "host_uid": "validator_123",
    "trust_score": 85,
    "vulnerabilities": [],
    "open_ports": [22, 80, 443]
}

ledger_result = publish_to_ledger(scan_data, config)
print(f"Transaction hash: {ledger_result['transaction_hash']}")

# Publish report
report_results = publish_report(scan_data, config=config)
for dest, result in report_results.items():
    if result.success:
        print(f"Published to {dest}: {result.identifier}")
```

### CLI Usage

```bash
# Publish to blockchain ledger
pgdn-publisher ledger --scan-data '{"host_uid": "validator_123", "trust_score": 85}'

# Publish report to Walrus and local file
pgdn-publisher report --scan-data '{"scan_id": 123, "trust_score": 85}'

# Check connection status
pgdn-publisher status

# Retrieve report from Walrus
pgdn-publisher retrieve --walrus-hash "abc123def456"
```

## Configuration

Set these environment variables:

```bash
# Blockchain configuration (required)
export CONTRACT_ADDRESS="0x1234567890abcdef..."
export PRIVATE_KEY="0xabcdef1234567890..."
export ZKSYNC_RPC_URL="https://sepolia.era.zksync.dev"

# Walrus configuration (optional)
export WALRUS_API_KEY="your-walrus-api-key"
export WALRUS_API_URL="https://publisher-devnet.walrus.space"

# Optional configuration
export GAS_LIMIT="10000000"
export GAS_PRICE_GWEI="0.25"
export REPORTS_DIR="./reports"
```

## Library Classes

### PublisherConfig

Configuration management:

```python
from pgdn_publish import PublisherConfig

# From environment variables
config = PublisherConfig.from_env()

# Manual configuration
config = PublisherConfig(
    contract_address="0x...",
    private_key="0x...",
    walrus_api_key="your-key"
)

# Validate configuration
config.validate()
```

### LedgerPublisher

Direct ledger publishing:

```python
from pgdn_publish import LedgerPublisher

publisher = LedgerPublisher(config)

# Publish scan
result = publisher.publish(scan_data, wait_for_confirmation=True)

# Check status
status = publisher.get_status()
```

### ReportPublisher

Report publishing:

```python
from pgdn_publish import ReportPublisher

publisher = ReportPublisher(config)

# Publish to multiple destinations
results = publisher.publish(scan_data, destinations=['walrus', 'local_file'])

# Retrieve from Walrus
report = publisher.retrieve_from_walrus("walrus_hash")
```

## JSON CLI Reference

All CLI commands return JSON output for easy integration:

### Ledger Publishing

```bash
pgdn-publish ledger --scan-data '{"host_uid": "validator_123", "trust_score": 85}'
```

Returns:
```json
{
  "success": true,
  "command": "ledger",
  "result": {
    "success": true,
    "transaction_hash": "0xabc123...",
    "summary_hash": "0xdef456...",
    "confirmed": true,
    "block_number": 12345
  }
}
```

### Report Publishing

```bash
pgdn-publish report --scan-data '{"scan_id": 123}' --destinations walrus local_file
```

Returns:
```json
{
  "success": true,
  "command": "report",
  "results": {
    "walrus": {
      "success": true,
      "destination": "walrus",
      "identifier": "abc123def456",
      "error": null
    },
    "local_file": {
      "success": true,
      "destination": "local_file",
      "identifier": "./reports/scan_report_123_20241226_143022.json",
      "error": null
    }
  }
}
```

### Status Check

```bash
pgdn-publish status
```

Returns:
```json
{
  "success": true,
  "command": "status",
  "status": {
    "connected": true,
    "account_address": "0x...",
    "balance_eth": 0.1,
    "is_publisher": true,
    "contract_info": {
      "version": "3.0",
      "is_paused": false
    }
  }
}
```

## Error Handling

All operations return structured error information:

```json
{
  "success": false,
  "command": "ledger",
  "error": "Account not authorized to publish"
}
```

## License

MIT License