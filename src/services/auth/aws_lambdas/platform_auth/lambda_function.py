"""
Vibe Platform Authentication Lambda Function

This function handles platform authentication and user creation.
"""

import sys
import os

# Add parent directory to path to import shared utilities
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from typing import Dict, Any

from core.auth_utils import hash_string_to_id, generate_jwt_token
from core.rest_utils import ResponseError, generate_response
from core.dynamo_utils import db_create_or_update_user_record

    
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
        # Parse request body
        body = json.loads(event["body"])
        platform = body.get("platform")
        platform_token = body.get("platformToken")
        platform_metadata = body.get("platformMetadata", {})

        if not platform or not platform_token:
            raise ResponseError(400, {"error": "Missing required fields"})

        if platform == "telegram":
            from .telegram import authenticate_user
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
        db_create_or_update_user_record(vibe_user_id, platform_user_id, dict(platform_metadata, **platform_user_data))

        # Generate JWT token
        token = generate_jwt_token(signed_data={ "uid": vibe_user_id })

        return generate_response(200, {
            "token": token,
            "userId": vibe_user_id,
            "userData": platform_user_data,
        })

    except ResponseError as e:
        return e.to_dict()

    except Exception as e:
        raise ResponseError(500, {"error": f"Internal server error: {str(e)}"})
