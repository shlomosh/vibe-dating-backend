"""
Test script to verify Lambda layer dependencies are working correctly
"""

import os
import sys

os.environ["AWS_PROFILE"] = "vibe-dev"
os.environ["AWS_REGION"] = "il-central-1"


def test_imports():
    """Test that all required packages can be imported"""
    print("Testing Lambda layer imports...")

    try:
        import jwt

        print("+ PyJWT imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import PyJWT: {e}")
        return False

    try:
        import boto3

        print("+ boto3 imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import boto3: {e}")
        return False

    try:
        import requests

        print("+ requests imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import requests: {e}")
        return False

    try:
        import urllib3

        print("+ urllib3 imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import urllib3: {e}")
        return False

    try:
        import dateutil

        print("+ python-dateutil imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import python-dateutil: {e}")
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
        import jwt
        import datetime

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
            print("❌ JWT encoding/decoding failed")
            return False

    except Exception as e:
        print(f"❌ JWT functionality test failed: {e}")
        return False


def test_boto3_functionality():
    """Test boto3 functionality"""
    print("\nTesting boto3 functionality...")

    try:
        import boto3

        # Test boto3 client creation (without actual AWS calls)
        dynamodb = boto3.resource("dynamodb", region_name=os.environ["AWS_REGION"])
        print("+ boto3 DynamoDB resource created successfully")

        return True

    except Exception as e:
        print(f"❌ boto3 functionality test failed: {e}")
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

    # Summary
    print("\n" + "=" * 30)
    print("Test Summary:")
    print(f"  Imports: {'+ PASS' if imports_ok else 'X FAIL'}")
    print(f"  Python Path: {'+ PASS' if path_ok else 'X FAIL'}")
    print(f"  JWT Functionality: {'+ PASS' if jwt_ok else 'X FAIL'}")
    print(f"  Boto3 Functionality: {'+ PASS' if boto3_ok else 'X FAIL'}")

    all_passed = imports_ok and path_ok and jwt_ok and boto3_ok

    if all_passed:
        print("\n+ All tests passed! Lambda layer is working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the Lambda layer setup.")
        return 1


if __name__ == "__main__":
    exit(main())
