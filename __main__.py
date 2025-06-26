"""
Entry point for the PGDN Publisher console script.
"""

import sys
import os

# Add the current directory to the Python path so we can import main
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main_entry():
    """Entry point for the console script."""
    from cli import main
    main()

if __name__ == "__main__":
    main_entry()