# PGDN Publish

A pure Python library for publishing DePIN (Decentralized Physical Infrastructure Network) scan results to blockchain ledgers and report storage systems.

## Features

- **Blockchain Ledger Publishing**: Publish scan summaries to zkSync Era blockchain
- **Report Publishing**: Generate and publish detailed security reports to Walrus storage and local files
- **Pure Library Design**: No database dependencies, no agent architecture
- **JSON CLI**: Simple command-line interface that returns only JSON output
- **Configurable**: Environment variable and configuration file support

## Installation

Install directly from GitHub:
```bash
pip install git+https://github.com/pgdn-network/pgdn-publisher.git
```

Or for development:
```bash
git clone https://github.com/pgdn-network/pgdn-publisher.git
cd pgdn-publisher
pip install -e .
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
pgdn-publish ledger --scan-data '{"host_uid": "validator_123", "trust_score": 85}'

# Publish report to Walrus and local file
pgdn-publish report --scan-data '{"scan_id": 123, "trust_score": 85}'

# Check connection status
pgdn-publish status

# Retrieve report from Walrus
pgdn-publish retrieve --walrus-hash "abc123def456"
```

## Configuration

The library automatically loads configuration from `.env` files. Create a `.env` file in your project root:

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

## License

MIT License