#!/usr/bin/env python3
"""
PGDN Publisher CLI

A simplified CLI for publishing DePIN scan results to blockchain ledgers and reports.
Returns only JSON output.
"""

import json
import sys
import argparse
from typing import Dict, Any

try:
    from . import (
        publish_to_ledger, 
        publish_report, 
        diagnose_ledger_connection,
        LedgerPublisher, 
        ReportPublisher, 
        PublisherConfig
    )
    from .network_factory import create_ledger_publisher, get_supported_networks
except ImportError:
    print(json.dumps({
        "success": False,
        "error": "pgdn_publisher library not found. Please install the library first."
    }))
    sys.exit(1)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="PGDN Publisher - Blockchain ledger and report publishing CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Publish scan to ledger (default ZKSync)
  pgdn-publish ledger --scan-data '{"host_uid": "validator_123", "trust_score": 85}'
  
  # Publish scan to SUI ledger
  pgdn-publish ledger --scan-data '{"host_uid": "validator_123", "trust_score": 85}' --network sui
  
  # Publish scan report
  pgdn-publish report --scan-data '{"scan_id": 123, "trust_score": 85}'
  
  # Publish report to specific destinations
  pgdn-publish report --scan-data '{"scan_id": 123}' --destinations walrus local_file
  
  # Check ledger status for different networks
  pgdn-publish status --network zksync
  pgdn-publish status --network sui
  
  # Run diagnostic tests
  pgdn-publish diagnose --network zksync
  pgdn-publish diagnose
  
  # Retrieve report from Walrus
  pgdn-publish retrieve --walrus-hash "abc123def456"
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Ledger publishing command
    ledger_parser = subparsers.add_parser('ledger', help='Publish scan to blockchain ledger')
    ledger_parser.add_argument(
        '--scan-data',
        required=True,
        help='Scan data as JSON string'
    )
    ledger_parser.add_argument(
        '--no-wait',
        action='store_true',
        help='Do not wait for transaction confirmation'
    )
    
    # Report publishing command
    report_parser = subparsers.add_parser('report', help='Publish scan report')
    report_parser.add_argument(
        '--scan-data',
        required=True,
        help='Scan data as JSON string'
    )
    report_parser.add_argument(
        '--destinations',
        nargs='+',
        choices=['walrus', 'local_file'],
        default=['walrus', 'local_file'],
        help='Publishing destinations (default: walrus local_file)'
    )
    
    # Status command
    subparsers.add_parser('status', help='Check ledger connection status')
    
    # Diagnose command
    subparsers.add_parser('diagnose', help='Run comprehensive diagnostic tests for ledger connection')
    
    # Retrieve command
    retrieve_parser = subparsers.add_parser('retrieve', help='Retrieve report from Walrus')
    retrieve_parser.add_argument(
        '--walrus-hash',
        required=True,
        help='Walrus hash of the report to retrieve'
    )
    
    # Global configuration options
    parser.add_argument(
        '--network',
        choices=get_supported_networks(),
        default='zksync',
        help='Blockchain network to use (default: zksync)'
    )
    parser.add_argument(
        '--config-file',
        help='Path to configuration file (JSON format)'
    )
    
    return parser.parse_args()


def load_scan_data(scan_data_str: str) -> Dict[str, Any]:
    """Load and validate scan data from JSON string."""
    try:
        return json.loads(scan_data_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in scan data: {e}")


def handle_ledger_command(args, config: PublisherConfig) -> Dict[str, Any]:
    """Handle ledger publishing command."""
    try:
        scan_data = load_scan_data(args.scan_data)
        
        # Create network-specific ledger publisher
        publisher = create_ledger_publisher(args.network, config)
        
        # Extract required fields with fallbacks
        host_uid = scan_data.get('host_uid') or scan_data.get('validator_id', 'unknown_host')
        trust_score = int(scan_data.get('trust_score', 0))
        
        # Generate data hash from scan data
        import hashlib
        data_hash = hashlib.sha256(json.dumps(scan_data, sort_keys=True).encode()).hexdigest()
        
        # Publish to ledger
        result = publisher.publish_scan(
            host_uid=host_uid,
            trust_score=trust_score,
            data_hash=data_hash,
            timestamp=scan_data.get('scan_time')
        )
        
        return {
            "success": True,
            "command": "ledger",
            "network": args.network,
            "result": result
        }
        
    except Exception as e:
        return {
            "success": False,
            "command": "ledger",
            "network": args.network,
            "error": str(e)
        }


def handle_report_command(args, config: PublisherConfig) -> Dict[str, Any]:
    """Handle report publishing command."""
    try:
        scan_data = load_scan_data(args.scan_data)
        
        # Publish report
        results = publish_report(
            scan_data,
            destinations=args.destinations,
            config=config
        )
        
        # Convert PublishResult objects to dicts for JSON serialization
        serializable_results = {}
        for dest, result in results.items():
            serializable_results[dest] = {
                "success": result.success,
                "destination": result.destination,
                "identifier": result.identifier,
                "error": result.error
            }
        
        # Determine overall success
        overall_success = any(r.success for r in results.values())
        
        return {
            "success": overall_success,
            "command": "report",
            "results": serializable_results,
            "destinations": args.destinations
        }
        
    except Exception as e:
        return {
            "success": False,
            "command": "report",
            "error": str(e)
        }


def handle_status_command(args, config: PublisherConfig) -> Dict[str, Any]:
    """Handle status command."""
    try:
        publisher = create_ledger_publisher(args.network, config)
        status = publisher.get_status()
        
        return {
            "success": True,
            "command": "status",
            "network": args.network,
            "status": status
        }
        
    except Exception as e:
        return {
            "success": False,
            "command": "status",
            "network": args.network,
            "error": str(e)
        }


def handle_diagnose_command(args, config: PublisherConfig) -> Dict[str, Any]:
    """Handle diagnose command."""
    try:
        publisher = create_ledger_publisher(args.network, config, skip_auth_check=True)
        diagnostics = publisher.diagnose_connection()
        
        return {
            "success": True,
            "command": "diagnose",
            "network": args.network,
            "diagnostics": diagnostics
        }
        
    except Exception as e:
        return {
            "success": False,
            "command": "diagnose",
            "network": args.network,
            "error": str(e)
        }


def handle_retrieve_command(args, config: PublisherConfig) -> Dict[str, Any]:
    """Handle retrieve command."""
    try:
        publisher = ReportPublisher(config)
        report = publisher.retrieve_from_walrus(args.walrus_hash)
        
        if report:
            return {
                "success": True,
                "command": "retrieve",
                "walrus_hash": args.walrus_hash,
                "report": report
            }
        else:
            return {
                "success": False,
                "command": "retrieve",
                "error": "Report not found or could not be retrieved"
            }
        
    except Exception as e:
        return {
            "success": False,
            "command": "retrieve",
            "error": str(e)
        }


def main():
    """Main CLI entry point."""
    try:
        args = parse_arguments()
        
        if not args.command:
            print(json.dumps({
                "success": False,
                "error": "No command specified. Use --help for usage information."
            }))
            sys.exit(1)
        
        # Load configuration
        try:
            config = PublisherConfig.from_env(network=args.network)
        except Exception as e:
            print(json.dumps({
                "success": False,
                "error": f"Configuration error: {e}"
            }))
            sys.exit(1)
        
        # Route to command handlers
        if args.command == 'ledger':
            result = handle_ledger_command(args, config)
        elif args.command == 'report':
            result = handle_report_command(args, config)
        elif args.command == 'status':
            result = handle_status_command(args, config)
        elif args.command == 'diagnose':
            result = handle_diagnose_command(args, config)
        elif args.command == 'retrieve':
            result = handle_retrieve_command(args, config)
        else:
            result = {
                "success": False,
                "error": f"Unknown command: {args.command}"
            }
        
        # Output result as JSON
        print(json.dumps(result, indent=2))
        
        # Exit with appropriate code
        if not result.get('success', False):
            sys.exit(1)
        
    except KeyboardInterrupt:
        print(json.dumps({
            "success": False,
            "error": "Operation cancelled by user"
        }))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }))
        sys.exit(1)


if __name__ == "__main__":
    main()