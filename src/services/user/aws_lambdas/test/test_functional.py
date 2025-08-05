#!/usr/bin/env python3
"""
Functional tests for user service utilities
"""

import os
import sys
import traceback
from pathlib import Path
from unittest.mock import Mock, patch

# Add the lambda directories to the path
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
service_aws_lambdas_dir = project_root / "src" / "services" / "user" / "aws_lambdas"
common_aws_lambdas_dir = project_root / "src" / "common" / "aws_lambdas"

print(f"Adding {service_aws_lambdas_dir} to sys.path")
sys.path.insert(0, str(service_aws_lambdas_dir))
print(f"Adding {common_aws_lambdas_dir} to sys.path")
sys.path.insert(0, str(common_aws_lambdas_dir))


def test_auth_utils():
    """Test authentication utility functions"""
    print("Testing auth utilities...")

    try:
        from core.auth_utils import (
            extract_user_id_from_context,
        )
        from core.user_utils import UserManager

        # Test extract_user_id_from_context
        mock_event = {"requestContext": {"authorizer": {"uid": "test_user_123"}}}

        user_id = extract_user_id_from_context(mock_event)
        assert user_id == "test_user_123", f"Expected 'test_user_123', got '{user_id}'"

        print("✓ extract_user_id_from_context works correctly")

        # Test get_allocated_profile_ids with mocked hash function
        with patch("core.user_utils.UserManager.hash_string_to_id") as mock_hash:
            mock_hash.side_effect = lambda x: f"profile_{x.split(':')[1]}"

            profile_ids = UserManager.get_allocated_profile_ids("test_user")
            assert (
                len(profile_ids) == 5
            ), f"Expected 5 profile IDs, got {len(profile_ids)}"
            assert (
                profile_ids[0] == "profile_0"
            ), f"Expected 'profile_0', got '{profile_ids[0]}'"

        print("✓ get_allocated_profile_ids works correctly")

        return True

    except Exception as e:
        print(f"✗ Auth utils test failed: {e}")
        traceback.print_exc()
        return False


def test_rest_utils():
    """Test REST utility functions"""
    print("\nTesting REST utilities...")

    try:
        from core.rest_utils import ResponseError, generate_response

        # Test generate_response
        response = generate_response(200, {"message": "success"})

        assert response["statusCode"] == 200
        assert "Content-Type" in response["headers"]
        assert "Access-Control-Allow-Origin" in response["headers"]

        print("✓ generate_response works correctly")

        # Test ResponseError
        error = ResponseError(400, {"error": "bad request"})
        error_response = error.to_dict()

        assert error_response["statusCode"] == 400
        assert "error" in error_response["body"]

        print("✓ ResponseError works correctly")

        return True

    except Exception as e:
        print(f"✗ REST utils test failed: {e}")
        traceback.print_exc()
        return False


def test_settings():
    """Test settings module"""
    print("\nTesting settings...")

    try:
        from core.settings import CoreSettings

        settings = CoreSettings()
        assert hasattr(settings, "max_profile_count")
        assert settings.max_profile_count == 5

        print("✓ CoreSettings works correctly")

        return True

    except Exception as e:
        print(f"✗ Settings test failed: {e}")
        traceback.print_exc()
        return False


def test_profile_utils():
    """Test profile utility functions (mock-based tests)"""
    print("\nTesting profile utilities...")

    try:
        from core.profile_utils import (
            ProfileManager,
        )

        # Mock DynamoDB dependencies to avoid environment variable requirements
        with patch("core.aws.DynamoDBService.get_table") as mock_table:
            # Create a mock table that returns empty results
            mock_table_instance = Mock()
            mock_table_instance.get_item.return_value = {"Item": None}
            mock_table_instance.query.return_value = {"Items": []}
            mock_table.return_value = mock_table_instance
            
            # Test that ProfileManager can be instantiated (without DynamoDB)
            # Use a valid 8-character user ID that matches the expected format
            valid_user_id = "test1234"
            manager = ProfileManager(valid_user_id, ok_if_not_exists=True)
            assert hasattr(manager, "user_id")
            assert manager.user_id == valid_user_id

        print("✓ Profile utility functions are importable")

        return True

    except Exception as e:
        print(f"✗ Profile utils test failed: {e}")
        traceback.print_exc()
        return False


def test_lambda_handlers():
    """Test that the profile management Lambda handler can be imported and has correct structure"""
    print("\nTesting Lambda handlers...")

    lambda_modules = ["user_profile_mgmt.lambda_function"]

    passed = 0
    failed = 0

    for module_name in lambda_modules:
        try:
            module = __import__(module_name, fromlist=[""])

            # Check if lambda_handler function exists and is callable
            if hasattr(module, "lambda_handler") and callable(module.lambda_handler):
                print(f"✓ {module_name}: lambda_handler is callable")
                passed += 1

                # Test handler function structure by checking expected handler functions
                expected_handlers = [
                    "handle_get_profile",
                    "handle_upsert_profile",
                    "handle_delete_profile",
                ]
                for handler in expected_handlers:
                    if hasattr(module, handler):
                        print(f"✓ {module_name}: {handler} function found")
                    else:
                        print(f"✗ {module_name}: {handler} function not found")

            else:
                print(f"✗ {module_name}: lambda_handler not found or not callable")
                failed += 1

        except Exception as e:
            print(f"✗ {module_name}: Import failed - {e}")
            failed += 1

    print(f"\nLambda handler results: {passed} passed, {failed} failed")
    return failed == 0


def main():
    """Run all functional tests"""
    print("User Service Functional Tests")
    print("=" * 40)

    all_passed = True

    # Test individual utilities
    all_passed &= test_auth_utils()
    all_passed &= test_rest_utils()
    all_passed &= test_settings()
    all_passed &= test_profile_utils()
    all_passed &= test_lambda_handlers()

    print("\n" + "=" * 40)
    if all_passed:
        print("All functional tests PASSED")
        return 0
    else:
        print("Some functional tests FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
