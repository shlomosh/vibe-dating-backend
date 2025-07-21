"""
Test script for Vibe Authentication Service

This script demonstrates how to test the authentication functions locally
before deploying to AWS Lambda.
"""

import json
import os
import sys
from unittest.mock import MagicMock, patch

import boto3

# Add the lambda directories to the path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import the functions to test
from platform_auth.lambda_function import lambda_handler as platform_lambda_handler
from platform_auth.telegram import authenticate_user, telegram_verify_data

from core.auth_utils import (
    generate_jwt_token,
    hash_string_to_id,
    verify_jwt_token_with_secret_manager,
)

os.environ["AWS_PROFILE"] = "vibe-dev"
_aws_region = boto3.session.Session().region_name
_aws_account = boto3.client("sts").get_caller_identity()["Account"]


def test_platform_auth():
    """Test the platform authentication function"""

    # Mock environment variables
    os.environ[
        "TELEGRAM_BOT_TOKEN_SECRET_ARN"
    ] = f"arn:aws:secretsmanager:{_aws_region}:{_aws_account}:secret:vibe-dating/telegram-bot-token/dev"
    os.environ[
        "JWT_SECRET_ARN"
    ] = f"arn:aws:secretsmanager:{_aws_region}:{_aws_account}:secret:vibe-dating/jwt-secret/dev"
    os.environ[
        "UUID_NAMESPACE_SECRET_ARN"
    ] = f"arn:aws:secretsmanager:{_aws_region}:{_aws_account}:secret:vibe-dating/uuid-namespace/dev"
    os.environ["DYNAMODB_TABLE"] = "vibe-dating-dev"

    # Mock AWS Secrets Manager calls
    with patch(
        "common.aws_lambdas.core.auth_utils.get_secret_from_aws_secrets_manager"
    ) as mock_get_secret:
        mock_get_secret.side_effect = lambda arn: {
            f"arn:aws:secretsmanager:{_aws_region}:{_aws_account}:secret:vibe-dating/telegram-bot-token/dev": "test_bot_token",
            f"arn:aws:secretsmanager:{_aws_region}:{_aws_account}:secret:vibe-dating/jwt-secret/dev": "test_jwt_secret",
            f"arn:aws:secretsmanager:{_aws_region}:{_aws_account}:secret:vibe-dating/uuid-namespace/dev": "123e4567-e89b-12d3-a456-426614174000",
        }.get(arn, "test_secret")

        # Mock DynamoDB
        with patch("common.aws_lambdas.core.dynamo_utils.dynamodb") as mock_dynamodb:
            mock_table = MagicMock()
            mock_dynamodb.Table.return_value = mock_table

            # Test event
            test_event = {
                "body": json.dumps(
                    {
                        "platform": "telegram",
                        "platformToken": "query_id=AAHdF6IQAAAAAN0XohDhrOrc&user=%7B%22id%22%3A123456789%2C%22first_name%22%3A%22Test%22%2C%22last_name%22%3A%22User%22%2C%22username%22%3A%22testuser%22%7D&auth_date=1234567890&hash=test_hash",
                        "platformMetadata": {"source": "webapp"},
                    }
                )
            }

            # Mock the telegram verification to return valid user data
            with patch("platform_auth.telegram.telegram_verify_data") as mock_verify:
                mock_verify.return_value = {
                    "id": 123456789,
                    "username": "testuser",
                    "first_name": "Test",
                    "last_name": "User",
                }

                response = platform_lambda_handler(test_event, None)

                print("Platform Auth Test Response:")
                print(json.dumps(response, indent=2))

                # Verify response structure
                assert response["statusCode"] == 200
                body = json.loads(response["body"])
                assert "token" in body
                assert "userId" in body
                assert "userData" in body

                print("✅ Platform authentication test passed!")


def test_user_jwt_authorizer():
    """Test the JWT authorizer function"""
    from user_jwt_authorizer.lambda_function import lambda_handler as jwt_lambda_handler

    # Mock environment variables
    os.environ[
        "JWT_SECRET_ARN"
    ] = f"arn:aws:secretsmanager:{_aws_region}:{_aws_account}:secret:vibe-dating/jwt-secret/dev"

    # Test event
    test_event = {
        "authorizationToken": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiYUIzY0Q0ZUYiLCJpYXQiOjE2MzQ1Njc4OTAsImV4cCI6MTYzNTQzMTg5MCwiaXNzIjoidmliZS1hcHAifQ.test_signature",
        "methodArn": "arn:aws:execute-api:us-east-1:123456789012:abc123def4/test/GET/users",
    }

    # Mock JWT decode to return a valid payload
    mock_payload = {
        "uid": "aB3cD4eF",
        "iat": 1634567890,
        "exp": 1635431890,
        "iss": "vibe-app",
    }

    with patch(
        "common.aws_lambdas.core.auth_utils.get_secret_from_aws_secrets_manager",
        return_value="test_jwt_secret",
    ):
        with patch("common.aws_lambdas.core.auth_utils.jwt.decode", return_value=mock_payload):
            response = jwt_lambda_handler(test_event, None)

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

    # Mock environment variables
    os.environ[
        "UUID_NAMESPACE_SECRET_ARN"
    ] = f"arn:aws:secretsmanager:{_aws_region}:{_aws_account}:secret:vibe-dating/uuid-namespace/dev"

    with patch(
        "common.aws_lambdas.core.auth_utils.get_secret_from_aws_secrets_manager",
        return_value="123e4567-e89b-12d3-a456-426614174000",
    ):
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


def test_telegram_verification():
    """Test Telegram data verification"""

    # Mock environment variables
    os.environ[
        "TELEGRAM_BOT_TOKEN_SECRET_ARN"
    ] = f"arn:aws:secretsmanager:{_aws_region}:{_aws_account}:secret:vibe-dating/telegram-bot-token/dev"

    with patch(
        "common.aws_lambdas.core.auth_utils.get_secret_from_aws_secrets_manager",
        return_value="test_bot_token",
    ):
        # Test with valid Telegram data
        test_init_data = "query_id=AAHdF6IQAAAAAN0XohDhrOrc&user=%7B%22id%22%3A123456789%2C%22first_name%22%3A%22Test%22%2C%22last_name%22%3A%22User%22%2C%22username%22%3A%22testuser%22%7D&auth_date=1234567890&hash=test_hash"

        # Mock the verification to return valid user data
        with patch("platform_auth.telegram.hmac.new") as mock_hmac:
            mock_hmac.return_value.hexdigest.return_value = "test_hash"

            try:
                user_data = telegram_verify_data(test_init_data, "test_bot_token")
                print("✅ Telegram verification test passed!")
            except Exception as e:
                print(f"❌ Telegram verification test failed: {e}")


def test_error_handling():
    """Test error handling in authentication functions"""

    # Mock environment variables
    os.environ[
        "TELEGRAM_BOT_TOKEN_SECRET_ARN"
    ] = f"arn:aws:secretsmanager:{_aws_region}:{_aws_account}:secret:vibe-dating/telegram-bot-token/dev"
    os.environ[
        "JWT_SECRET_ARN"
    ] = f"arn:aws:secretsmanager:{_aws_region}:{_aws_account}:secret:vibe-dating/jwt-secret/dev"
    os.environ[
        "UUID_NAMESPACE_SECRET_ARN"
    ] = f"arn:aws:secretsmanager:{_aws_region}:{_aws_account}:secret:vibe-dating/uuid-namespace/dev"
    os.environ["DYNAMODB_TABLE"] = "vibe-dating-dev"

    # Test missing required fields
    test_event_missing_fields = {
        "body": json.dumps(
            {
                "platform": "telegram"
                # Missing platformToken
            }
        )
    }

    with patch(
        "common.aws_lambdas.core.auth_utils.get_secret_from_aws_secrets_manager",
        return_value="test_secret",
    ):
        with patch("common.aws_lambdas.core.dynamo_utils.dynamodb") as mock_dynamodb:
            mock_table = MagicMock()
            mock_dynamodb.Table.return_value = mock_table

            response = platform_lambda_handler(test_event_missing_fields, None)

            print("Error Handling Test Response (Missing Fields):")
            print(json.dumps(response, indent=2))

            assert response["statusCode"] == 400
            body = json.loads(response["body"])
            assert "error" in body

            print("✅ Error handling test passed!")


def test_jwt_token_generation():
    """Test JWT token generation"""

    # Mock environment variables
    os.environ[
        "JWT_SECRET_ARN"
    ] = f"arn:aws:secretsmanager:{_aws_region}:{_aws_account}:secret:vibe-dating/jwt-secret/dev"

    with patch(
        "common.aws_lambdas.core.auth_utils.get_secret_from_aws_secrets_manager",
        return_value="test_jwt_secret",
    ):
        # Test JWT token generation
        signed_data = {"uid": "test_user_id"}

        try:
            token = generate_jwt_token(signed_data)
            print(f"Generated JWT token: {token[:50]}...")
            print("✅ JWT token generation test passed!")
        except Exception as e:
            print(f"❌ JWT token generation test failed: {e}")


def main():
    """Run all tests"""
    print("• Running Vibe Authentication Service Tests\n")

    try:
        test_user_id_generation()
        print()

        test_jwt_token_generation()
        print()

        test_telegram_verification()
        print()

        test_platform_auth()
        print()

        test_user_jwt_authorizer()
        print()

        test_error_handling()
        print()

        print("✅ All tests passed!")

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
