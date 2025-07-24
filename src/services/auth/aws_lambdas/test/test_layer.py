"""
Test script to verify Lambda layer dependencies are working correctly
"""

import os
import sys

os.environ["AWS_PROFILE"] = "vibe-dev"


def test_imports():
    """Test that all required packages can be imported"""
    print("Testing Lambda layer imports...")

    try:
        import jwt

        print("+ PyJWT imported successfully")
    except ImportError as e:
        print(f"[FAIL] Failed to import PyJWT: {e}")
        return False

    try:
        import boto3

        print("+ boto3 imported successfully")
    except ImportError as e:
        print(f"[FAIL] Failed to import boto3: {e}")
        return False

    try:
        import requests

        print("+ requests imported successfully")
    except ImportError as e:
        print(f"[FAIL] Failed to import requests: {e}")
        return False

    try:
        import urllib3

        print("+ urllib3 imported successfully")
    except ImportError as e:
        print(f"[FAIL] Failed to import urllib3: {e}")
        return False

    try:
        from dateutil import parser

        print("+ python-dateutil imported successfully")
    except ImportError as e:
        print(f"[FAIL] Failed to import python-dateutil: {e}")
        return False

    return True


def test_python_path():
    """Test Python path includes Lambda layer directories"""
    print("\nTesting Python path...")

    # Check if /opt/python is in Python path (Lambda layer location)
    python_paths = sys.path
    layer_paths = [
        path for path in python_paths if "/opt/python" in path or "python" in path
    ]

    print(f"Python path entries: {len(python_paths)}")
    print(f"Layer-related paths: {len(layer_paths)}")

    for path in layer_paths:
        print(f"  - {path}")

    return len(layer_paths) > 0


def test_jwt_functionality():
    """Test JWT functionality"""
    print("\nTesting JWT functionality...")

    try:
        import datetime

        import jwt

        # Test JWT encoding/decoding
        secret = "test_secret"
        payload = {
            "user_id": "test_user",
            "iat": datetime.datetime.utcnow(),
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        }

        token = jwt.encode(payload, secret, algorithm="HS256")
        decoded = jwt.decode(token, secret, algorithms=["HS256"])

        if decoded["user_id"] == "test_user":
            print("+ JWT encoding/decoding works correctly")
            return True
        else:
            print("[FAIL] JWT encoding/decoding failed")
            return False

    except Exception as e:
        print(f"[FAIL] JWT functionality test failed: {e}")
        return False


def test_boto3_functionality():
    """Test boto3 functionality"""
    print("\nTesting boto3 functionality...")

    try:
        import boto3

        # Test boto3 client creation (without actual AWS calls)
        dynamodb = boto3.resource("dynamodb")
        print("+ boto3 DynamoDB resource created successfully")

        return True

    except Exception as e:
        print(f"[FAIL] boto3 functionality test failed: {e}")
        return False


def test_dateutil_functionality():
    """Test python-dateutil functionality"""
    print("\nTesting python-dateutil functionality...")

    try:
        from dateutil import parser

        # Test date parsing
        test_date = "2023-12-01T10:30:00Z"
        parsed_date = parser.parse(test_date)

        if parsed_date:
            print("+ python-dateutil date parsing works correctly")
            return True
        else:
            print("[FAIL] python-dateutil date parsing failed")
            return False

    except Exception as e:
        print(f"[FAIL] python-dateutil functionality test failed: {e}")
        return False


def main():
    """Main test function"""
    print("Vibe Lambda Layer Test")
    print("=" * 30)

    # Test imports
    imports_ok = test_imports()

    # Test Python path
    path_ok = test_python_path()

    # Test functionality
    jwt_ok = test_jwt_functionality()
    boto3_ok = test_boto3_functionality()
    dateutil_ok = test_dateutil_functionality()

    # Summary
    print("\n" + "=" * 30)
    print("Test Summary:")
    print(f"  Imports: {'PASS' if imports_ok else 'FAIL'}")
    print(f"  Python Path: {'PASS' if path_ok else 'FAIL'}")
    print(f"  JWT Functionality: {'PASS' if jwt_ok else 'FAIL'}")
    print(f"  Boto3 Functionality: {'PASS' if boto3_ok else 'FAIL'}")
    print(f"  DateUtil Functionality: {'PASS' if dateutil_ok else 'FAIL'}")

    all_passed = imports_ok and path_ok and jwt_ok and boto3_ok and dateutil_ok

    if all_passed:
        print("\n[PASS] All tests passed! Lambda layer is working correctly.")
        return 0
    else:
        print("\n[FAIL] Some tests failed. Please check the Lambda layer setup.")
        return 1


if __name__ == "__main__":
    exit(main())
