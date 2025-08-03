#!/usr/bin/env python3
"""
Structure tests for Media Service
"""

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


def test_file_structure():
    """Test that all required files exist"""
    print("Testing Media Service file structure...")

    # Get the service directory
    current_dir = Path(__file__).parent
    service_dir = current_dir.parent.parent.parent / "media"

    required_files = [
        service_dir / "build.py",
        service_dir / "deploy.py",
        service_dir / "test.py",
        service_dir / "aws_lambdas" / "requirements.json",
        service_dir / "aws_lambdas" / "media_upload" / "lambda_function.py",
        service_dir / "aws_lambdas" / "media_processing" / "lambda_function.py",
        service_dir / "aws_lambdas" / "media_management" / "lambda_function.py",
        service_dir / "cloudformation" / "template.yaml",
    ]

    print(f"Service directory: {service_dir}")
    print(f"Current directory: {current_dir}")

    all_files_exist = True
    for file_path in required_files:
        if file_path.exists():
            print(f"+ {file_path.name} exists")
        else:
            print(f"[FAIL] {file_path.name} not found")
            all_files_exist = False

    return all_files_exist


def test_core_imports():
    """Test that core modules can be imported"""
    print("\nTesting core imports...")

    try:
        from core.aws import DynamoDBService

        print("+ core.aws imported successfully")

        from core.rest_utils import ResponseError, generate_response

        print("+ core.rest_utils imported successfully")

        from core.auth_utils import extract_user_id_from_context

        print("+ core.auth_utils imported successfully")

        from core.profile_utils import ProfileManager

        print("+ core.profile_utils imported successfully")

        return True

    except ImportError as e:
        print(f"[FAIL] Core import failed: {e}")
        return False


def test_media_upload_import():
    """Test that media upload module can be imported"""
    print("\nTesting media upload import...")

    try:
        sys.path.insert(0, str(service_aws_lambdas_dir / "media_upload"))
        from media_upload.lambda_function import MediaUploadHandler

        print("+ MediaUploadHandler imported successfully")
        return True

    except ImportError as e:
        print(f"[FAIL] Failed to import MediaUploadHandler: {e}")
        return False


def test_media_processing_import():
    """Test that media processing module can be imported"""
    print("\nTesting media processing import...")

    try:
        sys.path.insert(0, str(service_aws_lambdas_dir / "media_processing"))
        from media_processing.lambda_function import MediaProcessor

        print("+ MediaProcessor imported successfully")
        return True

    except ImportError as e:
        print(f"[FAIL] Failed to import MediaProcessor: {e}")
        return False


def test_media_management_import():
    """Test that media management module can be imported"""
    print("\nTesting media management import...")

    try:
        sys.path.insert(0, str(service_aws_lambdas_dir / "media_management"))
        from media_management.lambda_function import MediaManager

        print("+ MediaManager imported successfully")
        return True

    except ImportError as e:
        print(f"[FAIL] Failed to import MediaManager: {e}")
        return False


def main():
    """Main test function"""
    print("Media Service Structure Test")
    print("=" * 35)

    # Test file structure
    structure_ok = test_file_structure()

    # Test imports
    core_ok = test_core_imports()
    upload_ok = test_media_upload_import()
    processing_ok = test_media_processing_import()
    management_ok = test_media_management_import()

    # Summary
    print("\n" + "=" * 35)
    print("Test Summary:")
    print(f"  File Structure: {'PASS' if structure_ok else 'FAIL'}")
    print(f"  Core Imports: {'PASS' if core_ok else 'FAIL'}")
    print(f"  Media Upload Import: {'PASS' if upload_ok else 'FAIL'}")
    print(f"  Media Processing Import: {'PASS' if processing_ok else 'FAIL'}")
    print(f"  Media Management Import: {'PASS' if management_ok else 'FAIL'}")

    all_passed = (
        structure_ok and core_ok and upload_ok and processing_ok and management_ok
    )

    if all_passed:
        print("\n[PASS] All structure tests passed!")
        return 0
    else:
        print("\n[FAIL] Some structure tests failed.")
        return 1


if __name__ == "__main__":
    exit(main())
