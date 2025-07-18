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
  # Publish scan to ledger
  pgdn-publish ledger --scan-data '{"host_uid": "validator_123", "trust_score": 85}'
  
  # Publish scan report
  pgdn-publish report --scan-data '{"scan_id": 123, "trust_score": 85}'
  
  # Publish report to specific destinations
  pgdn-publish report --scan-data '{"scan_id": 123}' --destinations walrus local_file
  
  # Check ledger status
  pgdn-publish status
  
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
    
    # Retrieve command
    retrieve_parser = subparsers.add_parser('retrieve', help='Retrieve report from Walrus')
    retrieve_parser.add_argument(
        '--walrus-hash',
        required=True,
        help='Walrus hash of the report to retrieve'
    )
    
    # Global configuration options
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
        
        # Publish to ledger
        result = publish_to_ledger(
            scan_data, 
            config
        )
        
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
        args = parse_arguments()
        
        if not args.command:
            print(json.dumps({
                "success": False,
                "error": "No command specified. Use --help for usage information."
            }))
            sys.exit(1)
        
        # Load configuration
        try:
            config = PublisherConfig.from_env()
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