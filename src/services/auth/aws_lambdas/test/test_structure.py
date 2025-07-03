"""
Test script to verify the new code structure and imports work correctly
"""

import sys
import os


def test_auth_utils_import():
    """Test that auth_utils can be imported"""
    print("Testing auth_utils import...")

    try:
        # Add parent directory to path to import auth_utils
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from core.auth_utils import verify_jwt_token, generate_policy

        print("+ auth_utils imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import auth_utils: {e}")
        return False


def test_jwt_authorizer_import():
    """Test that JWT authorizer can be imported"""
    print("\nTesting JWT authorizer import...")

    try:
        # Add jwt_authorizer directory to path
        jwt_authorizer_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "jwt_authorizer"
        )
        sys.path.insert(0, jwt_authorizer_path)

        from lambda_function import lambda_handler

        print("+ JWT authorizer lambda_function imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import JWT authorizer: {e}")
        return False


def test_telegram_auth_import():
    """Test that Telegram auth can be imported"""
    print("\nTesting Telegram auth import...")

    try:
        # Add telegram_auth directory to path
        telegram_auth_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "telegram_auth"
        )
        sys.path.insert(0, telegram_auth_path)

        from lambda_function import lambda_handler

        print("+ Telegram auth lambda_function imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import Telegram auth: {e}")
        return False


def test_auth_functions():
    """Test that auth functions work correctly"""
    print("\nTesting auth functions...")

    try:
        from core.auth_utils import verify_jwt_token, generate_policy

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
            print("❌ generate_policy function failed")
            return False

    except Exception as e:
        print(f"❌ Auth functions test failed: {e}")
        return False


def main():
    """Main test function"""
    print("Vibe Code Structure Test")
    print("=" * 30)

    # Test imports
    auth_ok = test_auth_utils_import()
    jwt_ok = test_jwt_authorizer_import()
    telegram_ok = test_telegram_auth_import()

    # Test functionality
    functions_ok = test_auth_functions()

    # Summary
    print("\n" + "=" * 30)
    print("Test Summary:")
    print(f"  Auth Utils Import: {'+ PASS' if auth_ok else 'X FAIL'}")
    print(f"  JWT Authorizer Import: {'+ PASS' if jwt_ok else 'X FAIL'}")
    print(f"  Telegram Auth Import: {'+ PASS' if telegram_ok else 'X FAIL'}")
    print(f"  Auth Functions: {'+ PASS' if functions_ok else 'X FAIL'}")

    all_passed = auth_ok and jwt_ok and telegram_ok and functions_ok

    if all_passed:
        print("\n+ All tests passed! Code structure is working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the code structure.")
        return 1


if __name__ == "__main__":
    exit(main())
