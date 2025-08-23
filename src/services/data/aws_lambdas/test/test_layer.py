#!/usr/bin/env python3
"""
Layer tests for Media Service
"""

import os
import sys

os.environ["AWS_PROFILE"] = "vibe-dev"


def test_imports():
    """Test that all required packages can be imported"""
    print("Testing Media Service Lambda layer imports...")

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

    try:
        import msgspec

        print("+ msgspec imported successfully")
    except ImportError as e:
        print(f"[FAIL] Failed to import msgspec: {e}")
        return False

    try:
        from PIL import Image

        print("+ Pillow imported successfully")
    except ImportError as e:
        print(f"[FAIL] Failed to import Pillow: {e}")
        return False

    return True


def test_pillow_functionality():
    """Test Pillow image processing functionality"""
    print("\nTesting Pillow functionality...")

    try:
        import io

        from PIL import Image

        # Create a simple test image
        test_image = Image.new("RGB", (100, 100), color="red")

        # Test image operations
        buffer = io.BytesIO()
        test_image.save(buffer, format="JPEG")

        print("+ Pillow image processing works correctly")
        return True

    except Exception as e:
        print(f"[FAIL] Pillow functionality test failed: {e}")
        return False


def test_boto3_functionality():
    """Test boto3 functionality"""
    print("\nTesting boto3 functionality...")

    try:
        import boto3

        # Test boto3 client creation (without actual AWS calls)
        s3_client = boto3.client("s3")
        print("+ boto3 S3 client created successfully")

        cloudfront_client = boto3.client("cloudfront")
        print("+ boto3 CloudFront client created successfully")

        return True

    except Exception as e:
        print(f"[FAIL] boto3 functionality test failed: {e}")
        return False


def test_msgspec_functionality():
    """Test msgspec functionality"""
    print("\nTesting msgspec functionality...")

    try:
        import msgspec

        # Test basic serialization/deserialization
        test_data = {"test": "value", "number": 123}
        encoded = msgspec.to_builtins(test_data)
        decoded = msgspec.from_builtins(encoded, dict)

        if decoded == test_data:
            print("+ msgspec serialization/deserialization works correctly")
            return True
        else:
            print("[FAIL] msgspec serialization/deserialization failed")
            return False

    except Exception as e:
        print(f"[FAIL] msgspec functionality test failed: {e}")
        return False


def main():
    """Main test function"""
    print("Media Service Lambda Layer Test")
    print("=" * 40)

    # Test imports
    imports_ok = test_imports()

    # Test functionality
    pillow_ok = test_pillow_functionality()
    boto3_ok = test_boto3_functionality()
    msgspec_ok = test_msgspec_functionality()

    # Summary
    print("\n" + "=" * 40)
    print("Test Summary:")
    print(f"  Imports: {'PASS' if imports_ok else 'FAIL'}")
    print(f"  Pillow Functionality: {'PASS' if pillow_ok else 'FAIL'}")
    print(f"  Boto3 Functionality: {'PASS' if boto3_ok else 'FAIL'}")
    print(f"  Msgspec Functionality: {'PASS' if msgspec_ok else 'FAIL'}")

    all_passed = imports_ok and pillow_ok and boto3_ok and msgspec_ok

    if all_passed:
        print(
            "\n[PASS] All tests passed! Media Service Lambda layer is working correctly."
        )
        return 0
    else:
        print("\n[FAIL] Some tests failed. Please check the Lambda layer setup.")
        return 1


if __name__ == "__main__":
    exit(main())
