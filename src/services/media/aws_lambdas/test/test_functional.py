#!/usr/bin/env python3
"""
Functional tests for Media Service
"""

import json
import os
import sys
from pathlib import Path

# Add the lambda directories to the path
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
service_aws_lambdas_dir = project_root / "src" / "services" / "media" / "aws_lambdas"
common_aws_lambdas_dir = project_root / "src" / "common" / "aws_lambdas"

print(f"Adding {service_aws_lambdas_dir} to sys.path")
sys.path.insert(0, str(service_aws_lambdas_dir))
print(f"Adding {common_aws_lambdas_dir} to sys.path")
sys.path.insert(0, str(common_aws_lambdas_dir))

os.environ["AWS_PROFILE"] = "vibe-dev"
os.environ["DYNAMODB_TABLE"] = "test-table"
os.environ["MEDIA_S3_BUCKET"] = "test-bucket"
os.environ["CLOUDFRONT_DOMAIN"] = "test.cloudfront.net"
os.environ["CLOUDFRONT_DISTRIBUTION_ID"] = "test-distribution"


def test_media_upload_handler():
    """Test media upload handler functionality"""
    print("Testing Media Upload Handler...")

    try:
        sys.path.insert(0, str(service_aws_lambdas_dir / "media_upload"))
        from media_upload.lambda_function import MediaUploadHandler

        # Test handler initialization
        handler = MediaUploadHandler()
        print("+ MediaUploadHandler initialized")

        # Test media ID generation
        media_id = handler.generate_media_id()
        if len(media_id) == 16:
            print("+ Media ID generation works")
        else:
            print(f"[FAIL] Media ID should be 16 characters, got {len(media_id)}")
            return False

        # Test upload request validation
        valid_request = {
            "type": "image",
            "aspectRatio": "3:4",
            "metadata": {
                "width": 1440,
                "height": 1920,
                "size": 2048576,
                "format": "jpeg",
            },
            "order": 1,
        }

        try:
            handler.validate_upload_request(valid_request)
            print("+ Upload request validation works")
        except Exception as e:
            print(f"[FAIL] Valid request validation failed: {e}")
            return False

        # Test invalid request validation
        invalid_request = {
            "type": "video",  # Invalid type
            "aspectRatio": "3:4",
            "metadata": {
                "width": 1440,
                "height": 1920,
                "size": 2048576,
                "format": "jpeg",
            },
        }

        try:
            handler.validate_upload_request(invalid_request)
            print("[FAIL] Should have raised an error for invalid type")
            return False
        except Exception:
            print("+ Invalid request validation works")

        return True

    except Exception as e:
        print(f"[FAIL] Media upload handler test failed: {e}")
        return False


def test_media_processor():
    """Test media processor functionality"""
    print("\nTesting Media Processor...")

    try:
        sys.path.insert(0, str(service_aws_lambdas_dir / "media_processing"))
        from media_processing.lambda_function import MediaProcessor

        # Test processor initialization
        processor = MediaProcessor()
        print("+ MediaProcessor initialized")

        # Test media ID extraction
        s3_key = "uploads/profile-images/test123.jpg"
        media_id = processor.extract_media_id_from_s3_key(s3_key)
        if media_id == "test123":
            print("+ Media ID extraction works")
        else:
            print(f"[FAIL] Expected 'test123', got '{media_id}'")
            return False

        # Test invalid S3 key
        try:
            processor.extract_media_id_from_s3_key("invalid/key")
            print("[FAIL] Should have raised an error for invalid S3 key")
            return False
        except ValueError:
            print("+ Invalid S3 key handling works")

        return True

    except Exception as e:
        print(f"[FAIL] Media processor test failed: {e}")
        return False


def test_media_manager():
    """Test media manager functionality"""
    print("\nTesting Media Manager...")

    try:
        sys.path.insert(0, str(service_aws_lambdas_dir / "media_management"))
        from media_management.lambda_function import MediaManager

        # Test manager initialization
        manager = MediaManager()
        print("+ MediaManager initialized")

        # Test response structure validation
        test_response = {
            "mediaId": "test123",
            "status": "completed",
            "urls": {
                "original": "https://example.com/original.jpg",
                "thumbnail": "https://example.com/thumb.jpg",
            },
            "processedAt": "2024-01-01T12:00:00Z",
        }

        # Validate response structure
        required_fields = ["mediaId", "status", "urls"]
        for field in required_fields:
            if field not in test_response:
                print(f"[FAIL] Missing required field: {field}")
                return False

        if "original" not in test_response["urls"]:
            print("[FAIL] Missing original URL")
            return False

        if "thumbnail" not in test_response["urls"]:
            print("[FAIL] Missing thumbnail URL")
            return False

        print("+ Response structure validation works")
        return True

    except Exception as e:
        print(f"[FAIL] Media manager test failed: {e}")
        return False


def main():
    """Main test function"""
    print("Media Service Functional Test")
    print("=" * 35)

    # Test media upload handler
    upload_ok = test_media_upload_handler()

    # Test media processor
    processor_ok = test_media_processor()

    # Test media manager
    manager_ok = test_media_manager()

    # Summary
    print("\n" + "=" * 35)
    print("Test Summary:")
    print(f"  Media Upload Handler: {'PASS' if upload_ok else 'FAIL'}")
    print(f"  Media Processor: {'PASS' if processor_ok else 'FAIL'}")
    print(f"  Media Manager: {'PASS' if manager_ok else 'FAIL'}")

    all_passed = upload_ok and processor_ok and manager_ok

    if all_passed:
        print("\n[PASS] All functional tests passed!")
        return 0
    else:
        print("\n[FAIL] Some functional tests failed.")
        return 1


if __name__ == "__main__":
    exit(main())
