#!/usr/bin/env python
"""Simple startup script for American Law Search."""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

FIFTY_EQUAL_SIGNS = "=" * 50

try:
    import uvicorn
    import pytest
except ImportError as e:
    print(f"Error importing required modules: {e}")
    sys.exit(1)

if __name__ == "__main__":
    have_args = len(sys.argv) > 1
    port = int(sys.argv[1]) if have_args else 9000
    run_pytest = True if have_args and sys.argv[2] == "test" else False

    print(FIFTY_EQUAL_SIGNS)
    print("  American Law Search")
    print(f"  Starting on port {port}")
    print(FIFTY_EQUAL_SIGNS)
    
    if run_pytest:
        print("Running tests...")
        try:
            result = pytest.main([str(project_root / "tests"), "-v"])
            if result != 0:
                print("Tests failed. Exiting.")
                sys.exit(1)
        except Exception as e:
            print(f"Error while running tests: {e}")
            sys.exit(1)

    uvicorn.run(
        "app.app:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
