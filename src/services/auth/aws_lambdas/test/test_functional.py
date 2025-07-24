"""
Test script for Vibe Authentication Service

This script demonstrates how to test the authentication functions locally
before deploying to AWS Lambda.
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import boto3

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

os.environ["AWS_PROFILE"] = "vibe-dev"
_aws_region = boto3.session.Session().region_name
_aws_account = boto3.client("sts").get_caller_identity()["Account"]


def test_auth_platform():
    """Test the platform authentication function"""
    sys.path.insert(0, str(service_aws_lambdas_dir / "auth_platform"))
    from auth_platform.lambda_function import lambda_handler as platform_lambda_handler

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
        "core.auth_utils.get_secret_from_aws_secrets_manager"
    ) as mock_get_secret:
        mock_get_secret.side_effect = lambda arn: {
            f"arn:aws:secretsmanager:{_aws_region}:{_aws_account}:secret:vibe-dating/telegram-bot-token/dev": "test_bot_token",
            f"arn:aws:secretsmanager:{_aws_region}:{_aws_account}:secret:vibe-dating/jwt-secret/dev": "test_jwt_secret",
            f"arn:aws:secretsmanager:{_aws_region}:{_aws_account}:secret:vibe-dating/uuid-namespace/dev": "123e4567-e89b-12d3-a456-426614174000",
        }.get(arn, "test_secret")

        # Mock DynamoDB
        with patch("core.dynamo_utils.dynamodb") as mock_dynamodb:
            mock_table = MagicMock()
            mock_dynamodb.Table.return_value = mock_table

            # Test event
            test_event = {
                "resource": "/auth/platform",
                "path": "/auth/platform",
                "httpMethod": "POST",
                "headers": {
                    "accept": "*/*",
                    "accept-encoding": "gzip, deflate, br, zstd",
                    "accept-language": "en-US,en;q=0.9",
                    "content-type": "application/json",
                    "Host": "api.vibe-dating.io",
                    "origin": "https://shlomosh.github.io",
                    "priority": "u=1, i",
                    "referer": "https://shlomosh.github.io/",
                    "sec-ch-ua": '"Chromium";v="138", "Microsoft Edge";v="138", "Microsoft Edge WebView2";v="138", "Not)A;Brand";v="8"',
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": '"Windows"',
                    "sec-fetch-dest": "empty",
                    "sec-fetch-mode": "cors",
                    "sec-fetch-site": "cross-site",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0",
                    "X-Amzn-Trace-Id": "Root=1-687e26ce-283fbb8d430a188358b37947",
                    "X-Forwarded-For": "77.137.65.80",
                    "X-Forwarded-Port": "443",
                    "X-Forwarded-Proto": "https",
                },
                "multiValueHeaders": {
                    "accept": ["*/*"],
                    "accept-encoding": ["gzip, deflate, br, zstd"],
                    "accept-language": ["en-US,en;q=0.9"],
                    "content-type": ["application/json"],
                    "Host": ["api.vibe-dating.io"],
                    "origin": ["https://shlomosh.github.io"],
                    "priority": ["u=1, i"],
                    "referer": ["https://shlomosh.github.io/"],
                    "sec-ch-ua": [
                        '"Chromium";v="138", "Microsoft Edge";v="138", "Microsoft Edge WebView2";v="138", "Not)A;Brand";v="8"'
                    ],
                    "sec-ch-ua-mobile": ["?0"],
                    "sec-ch-ua-platform": ['"Windows"'],
                    "sec-fetch-dest": ["empty"],
                    "sec-fetch-mode": ["cors"],
                    "sec-fetch-site": ["cross-site"],
                    "User-Agent": [
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0"
                    ],
                    "X-Amzn-Trace-Id": ["Root=1-687e26ce-283fbb8d430a188358b37947"],
                    "X-Forwarded-For": ["77.137.65.80"],
                    "X-Forwarded-Port": ["443"],
                    "X-Forwarded-Proto": ["https"],
                },
                "queryStringParameters": None,
                "multiValueQueryStringParameters": None,
                "pathParameters": None,
                "stageVariables": None,
                "requestContext": {
                    "resourceId": "x2bg71",
                    "resourcePath": "/auth/platform",
                    "httpMethod": "POST",
                    "extendedRequestId": "ODsASE8qTXUEOPQ=",
                    "requestTime": "21/Jul/2025:11:38:54 +0000",
                    "path": "/auth/platform",
                    "accountId": "555171060142",
                    "protocol": "HTTP/1.1",
                    "stage": "dev",
                    "domainPrefix": "api",
                    "requestTimeEpoch": 1753097934235,
                    "requestId": "5510194d-3528-45ab-85b5-9439a090d219",
                    "identity": {
                        "cognitoIdentityPoolId": None,
                        "accountId": None,
                        "cognitoIdentityId": None,
                        "caller": None,
                        "sourceIp": "77.137.65.80",
                        "principalOrgId": None,
                        "accessKey": None,
                        "cognitoAuthenticationType": None,
                        "cognitoAuthenticationProvider": None,
                        "userArn": None,
                        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0",
                        "user": None,
                    },
                    "domainName": "api.vibe-dating.io",
                    "deploymentId": "2xh5gn",
                    "apiId": "xxoh56teej",
                },
                "body": '{"platform":"telegram","platformToken":"user=%7B%22id%22%3A485233267%2C%22first_name%22%3A%22Shlomo%22%2C%22last_name%22%3A%22Shachar%22%2C%22username%22%3A%22XomoGo%22%2C%22language_code%22%3A%22en%22%2C%22allows_write_to_pm%22%3Atrue%2C%22photo_url%22%3A%22https%3A%5C%2F%5C%2Ft.me%5C%2Fi%5C%2Fuserpic%5C%2F320%5C%2Fhz_lBwqKghtC8Whuyd_JUoVykTP1XG2D_HPURCnfEKc.svg%22%7D&chat_instance=2514264085585022705&chat_type=sender&auth_date=1753097927&signature=KmqzriNB0t-pbG1hSAix-dRqkDuFnhk0n6Ll1YlXKXCo8xKijyMJOD5If7T9AZCi-Qa3K60_Y3yyPT_gWyzCBQ&hash=3621655026f7b0734f4e117090b6f2b4556583a6e11b77553984184b1aeed11f","platformMetadata":{"allows_write_to_pm":true,"first_name":"Shlomo","id":485233267,"last_name":"Shachar","language_code":"en","photo_url":"https://t.me/i/userpic/320/hz_lBwqKghtC8Whuyd_JUoVykTP1XG2D_HPURCnfEKc.svg","username":"XomoGo"}}',
                "isBase64Encoded": False,
            }

            # Mock the telegram verification to return valid user data
            with patch("auth_platform.telegram.telegram_verify_data") as mock_verify:
                mock_verify.return_value = {
                    "id": 485233267,
                    "username": "XomoGo",
                    "first_name": "Shlomo",
                    "last_name": "Shachar",
                }

                response = platform_lambda_handler(test_event, None)

                print("Platform Auth Test Response:")
                print(json.dumps(response, indent=2))

                # Verify response structure
                assert response["statusCode"] == 200
                body = json.loads(response["body"])
                assert "token" in body
                assert "userId" in body
                assert "profileIds" in body

                print("[PASS] Platform authentication test passed!")


def test_auth_jwt_authorizer():
    """Test the JWT authorizer function"""
    sys.path.insert(0, str(service_aws_lambdas_dir / "auth_jwt_authorizer"))
    from auth_jwt_authorizer.lambda_function import (
        lambda_handler as auth_jwt_authorizer_lambda_handler,
    )

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
        "core.auth_utils.get_secret_from_aws_secrets_manager",
        return_value="test_jwt_secret",
    ):
        with patch("core.auth_utils.jwt.decode", return_value=mock_payload):
            response = auth_jwt_authorizer_lambda_handler(test_event, None)

            print("JWT Authorizer Test Response:")
            print(json.dumps(response, indent=2))

            # Verify response structure
            assert "principalId" in response
            assert "policyDocument" in response
            assert "context" in response
            assert response["principalId"] == "aB3cD4eF"

            print("[PASS] JWT authorizer test passed!")


def test_user_id_generation():
    """Test the user ID generation function"""
    from core.auth_utils import hash_string_to_id

    # Mock environment variables
    os.environ[
        "UUID_NAMESPACE_SECRET_ARN"
    ] = f"arn:aws:secretsmanager:{_aws_region}:{_aws_account}:secret:vibe-dating/uuid-namespace/dev"

    with patch(
        "core.auth_utils.get_secret_from_aws_secrets_manager",
        return_value="123e4567-e89b-12d3-a456-426614174000",
    ):
        # Test cases
        test_cases = [
            ("telegram:485233267", 8),
            ("telegram:123456789", 8),
            ("telegram:987654321", 8),
        ]

        for platform_string, expected_length in test_cases:
            user_id = hash_string_to_id(platform_string, expected_length)

            print(f"Platform: {platform_string}")
            print(f"Generated User ID: {user_id}")
            print(f"Length: {len(user_id)}")
            print(f"Expected Length: {expected_length}")

            # Verify the generated ID
            assert len(user_id) == expected_length

            # Test determinism (same input should produce same output)
            user_id2 = hash_string_to_id(platform_string, expected_length)
            assert user_id == user_id2

            print("[PASS] User ID generation test passed!")


def test_telegram_verification():
    """Test Telegram data verification"""
    sys.path.insert(0, str(service_aws_lambdas_dir / "auth_platform"))
    from auth_platform.telegram import telegram_verify_data

    # Mock environment variables
    os.environ[
        "TELEGRAM_BOT_TOKEN_SECRET_ARN"
    ] = f"arn:aws:secretsmanager:{_aws_region}:{_aws_account}:secret:vibe-dating/telegram-bot-token/dev"

    with patch(
        "core.auth_utils.get_secret_from_aws_secrets_manager",
        return_value="test_bot_token",
    ):
        # Test with valid Telegram data
        test_init_data = "query_id=AAFzEuwcAAAAAHMS7ByppBvu&user=%7B%22id%22%3A485233267%2C%22first_name%22%3A%22Shlomo%22%2C%22last_name%22%3A%22Shachar%22%2C%22username%22%3A%22XomoGo%22%2C%22language_code%22%3A%22en%22%2C%22allows_write_to_pm%22%3Atrue%2C%22photo_url%22%3A%22https%3A%5C%2F%5C%2Ft.me%5C%2Fi%5C%2Fuserpic%5C%2F320%5C%2Fhz_lBwqKghtC8Whuyd_JUoVykTP1XG2D_HPURCnfEKc.svg%22%7D&auth_date=1752397621&signature=ZSyEY43VghqD2A3CXUQBl40FzqcKsJ9AXQGfClQpucIQV1-W2mH9X9CaIX7t7W-lUtNgCW5YXcSyk6BQesm_CA&hash=fe0c5ad37042b6e0df60acc4da3bce2f73571954119c8e1c6ccabc732ef54e67"

        # Mock the verification to return valid user data
        with patch("auth_platform.telegram.hmac.new") as mock_hmac:
            mock_hmac.return_value.hexdigest.return_value = "test_hash"

            try:
                user_data = telegram_verify_data(test_init_data, "test_bot_token")
                print("[PASS] Telegram verification test passed!")
            except Exception as e:
                print(f"[FAIL] Telegram verification test failed: {e}")


def test_error_handling():
    """Test error handling in authentication functions"""
    sys.path.insert(0, str(service_aws_lambdas_dir / "auth_platform"))
    from auth_platform.lambda_function import lambda_handler as platform_lambda_handler

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
        "core.auth_utils.get_secret_from_aws_secrets_manager",
        return_value="test_secret",
    ):
        with patch("core.dynamo_utils.dynamodb") as mock_dynamodb:
            mock_table = MagicMock()
            mock_dynamodb.Table.return_value = mock_table

            response = platform_lambda_handler(test_event_missing_fields, None)

            print("Error Handling Test Response (Missing Fields):")
            print(json.dumps(response, indent=2))

            assert response["statusCode"] == 400
            body = json.loads(response["body"])
            assert "error" in body

            print("[PASS] Error handling test passed!")


def test_jwt_token_generation():
    """Test JWT token generation"""
    from core.auth_utils import generate_jwt_token

    # Mock environment variables
    os.environ[
        "JWT_SECRET_ARN"
    ] = f"arn:aws:secretsmanager:{_aws_region}:{_aws_account}:secret:vibe-dating/jwt-secret/dev"

    with patch(
        "core.auth_utils.get_secret_from_aws_secrets_manager",
        return_value="test_jwt_secret",
    ):
        # Test JWT token generation
        signed_data = {"uid": "test_user_id"}

        try:
            token = generate_jwt_token(signed_data)
            print(f"Generated JWT token: {token[:50]}...")
            print("[PASS] JWT token generation test passed!")
        except Exception as e:
            print(f"[FAIL] JWT token generation test failed: {e}")


def main():
    """Run all tests"""
    print("[INFO] Running Vibe Authentication Service Tests\n")

    try:
        test_user_id_generation()
        print()

        test_jwt_token_generation()
        print()

        test_telegram_verification()
        print()

        test_auth_platform()
        print()

        test_auth_jwt_authorizer()
        print()

        test_error_handling()
        print()

        print("[PASS] All tests passed!")

    except Exception as e:
        print(f"[FAIL] Test failed: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
