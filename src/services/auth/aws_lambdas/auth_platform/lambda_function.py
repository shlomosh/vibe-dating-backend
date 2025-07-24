"""
Vibe Platform Authentication Lambda Function

This function handles platform authentication and user creation.
"""

import base64
import json
import os
from typing import Any, Dict

from core.auth_utils import generate_jwt_token, hash_string_to_id
from core.dynamo_utils import db_create_or_update_user_record
from core.rest_utils import ResponseError, generate_response
from core.settings import CoreSettings


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
        print(f"Event: {event}")

        # Parse request body
        request_body = event.get("body")
        if not request_body:
            raise ResponseError(400, {"error": "Missing request body"})

        # Handle base64 encoded body
        if event.get("isBase64Encoded", False):
            try:
                request_body = base64.b64decode(request_body).decode("utf-8")
            except Exception as e:
                raise ResponseError(
                    400, {"error": f"Failed to decode base64 body: {str(e)}"}
                )

        try:
            body = json.loads(request_body)
        except json.JSONDecodeError as e:
            raise ResponseError(
                400, {"error": f"Invalid JSON in request body: {str(e)}"}
            )

        platform = body.get("platform")
        platform_token = body.get("platformToken")
        platform_metadata = body.get("platformMetadata", {})

        if not platform or not platform_token:
            raise ResponseError(400, {"error": "Missing required fields"})

        if platform == "telegram":
            from telegram import authenticate_user

            platform_user_data = authenticate_user(platform_token)
            if not platform_user_data:
                raise ResponseError(400, {"error": "Failed to authenticate user"})

            platform_user_id = platform_user_data.get("id")
        else:
            raise ResponseError(400, {"error": "Invalid platform"})

        # Generate user ID
        platform_id_string = f"{platform}:{platform_user_id}"
        vibe_user_id = hash_string_to_id(platform_id_string)

        # Create or update user in DynamoDB
        db_create_or_update_user_record(
            vibe_user_id,
            platform_user_id,
            dict(platform_metadata, **platform_user_data),
        )

        # Generate JWT token
        token = generate_jwt_token(signed_data={"uid": vibe_user_id})

        # Core settings
        core_settings = CoreSettings()

        # Generate profile IDs
        vibe_user_profile_ids = [
            hash_string_to_id(f"{vibe_user_id}:{profile_idx}")
            for profile_idx in range(0, core_settings.max_profile_count)
        ]

        return generate_response(
            200,
            {
                "token": token,
                "userId": vibe_user_id,
                "profileIds": vibe_user_profile_ids,
            },
        )

    except ResponseError as e:
        return e.to_dict()

    except Exception as e:
        raise ResponseError(500, {"error": f"Internal server error: {str(e)}"})
