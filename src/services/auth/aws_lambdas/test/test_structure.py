"""
Test script to verify the new code structure and imports work correctly
"""

import os
import sys
from pathlib import Path

# Add the lambda directories to the path
project_root = str(Path(__file__).parent.parent.parent.parent.parent.parent)
service_aws_lambdas_dir = (
    Path(project_root) / "src" / "services" / "auth" / "aws_lambdas"
)
print(f"Adding {service_aws_lambdas_dir} to sys.path")
sys.path.insert(0, str(service_aws_lambdas_dir))
common_aws_lambdas_dir = Path(project_root) / "src" / "common" / "aws_lambdas"
print(f"Adding {common_aws_lambdas_dir} to sys.path")
sys.path.insert(0, str(common_aws_lambdas_dir))


def test_auth_utils_import():
    """Test that auth_utils can be imported"""
    print("Testing auth_utils import...")

    try:
        from core.auth_utils import (
            generate_jwt_token,
            generate_policy,
            hash_string_to_id,
            verify_jwt_token_with_secret_manager,
        )

        print("+ auth_utils imported successfully")
        return True

    except ImportError as e:
        print(f"[FAIL] Failed to import auth_utils: {e}")
        return False


def test_auth_platform_import():
    """Test that platform auth can be imported"""
    print("\nTesting platform auth import...")

    try:
        sys.path.insert(0, service_aws_lambdas_dir / "auth_platform")
        from auth_platform.lambda_function import (
            lambda_handler as platform_lambda_handler,
        )

        print("+ Platform auth lambda_function imported successfully")
        return True

    except ImportError as e:
        print(f"[FAIL] Failed to import platform auth: {e}")
        return False


def test_auth_jwt_authorizer_import():
    """Test that JWT authorizer can be imported"""
    print("\nTesting JWT authorizer import...")

    try:
        # Add auth_jwt_authorizer directory to path
        sys.path.insert(0, service_aws_lambdas_dir / "auth_jwt_authorizer")
        from auth_jwt_authorizer.lambda_function import (
            lambda_handler as auth_jwt_authorizer_lambda_handler,
        )

        print("+ JWT authorizer lambda_function imported successfully")
        return True

    except ImportError as e:
        print(f"[FAIL] Failed to import JWT authorizer: {e}")
        return False


def test_telegram_module_import():
    """Test that Telegram module can be imported"""
    print("\nTesting Telegram module import...")

    try:
        # Add auth_platform directory to path
        sys.path.insert(0, service_aws_lambdas_dir / "auth_platform")
        from auth_platform.telegram import authenticate_user, telegram_verify_data

        print("+ Telegram module imported successfully")
        return True

    except ImportError as e:
        print(f"[FAIL] Failed to import Telegram module: {e}")
        return False


def test_auth_functions():
    """Test that auth functions work correctly"""
    print("\nTesting auth functions...")

    try:
        from core.auth_utils import generate_policy

        # Test generate_policy function
        policy = generate_policy(
            principal_id="test_user",
            effect="Allow",
            resource="test_resource",
            context={"test": "value"},
        )

        if (
            policy["principalId"] == "test_user"
            and policy["policyDocument"]["Statement"][0]["Effect"] == "Allow"
        ):
            print("+ generate_policy function works correctly")
            return True
        else:
            print("[FAIL] generate_policy function failed")
            return False

    except Exception as e:
        print(f"[FAIL] Auth functions test failed: {e}")
        return False


def test_core_utils_import():
    """Test that core utility modules can be imported"""
    print("\nTesting core utilities import...")

    try:
        from core.dynamo_utils import db_create_or_update_user_record
        from core.rest_utils import ResponseError, generate_response

        print("+ Core utilities imported successfully")
        return True

    except ImportError as e:
        print(f"[FAIL] Failed to import core utilities: {e}")
        return False


def main():
    """Main test function"""
    print("Vibe Code Structure Test")
    print("=" * 30)

    # Test imports
    auth_ok = test_auth_utils_import()
    platform_ok = test_auth_platform_import()
    jwt_ok = test_auth_jwt_authorizer_import()
    telegram_ok = test_telegram_module_import()
    core_ok = test_core_utils_import()

    # Test functionality
    functions_ok = test_auth_functions()

    # Summary
    print("\n" + "=" * 30)
    print("Test Summary:")
    print(f"  Auth Utils Import: {'PASS' if auth_ok else 'FAIL'}")
    print(f"  Platform Auth Import: {'PASS' if platform_ok else 'FAIL'}")
    print(f"  JWT Authorizer Import: {'PASS' if jwt_ok else 'FAIL'}")
    print(f"  Telegram Module Import: {'PASS' if telegram_ok else 'FAIL'}")
    print(f"  Core Utils Import: {'PASS' if core_ok else 'FAIL'}")
    print(f"  Auth Functions: {'PASS' if functions_ok else 'FAIL'}")

    all_passed = (
        auth_ok and platform_ok and jwt_ok and telegram_ok and core_ok and functions_ok
    )

    if all_passed:
        print("\n[PASS] All tests passed! Code structure is working correctly.")
        return 0
    else:
        print("\n[FAIL] Some tests failed. Please check the code structure.")
        return 1


if __name__ == "__main__":
    exit(main())
