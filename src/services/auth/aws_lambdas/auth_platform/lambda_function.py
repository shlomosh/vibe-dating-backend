"""
Vibe Platform Authentication Lambda Function

This function handles platform authentication and user creation.
"""

import datetime
import os
from typing import Any, Dict

import jwt

from core.aws import SecretsManagerService
from core.rest_utils import ResponseError, generate_response, parse_request_body
from core.user_utils import UserManager


def _api_generate_jwt_token(signed_data: Dict[str, Any], expires_in: int = 7) -> str:
    """
    Generate JWT token for authenticated user

    Args:
        signed_data: Data to include in the JWT token
        expires_in: Number of days until token expires (default: 7)

    Returns:
        str: JWT token string
    """
    now = datetime.datetime.utcnow()
    payload = {
        **signed_data,
        "iat": int(now.timestamp()),
        "exp": int((now + datetime.timedelta(days=expires_in)).timestamp()),
        "iss": "vibe-app",
    }

    # Get JWT secret from AWS Secrets Manager
    jwt_secret_arn = os.environ.get("JWT_SECRET_ARN")
    if not jwt_secret_arn:
        raise Exception("JWT_SECRET_ARN environment variable not set")

    secret = SecretsManagerService.get_secret(jwt_secret_arn)
    if not secret:
        raise Exception("Failed to retrieve JWT secret from Secrets Manager")

    return jwt.encode(payload, secret, algorithm="HS256")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for platform authentication

    Args:
        event: Lambda event object
        context: Lambda context object

    Returns:
        Dict[str, Any]: API Gateway response
    """
    try:
        import json

        print(f"Auth Platform Event: {json.dumps(event)}")

        # Parse request body
        body = parse_request_body(event)

        platform = body.get("platform")
        platform_token = body.get("platformToken")
        platform_metadata = body.get("platformMetadata", {})

        if not platform or not platform_token:
            raise ResponseError(400, {"error": "Missing required fields"})

        if platform == "telegram":
            from telegram import TelegramPlatform

            platform_user_data = TelegramPlatform(
                platform_token=platform_token,
                get_secret_f=SecretsManagerService.get_secret,
            ).authenticate()
            if not platform_user_data:
                raise ResponseError(400, {"error": "Failed to authenticate user"})

            platform_user_id = platform_user_data.get("id")
        else:
            raise ResponseError(400, {"error": "Invalid platform"})

        user_mgmt = UserManager(platform=platform, platform_user_id=platform_user_id)

        # create / update user record
        user_mgmt.upsert(platform, platform_user_id, platform_metadata)

        if user_mgmt.is_banned():
            raise ResponseError(403, {"error": "Account is banned"})

        # Generate JWT token
        token = _api_generate_jwt_token(signed_data={"uid": user_mgmt.user_id})

        return generate_response(
            200,
            {
                "token": token,
                "userId": user_mgmt.user_id,
                "profileIds": user_mgmt.get()["allocatedProfileIds"],
            },
        )

    except ResponseError as e:
        return e.to_dict()

    except Exception as ex:
        return ResponseError(
            500, {"error": f"Internal server error: {str(ex)}"}
        ).to_dict()
