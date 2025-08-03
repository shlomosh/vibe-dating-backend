#!/usr/bin/env python3
"""
Test script for Media Service
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

from core.test_utils import ServiceTester


def main(action=None):
    """Run media service tests"""
    print("🧪 Running Media Service Tests...")

    tester = ServiceTester("media", {})

    # Run all tests
    success = tester.test()

    if success:
        print("\n✅ Media Service tests completed successfully!")
    else:
        print("\n❌ Some Media Service tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
