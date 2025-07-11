"""
Test script for Vibe Authentication Service

This script demonstrates how to test the authentication functions locally
before deploying to AWS Lambda.
"""

import json
import os
import sys
from unittest.mock import patch, MagicMock

# Add the lambda directories to the path
telegram_auth_path = os.path.join(os.path.dirname(__file__), "..", "telegram_auth")
jwt_authorizer_path = os.path.join(os.path.dirname(__file__), "..", "jwt_authorizer")
sys.path.insert(0, telegram_auth_path)
sys.path.insert(0, jwt_authorizer_path)

# Import the functions to test
from lambda_function import lambda_handler as telegram_lambda_handler

os.environ["AWS_PROFILE"] = "vibe-dev"
os.environ["AWS_REGION"] = "il-central-1"


# For JWT authorizer, we need to temporarily change the path
def get_jwt_handler():
    """Get JWT authorizer handler by temporarily changing path"""
    import importlib
    import os
    import sys
    jwt_authorizer_abs_path = os.path.abspath(jwt_authorizer_path)
    # Remove both lambda directories from sys.path, then add only jwt_authorizer (absolute)
    sys.path = [p for p in sys.path if jwt_authorizer_abs_path not in p and os.path.abspath(telegram_auth_path) not in p]
    sys.path.insert(0, jwt_authorizer_abs_path)
    if "lambda_function" in sys.modules:
        del sys.modules["lambda_function"]
    lambda_mod = importlib.import_module("lambda_function")
    return lambda_mod.lambda_handler


def test_telegram_auth():
    """Test the Telegram authentication function"""

    # Mock environment variables
    os.environ["TELEGRAM_BOT_TOKEN"] = "test_bot_token"
    os.environ["JWT_SECRET"] = "test_jwt_secret"
    os.environ["DYNAMODB_TABLE"] = "vibe-dating-dev"

    # Mock DynamoDB
    with patch("lambda_function.dynamodb") as mock_dynamodb:
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table

        # Test event
        test_event = {
            "body": json.dumps(
                {
                    "initData": "query_id=AAHdF6IQAAAAAN0XohDhrOrc&user=%7B%22id%22%3A123456789%2C%22first_name%22%3A%22Test%22%2C%22last_name%22%3A%22User%22%2C%22username%22%3A%22testuser%22%7D&auth_date=1234567890&hash=test_hash",
                    "telegramUser": {
                        "id": 123456789,
                        "username": "testuser",
                        "first_name": "Test",
                        "last_name": "User",
                    },
                }
            )
        }

        # Mock the verify_telegram_data function to return True
        with patch("lambda_function.verify_telegram_data", return_value=True):
            response = telegram_lambda_handler(test_event, None)

            print("Telegram Auth Test Response:")
            print(json.dumps(response, indent=2))

            # Verify response structure
            assert response["statusCode"] == 200
            body = json.loads(response["body"])
            assert "token" in body
            assert "userId" in body
            assert "telegramUser" in body

            print("✅ Telegram authentication test passed!")


def test_jwt_authorizer():
    """Test the JWT authorizer function"""
    import importlib
    import sys
    from unittest.mock import patch
    # Mock environment variables
    os.environ["JWT_SECRET"] = "test_jwt_secret"

    # Test event
    test_event = {
        "authorizationToken": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiYUIzY0Q0ZUYiLCJpYXQiOjE2MzQ1Njc4OTAsImV4cCI6MTYzNTQzMTg5MCwiaXNzIjoidmliZS1hcHAifQ.test_signature",
        "methodArn": "arn:aws:execute-api:us-east-1:123456789012:abc123def4/test/GET/users",
    }

    # Mock JWT decode to return a valid payload
    mock_payload = {
        "user_id": "aB3cD4eF",
        "iat": 1634567890,
        "exp": 1635431890,
        "iss": "vibe-app",
    }

    jwt_handler = get_jwt_handler()
    # Patch verify_jwt_token_with_secret_manager in the handler's module
    lambda_mod = sys.modules[jwt_handler.__module__]
    with patch.object(lambda_mod, "verify_jwt_token_with_secret_manager", return_value=mock_payload):
        response = jwt_handler(test_event, None)

        print("JWT Authorizer Test Response:")
        print(json.dumps(response, indent=2))

        # Verify response structure
        assert "principalId" in response
        assert "policyDocument" in response
        assert "context" in response
        assert response["principalId"] == "aB3cD4eF"

        print("✅ JWT authorizer test passed!")


def test_user_id_generation():
    """Test the user ID generation function"""
    import importlib
    import os
    import sys
    from unittest.mock import patch
    telegram_auth_abs_path = os.path.abspath(telegram_auth_path)
    os.environ["DYNAMODB_TABLE"] = "vibe-dating-dev"
    os.environ["UUID_NAMESPACE_SECRET_ARN"] = "dummy-arn"
    # Remove both lambda directories from sys.path, then add only telegram_auth (absolute)
    sys.path = [p for p in sys.path if telegram_auth_abs_path not in p and os.path.abspath(jwt_authorizer_path) not in p]
    sys.path.insert(0, telegram_auth_abs_path)
    if "lambda_function" in sys.modules:
        del sys.modules["lambda_function"]
    lambda_mod = importlib.import_module("lambda_function")
    hash_string_to_id = lambda_mod.hash_string_to_id

    # Patch get_secret_from_aws_secrets_manager to return a valid UUID
    with patch.object(lambda_mod, "get_secret_from_aws_secrets_manager", return_value="123e4567-e89b-12d3-a456-426614174000"):
        # Test cases
        test_cases = [
            ("tg:123456789", 8),
            ("tg:987654321", 8),
            ("tg:111111111", 8),
        ]

        for platform_string, expected_length in test_cases:
            user_id = hash_string_to_id(platform_string, expected_length)

            print(f"Platform: {platform_string}")
            print(f"Generated User ID: {user_id}")
            print(f"Length: {len(user_id)}")
            print(f"Expected Length: {expected_length}")

            # Verify the generated ID
            assert len(user_id) == expected_length
            assert user_id.isalnum()  # Should be alphanumeric

            # Test determinism (same input should produce same output)
            user_id2 = hash_string_to_id(platform_string, expected_length)
            assert user_id == user_id2

            print("• User ID generation test passed!")


def test_error_handling():
    """Test error handling in authentication functions"""

    # Mock environment variables
    os.environ["TELEGRAM_BOT_TOKEN"] = "test_bot_token"
    os.environ["JWT_SECRET"] = "test_jwt_secret"
    os.environ["DYNAMODB_TABLE"] = "vibe-dating-dev"

    # Test missing required fields
    test_event_missing_fields = {
        "body": json.dumps(
            {
                "initData": "test_data"
                # Missing telegramUser
            }
        )
    }

    with patch("lambda_function.dynamodb") as mock_dynamodb:
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table

        response = telegram_lambda_handler(test_event_missing_fields, None)

        print("Error Handling Test Response (Missing Fields):")
        print(json.dumps(response, indent=2))

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "error" in body

        print("✅ Error handling test passed!")


def main():
    """Run all tests"""
    print("• Running Vibe Authentication Service Tests\n")

    try:
        test_user_id_generation()
        print()

        test_telegram_auth()
        print()

        test_jwt_authorizer()
        print()

        test_error_handling()
        print()

        print("✅ All tests passed!")

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
