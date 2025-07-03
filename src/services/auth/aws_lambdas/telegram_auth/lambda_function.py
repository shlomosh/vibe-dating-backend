"""
Vibe Telegram Authentication Lambda Function

This function handles Telegram WebApp authentication and user creation.
"""

import sys
import os

# Add parent directory to path to import shared utilities
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import hmac
import hashlib
import uuid
import base64
import datetime
import jwt
import boto3
from urllib.parse import unquote, parse_qs
from typing import Dict, Any, Optional

# Import auth utilities
from core.auth_utils import (
    verify_jwt_token,
    generate_policy,
    get_secret_from_aws_secrets_manager,
)

# Initialize DynamoDB client
dynamodb = boto3.resource("dynamodb", region_name=os.environ["AWS_REGION"])
table = dynamodb.Table(os.environ["DYNAMODB_TABLE"])


def verify_telegram_data(init_data: str, bot_token: str) -> bool:
    """
    Verify Telegram WebApp init data integrity

    Args:
        init_data: The init data string from Telegram WebApp
        bot_token: The Telegram bot token

    Returns:
        bool: True if data is valid, False otherwise
    """
    try:
        # Parse the init data
        data_pairs = []
        hash_value = None

        for item in init_data.split("&"):
            if item.startswith("hash="):
                hash_value = item[5:]
            else:
                data_pairs.append(item)

        # Sort and join data
        data_pairs.sort()
        data_check_string = "\n".join(data_pairs)

        # Create secret key
        secret_key = hmac.new(
            b"WebAppData", bot_token.encode(), hashlib.sha256
        ).digest()

        # Calculate expected hash
        expected_hash = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()

        return hash_value == expected_hash
    except Exception as e:
        print(f"Error verifying Telegram data: {str(e)}")
        return False


def hash_string_to_id(platform_id_string: str, length: int = 8) -> str:
    """
    Convert platform ID string to Vibe user ID using UUID v5

    Args:
        platform_id_string: String in format "tg:123456789"
        length: Length of the final user ID (default: 8)

    Returns:
        str: Base64 encoded user ID
    """
    # Get UUID namespace from AWS Secrets Manager
    uuid_namespace_arn = os.environ.get("UUID_NAMESPACE_SECRET_ARN")
    if not uuid_namespace_arn:
        raise Exception("UUID_NAMESPACE_SECRET_ARN environment variable not set")

    uuid_namespace = get_secret_from_aws_secrets_manager(uuid_namespace_arn)
    if not uuid_namespace:
        raise Exception("Failed to retrieve UUID namespace from Secrets Manager")

    # Create UUID v5 with namespace from Secrets Manager
    namespace_uuid = uuid.UUID(uuid_namespace)
    user_uuid = uuid.uuid5(namespace_uuid, platform_id_string)

    # Convert UUID to base64
    uuid_bytes = user_uuid.bytes
    base64_string = base64.b64encode(uuid_bytes).decode("utf-8")

    # Remove padding and return first N characters
    return base64_string.rstrip("=")[:length]


def generate_jwt_token(user_id: str) -> str:
    """
    Generate JWT token for authenticated user

    Args:
        user_id: The Vibe user ID

    Returns:
        str: JWT token string
    """
    payload = {
        "user_id": user_id,
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7),
        "iss": "vibe-app",
    }

    # Get JWT secret from AWS Secrets Manager
    jwt_secret_arn = os.environ.get("JWT_SECRET_ARN")
    if not jwt_secret_arn:
        raise Exception("JWT_SECRET_ARN environment variable not set")

    secret = get_secret_from_aws_secrets_manager(jwt_secret_arn)
    if not secret:
        raise Exception("Failed to retrieve JWT secret from Secrets Manager")

    return jwt.encode(payload, secret, algorithm="HS256")


def create_or_update_user(user_id: str, telegram_user: Dict[str, Any]) -> None:
    """
    Create or update user in DynamoDB

    Args:
        user_id: The Vibe user ID
        telegram_user: Telegram user data dictionary
    """
    now = datetime.datetime.utcnow().isoformat() + "Z"

    # Create platform metadata map
    platform_metadata = {
        "username": telegram_user.get("username"),
        "first_name": telegram_user.get("first_name"),
        "last_name": telegram_user.get("last_name"),
        "language_code": telegram_user.get("language_code"),
        "is_premium": telegram_user.get("is_premium", False),
        "added_to_attachment_menu": telegram_user.get(
            "added_to_attachment_menu", False
        ),
    }

    # Use UpdateItem to handle both create and update
    table.update_item(
        Key={"PK": f"USER#{user_id}", "SK": "METADATA"},
        UpdateExpression="SET platform = :platform, platformId = :pid, platformMetadata = :pmd, lastActiveAt = :laa, #prefs = :prefs, GSI1PK = :gsi1pk, GSI1SK = :gsi1sk",
        ExpressionAttributeNames={"#prefs": "preferences"},
        ExpressionAttributeValues={
            ":platform": "tg",
            ":pid": str(telegram_user["id"]),
            ":pmd": platform_metadata,
            ":laa": now,
            ":prefs": {"notifications": True, "privacy": "public"},
            ":gsi1pk": f"USER#{user_id}",
            ":gsi1sk": "METADATA",
        },
    )


def add_security_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """
    Add security headers to response

    Args:
        headers: Existing headers dictionary

    Returns:
        Dict[str, str]: Headers with security headers added
    """
    security_headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
    }

    return {**headers, **security_headers}


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for Telegram authentication

    Args:
        event: Lambda event object
        context: Lambda context object

    Returns:
        Dict[str, Any]: API Gateway response
    """
    try:
        # Parse request body
        body = json.loads(event["body"])
        init_data = body.get("initData")
        telegram_user = body.get("telegramUser")

        if not init_data or not telegram_user:
            return {
                "statusCode": 400,
                "headers": add_security_headers(
                    {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "Content-Type,Authorization",
                        "Access-Control-Allow-Methods": "POST,OPTIONS",
                    }
                ),
                "body": json.dumps({"error": "Missing required fields"}),
            }

        # Verify Telegram data
        telegram_bot_token_arn = os.environ.get("TELEGRAM_BOT_TOKEN_SECRET_ARN")
        if not telegram_bot_token_arn:
            return {
                "statusCode": 500,
                "headers": add_security_headers(
                    {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "Content-Type,Authorization",
                        "Access-Control-Allow-Methods": "POST,OPTIONS",
                    }
                ),
                "body": json.dumps({"error": "Telegram bot token not configured"}),
            }

        bot_token = get_secret_from_aws_secrets_manager(telegram_bot_token_arn)
        if not bot_token:
            return {
                "statusCode": 500,
                "headers": add_security_headers(
                    {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "Content-Type,Authorization",
                        "Access-Control-Allow-Methods": "POST,OPTIONS",
                    }
                ),
                "body": json.dumps({"error": "Failed to retrieve Telegram bot token"}),
            }

        if not verify_telegram_data(init_data, bot_token):
            return {
                "statusCode": 401,
                "headers": add_security_headers(
                    {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "Content-Type,Authorization",
                        "Access-Control-Allow-Methods": "POST,OPTIONS",
                    }
                ),
                "body": json.dumps({"error": "Invalid Telegram data"}),
            }

        # Generate user ID
        platform_id_string = f"tg:{telegram_user['id']}"
        user_id = hash_string_to_id(platform_id_string)

        # Create or update user in DynamoDB
        create_or_update_user(user_id, telegram_user)

        # Generate JWT token
        token = generate_jwt_token(user_id)

        return {
            "statusCode": 200,
            "headers": add_security_headers(
                {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type,Authorization",
                    "Access-Control-Allow-Methods": "POST,OPTIONS",
                }
            ),
            "body": json.dumps(
                {
                    "token": token,
                    "userId": user_id,
                    "telegramUser": {
                        "id": telegram_user["id"],
                        "username": telegram_user.get("username"),
                        "firstName": telegram_user.get("first_name"),
                        "lastName": telegram_user.get("last_name"),
                    },
                }
            ),
        }

    except Exception as e:
        print(f"Error in telegram_auth_handler: {str(e)}")
        return {
            "statusCode": 500,
            "headers": add_security_headers(
                {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type,Authorization",
                    "Access-Control-Allow-Methods": "POST,OPTIONS",
                }
            ),
            "body": json.dumps({"error": "Internal server error"}),
        }
