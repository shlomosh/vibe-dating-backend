"""
Profiles Lambda Function

Handles all profile-related operations for authenticated users.
Supports GET, PUT, and DELETE operations for profile management.
"""

import base64
import json
from typing import Any, Dict

from core.auth_utils import extract_user_id_from_context, get_allocated_profile_ids
from core.profile_utils import delete_profile, get_profile, upsert_profile
from core.rest_utils import ResponseError, generate_response


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for all profile operations

    Args:
        event: Lambda event object
        context: Lambda context object

    Returns:
        Dict[str, Any]: API Gateway response
    """
    try:
        print(f"Event: {event}")

        # Extract user ID from JWT token context
        user_id = extract_user_id_from_context(event)

        # Get HTTP method and path parameters
        http_method = event.get("httpMethod", "")
        path_parameters = event.get("pathParameters", {}) or {}
        profile_id = path_parameters.get("profileId")

        # Validate profile ID if provided
        if profile_id:
            allocated_profile_ids = get_allocated_profile_ids(user_id)
            if profile_id not in allocated_profile_ids:
                raise ResponseError(403, {"error": "Profile ID not allocated to user"})

        # Route based on HTTP method
        if http_method == "GET":
            return handle_get_profile(user_id, profile_id)
        elif http_method == "PUT":
            return handle_upsert_profile(event, user_id, profile_id)
        elif http_method == "DELETE":
            return handle_delete_profile(user_id, profile_id)
        else:
            raise ResponseError(405, {"error": f"Method {http_method} not allowed"})

    except ResponseError as e:
        return e.to_dict()

    except Exception as e:
        print(f"Error: {str(e)}")
        return generate_response(500, {"error": f"Internal server error: {str(e)}"})


def handle_get_profile(user_id: str, profile_id: str) -> Dict[str, Any]:
    """
    Handle GET /profiles/{profileId}

    Args:
        user_id: The user ID
        profile_id: The profile ID

    Returns:
        Dict[str, Any]: API Gateway response
    """
    if not profile_id:
        raise ResponseError(400, {"error": "profileId path parameter is required"})

    # Get the profile
    profile = get_profile(profile_id)

    if not profile:
        raise ResponseError(404, {"error": "Profile not found"})

    return generate_response(200, {"profile": profile})


def handle_upsert_profile(
    event: Dict[str, Any], user_id: str, profile_id: str
) -> Dict[str, Any]:
    """
    Handle PUT /profiles/{profileId} - Create or update profile

    Args:
        event: Lambda event object
        user_id: The user ID
        profile_id: The profile ID

    Returns:
        Dict[str, Any]: API Gateway response
    """
    if not profile_id:
        raise ResponseError(400, {"error": "profileId path parameter is required"})

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
        raise ResponseError(400, {"error": f"Invalid JSON in request body: {str(e)}"})

    # Extract profile data
    profile_data = body.get("profileData", {})
    if not profile_data:
        raise ResponseError(400, {"error": "profileData is required"})

    # Upsert the profile (create if not exists, update if exists)
    result = upsert_profile(user_id, profile_id, profile_data)

    return generate_response(
        200,
        {
            "message": "Profile saved successfully",
            "profile": result["profile"],
            "created": result["created"],
        },
    )


def handle_delete_profile(user_id: str, profile_id: str) -> Dict[str, Any]:
    """
    Handle DELETE /profiles/{profileId}

    Args:
        user_id: The user ID
        profile_id: The profile ID

    Returns:
        Dict[str, Any]: API Gateway response
    """
    if not profile_id:
        raise ResponseError(400, {"error": "profileId path parameter is required"})

    # Delete the profile
    success = delete_profile(user_id, profile_id)

    if success:
        return generate_response(200, {"message": "Profile deleted successfully"})
    else:
        raise ResponseError(500, {"error": "Failed to delete profile"})
