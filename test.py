#!/usr/bin/env python3
import os
import sys
import time
import json
import subprocess

def load_env():
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

def main():
    if len(sys.argv) != 5:
        print("Usage: python publish.py <host_uid> <score> <report_pointer> <summary_hash>")
        sys.exit(1)
    
    load_env()
    
    host_uid, score, report_pointer, summary_hash_hex = sys.argv[1:5]
    
    # Parse summary hash
    if summary_hash_hex.startswith('0x'):
        summary_hash_hex = summary_hash_hex[2:]
    summary_hash = bytes.fromhex(summary_hash_hex)
    scan_time = int(time.time() * 1000)
    
    # Load from env
    PACKAGE_ID = os.getenv('DEPIN_PACKAGE_ID', '0x799a3a025c5c4e8bfd519b3af06b5f9938ee558cabd6d719074d9899204ba9a1')
    REGISTRY_ID = os.getenv('DEPIN_REGISTRY_ID', '0x4b5944372fab52322eb0c81e8badd89ae88258144bf1c39442629fce5a24fe8d')
    ADMIN_CAP_ID = os.getenv('DEPIN_ADMIN_CAP_ID', '0x6450631886eccff4c71390c6eefa0999b31aafaeea64ca4a3e28bed3ad8f7a2e')
    
    # Build command
    cmd = [
        "sui", "client", "call", "--json",
        "--package", PACKAGE_ID,
        "--module", "validator_scanner_registry", 
        "--function", "publish_scan_summary",
        "--args", REGISTRY_ID, ADMIN_CAP_ID, host_uid, str(scan_time),
        f"[{','.join(str(b) for b in summary_hash)}]", score, report_pointer, "0x6",
        "--gas-budget", "100000000"
    ]
    
    print(f"Publishing: {host_uid}, score: {score}, time: {scan_time}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        
        if result.returncode != 0:
            # Ignore version mismatch warnings
            if "version mismatch" not in result.stderr:
                print(f"Command failed: {result.stderr}")
                sys.exit(1)
        
        if not result.stdout.strip():
            print("No output from command")
            sys.exit(1)
            
        # Handle non-JSON output (plain text errors)
        if "aborted within function" in result.stdout and "code 4" in result.stdout:
            print(json.dumps({"success": False, "error": "duplicate_hash", "message": "Duplicate hash"}))
            sys.exit(1)
        elif "aborted within function" in result.stdout:
            print(json.dumps({"success": False, "error": "move_abort", "message": result.stdout}))
            sys.exit(1)
        elif "Error executing transaction" in result.stdout:
            print(json.dumps({"success": False, "error": "transaction_error", "message": result.stdout}))
            sys.exit(1)
        
        try:
            output = json.loads(result.stdout)
            # Check for failure in JSON
            if output.get("effects", {}).get("status", {}).get("status") == "failure":
                error = output["effects"]["status"]["error"]
                if "MoveAbort" in str(error) and ", 4)" in str(error):
                    print(json.dumps({"success": False, "error": "duplicate_hash", "message": "Duplicate hash"}))
                else:
                    print(json.dumps({"success": False, "error": "move_error", "message": str(error)}))
                sys.exit(1)
            print(json.dumps({"success": True, "digest": output.get('digest', 'unknown')}))
        except json.JSONDecodeError:
            # Assume success if no error patterns found
            if "Transaction executed successfully" in result.stdout or result.stdout.strip():
                print(json.dumps({"success": True, "message": "Transaction completed", "output": result.stdout}))
            else:
                print(json.dumps({"success": False, "error": "unknown_output", "message": result.stdout}))
                sys.exit(1)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
