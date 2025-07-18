# PGDN Publish

A pure Python library for publishing DePIN (Decentralized Physical Infrastructure Network) scan results to blockchain ledgers and report storage systems.

## Features

- **Multi-Network Blockchain Publishing**: Support for multiple blockchain networks (ZKSync Era, SUI)
- **Report Publishing**: Generate and publish detailed security reports to Walrus storage and local files
- **Pure Library Design**: No database dependencies, no agent architecture
- **JSON CLI**: Simple command-line interface that returns only JSON output
- **Configurable**: Environment variable and configuration file support
- **Network-Agnostic**: Easily switch between different blockchain networks

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
from pgdn_publish import publish_to_ledger, publish_report, PublisherConfig, create_ledger_publisher

# Configure for ZKSync (default)
config = PublisherConfig.from_env()

# Configure for specific network
config = PublisherConfig.from_env(network="sui")

# Publish to blockchain ledger (ZKSync by default)
scan_data = {
    "host_uid": "validator_123",
    "trust_score": 85,
    "vulnerabilities": [],
    "open_ports": [22, 80, 443]
}

ledger_result = publish_to_ledger(scan_data, config)
print(f"Transaction hash: {ledger_result['transaction_hash']}")

# Publish to specific network
ledger_result = publish_to_ledger(scan_data, config, network="sui")

# Use network-specific publisher directly
publisher = create_ledger_publisher("zksync", config)
result = publisher.publish_scan(
    host_uid="validator_123",
    trust_score=85,
    data_hash="abc123..."
)

# Publish report
report_results = publish_report(scan_data, config=config)
for dest, result in report_results.items():
    if result.success:
        print(f"Published to {dest}: {result.identifier}")
```

### CLI Usage

```bash
# Publish to blockchain ledger (default ZKSync)
pgdn-publish ledger --scan-data '{"host_uid": "validator_123", "trust_score": 85}'

# Publish to SUI network
pgdn-publish --network sui ledger --scan-data '{"host_uid": "validator_123", "trust_score": 85}'

# Publish report to Walrus and local file
pgdn-publish report --scan-data '{"scan_id": 123, "trust_score": 85}'

# Check connection status for different networks
pgdn-publish --network zksync status
pgdn-publish --network sui status

# Run comprehensive diagnostic tests
pgdn-publish --network zksync diagnose
pgdn-publish --network sui diagnose

# Retrieve report from Walrus
pgdn-publish retrieve --walrus-hash "abc123def456"
```

## Configuration

The library automatically loads configuration from `.env` files. Create a `.env` file in your project root:

```bash
# Network selection (optional, default: zksync)
NETWORK="zksync"  # Options: zksync, sui

# ZKSync configuration (required for ZKSync)
CONTRACT_ADDRESS="0x1234567890abcdef..."
PRIVATE_KEY="0xabcdef1234567890..."
ZKSYNC_RPC_URL="https://sepolia.era.zksync.dev"

# SUI configuration (required for SUI)
SUI_RPC_URL="https://fullnode.mainnet.sui.io"

# Walrus storage (optional)  
WALRUS_API_KEY="your-walrus-api-key"
WALRUS_API_URL="https://publisher-devnet.walrus.space"

# Report output (optional)
REPORTS_OUTPUT_DIR="./reports"

# Gas settings (optional, ZKSync only)
GAS_LIMIT="10000000"
GAS_PRICE_GWEI="0.25"
```

## Library Classes

### PublisherConfig

Configuration management:

```python
from pgdn_publish import PublisherConfig

# From environment variables (default ZKSync)
config = PublisherConfig.from_env()

# From environment variables for specific network
config = PublisherConfig.from_env(network="sui")

# Manual configuration
config = PublisherConfig(
    network="zksync",
    contract_address="0x...",
    private_key="0x...",
    walrus_api_key="your-key"
)

# Validate configuration
config.validate()
```

### Network Factory

Create network-specific publishers:

```python
from pgdn_publish import create_ledger_publisher, get_supported_networks

# Get supported networks
networks = get_supported_networks()  # ['zksync', 'sui']

# Create ZKSync publisher
zk_publisher = create_ledger_publisher("zksync", config)

# Create SUI publisher (when implemented)
sui_publisher = create_ledger_publisher("sui", config)

# Publish scan
result = zk_publisher.publish_scan(
    host_uid="validator_123",
    trust_score=85,
    data_hash="abc123..."
)
```

### LedgerPublisher

Direct ledger publishing (backward compatibility):

```python
from pgdn_publish import LedgerPublisher

# ZKSync publisher (default)
publisher = LedgerPublisher(config)

# Publish scan
result = publisher.publish(scan_data, wait_for_confirmation=True)

# Check status
status = publisher.get_status()
```

### Network-Specific Publishers

Use network-specific implementations:

```python
from pgdn_publish import ZKSyncLedgerPublisher, SuiLedgerPublisher

# ZKSync publisher
zk_publisher = ZKSyncLedgerPublisher(config)
zk_result = zk_publisher.publish_scan("validator_123", 85, "hash123")

# SUI publisher (when implemented)
sui_publisher = SuiLedgerPublisher(config)
# sui_result = sui_publisher.publish_scan("validator_123", 85, "hash123")
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