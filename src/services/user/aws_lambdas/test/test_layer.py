#!/usr/bin/env python3
"""
Test that all required packages are available in the user service layer
"""

import sys
import traceback

def test_imports():
    """Test that all required packages can be imported"""
    tests = [
        ("boto3", "import boto3"),
        ("jwt", "import jwt"),
        ("json", "import json"),
        ("datetime", "import datetime"),
        ("typing", "from typing import Any, Dict, List, Optional"),
        ("base64", "import base64"),
        ("uuid", "import uuid"),
    ]
    
    passed = 0
    failed = 0
    
    print("Testing package imports...")
    for test_name, test_code in tests:
        try:
            exec(test_code)
            print(f"✓ {test_name}")
            passed += 1
        except Exception as e:
            print(f"✗ {test_name}: {e}")
            traceback.print_exc()
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0

def test_core_modules():
    """Test that core modules can be imported"""
    core_modules = [
        "core.auth_utils",
        "core.profile_utils", 
        "core.rest_utils",
        "core.settings"
    ]
    
    passed = 0
    failed = 0
    
    print("\nTesting core module imports...")
    for module in core_modules:
        try:
            __import__(module)
            print(f"✓ {module}")
            passed += 1
        except Exception as e:
            print(f"✗ {module}: {e}")
            traceback.print_exc()
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0

def main():
    """Run all tests"""
    print("User Service Layer Tests")
    print("=" * 40)
    
    all_passed = True
    
    # Test imports
    all_passed &= test_imports()
    
    # Test core modules
    all_passed &= test_core_modules()
    
    print("\n" + "=" * 40)
    if all_passed:
        print("All tests PASSED")
        return 0
    else:
        print("Some tests FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())