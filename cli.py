#!/usr/bin/env python3
"""
PGDN Publisher CLI

A simplified CLI for publishing DePIN scan results to blockchain ledgers and reports.
Returns only JSON output.
"""

import json
import sys
import argparse
import os
from typing import Dict, Any

def load_env():
    """Load environment variables from .env file if it exists."""
    try:
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    except FileNotFoundError:
        pass  # .env file is optional

try:
    from pgdn_publisher import (
        publish_to_ledger, 
        publish_report, 
        LedgerPublisher, 
        ReportPublisher, 
        PublisherConfig
    )
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
  # Publish scan to zkSync ledger
  pgdn-publisher ledger --network zksync --scan-data '{"host_uid": "validator_123", "trust_score": 85, "summary_hash": "0x..."}'
  
  # Publish scan to SUI ledger
  pgdn-publisher ledger --network sui --scan-data '{"host_uid": "validator_123", "trust_score": 85, "summary_hash": "abc123"}'
  
  # Publish scan report
  pgdn-publisher report --scan-data '{"scan_id": 123, "trust_score": 85}'
  
  # Check SUI ledger status
  pgdn-publisher status --network sui
  
  # Retrieve report from Walrus
  pgdn-publisher retrieve --walrus-hash "abc123def456"
        """
    )
    
    # Global configuration options
    parser.add_argument(
        '--config-file',
        help='Path to configuration file (JSON format)'
    )
    parser.add_argument(
        '--network',
        choices=['zksync', 'sui'],
        help='Blockchain network to use (overrides PGDN_NETWORK env var)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Ledger publishing command
    ledger_parser = subparsers.add_parser('ledger', help='Publish scan to blockchain ledger')
    ledger_parser.add_argument(
        '--scan-data',
        required=True,
        help='Scan data as JSON string (must include summary_hash)'
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
    
    # Retrieve command
    retrieve_parser = subparsers.add_parser('retrieve', help='Retrieve report from Walrus')
    retrieve_parser.add_argument(
        '--walrus-hash',
        required=True,
        help='Walrus hash of the report to retrieve'
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
        
        # Validate that summary_hash is present
        if 'summary_hash' not in scan_data:
            return {
                "success": False,
                "command": "ledger",
                "error": "summary_hash is required in scan data"
            }
        
        # Set wait for confirmation based on flag
        wait_for_confirmation = not args.no_wait
        
        # Create publisher and publish
        publisher = LedgerPublisher(config)
        result = publisher.publish(scan_data, wait_for_confirmation=wait_for_confirmation)
        
        return {
            "success": True,
            "command": "ledger",
            "result": result
        }
        
    except Exception as e:
        return {
            "success": False,
            "command": "ledger",
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


def handle_status_command(config: PublisherConfig) -> Dict[str, Any]:
    """Handle status command."""
    try:
        publisher = LedgerPublisher(config)
        status = publisher.get_status()
        
        return {
            "success": True,
            "command": "status",
            "status": status
        }
        
    except Exception as e:
        return {
            "success": False,
            "command": "status",
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
        # Load .env file first
        load_env()
        
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
            result = handle_status_command(config)
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