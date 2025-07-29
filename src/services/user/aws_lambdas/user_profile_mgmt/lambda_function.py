"""
Profile Management Lambda Function

Handles all profile-related operations for authenticated users.
Supports GET, PUT, and DELETE operations for profile management.
"""

from typing import Any, Dict

from core.auth_utils import extract_user_id_from_context
from core.profile_utils import ProfileManager
from core.rest_utils import ResponseError, generate_response, parse_request_body


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
        import json

        print(f"User Profile Management Event: {json.dumps(event)}")

        # Extract user ID from JWT token context
        user_id = extract_user_id_from_context(event)
        profile_mgmt = ProfileManager(user_id)

        # Get HTTP method and path parameters
        http_method = event.get("httpMethod", "")
        path_parameters = event.get("pathParameters", {}) or {}

        # Validate profile ID
        profile_id = path_parameters.get("profileId")
        if not profile_mgmt.validate_profile_id(
            profile_id, is_existing=http_method in ["GET", "DELETE"]
        ):
            raise ResponseError(400, {"error": "Invalid profile ID"})

        # Route based on HTTP method
        if http_method == "PUT":
            profile_record = parse_request_body(event).get("profile", None)
            return handle_upsert_profile(
                profile_mgmt, profile_id, profile_record=profile_record
            )
        elif http_method == "GET":
            return handle_get_profile(profile_mgmt, profile_id)
        elif http_method == "DELETE":
            return handle_delete_profile(profile_mgmt, profile_id)
        else:
            raise ResponseError(405, {"error": f"Method {http_method} not allowed"})

    except ResponseError as e:
        return e.to_dict()

    except Exception as e:
        print(f"Error: {str(e)}")
        return generate_response(500, {"error": f"Internal server error: {str(e)}"})


def handle_get_profile(profile_mgmt: ProfileManager, profile_id: str) -> Dict[str, Any]:
    """
    Handle GET /profile/{profileId}

    Args:
        user_id: The user ID
        profile_id: The profile ID

    Returns:
        Dict[str, Any]: API Gateway response
    """
    if not profile_id:
        raise ResponseError(400, {"error": "profileId path parameter is required"})

    try:
        profile_record = profile_mgmt.get(profile_id)

        if not profile_record:
            raise ResponseError(404, {"error": "Profile record not found"})

        return generate_response(200, {"profile": profile_record})
    except ValueError as e:
        raise ResponseError(400, {"error": str(e)})
    except Exception as e:
        raise ResponseError(500, {"error": f"Failed to get profile: {str(e)}"})


def handle_upsert_profile(
    profile_mgmt: ProfileManager, profile_id: str, profile_record: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Handle PUT /profile/{profileId} - Create or update profile

    Args:
        user_id: The user ID
        profile_id: The profile ID
        profile_record: Profile record

    Returns:
        Dict[str, Any]: API Gateway response
    """
    if not profile_id:
        raise ResponseError(400, {"error": "profileId path parameter is required"})

    if not profile_record:
        raise ResponseError(400, {"error": "No profile record provided"})

    try:
        # Check if profile exists to determine if it's a create or update
        profile_exists = profile_id in profile_mgmt.active_profile_ids

        # Perform upsert operation
        success = profile_mgmt.upsert(profile_id, profile_record)

        if not success:
            raise ResponseError(500, {"error": "Failed to upsert profile"})

        # Get the updated profile data
        updated_profile = profile_mgmt.get(profile_id)

        message = "Profile created" if not profile_exists else "Profile updated"
        return generate_response(
            200,
            {
                "message": message,
                "profile": updated_profile,
                "created": not profile_exists,
            },
        )
    except ValueError as e:
        raise ResponseError(400, {"error": str(e)})
    except Exception as e:
        raise ResponseError(500, {"error": f"Failed to upsert profile: {str(e)}"})


def handle_delete_profile(
    profile_mgmt: ProfileManager, profile_id: str
) -> Dict[str, Any]:
    """
    Handle DELETE /profile/{profileId}

    Args:
        user_id: The user ID
        profile_id: The profile ID

    Returns:
        Dict[str, Any]: API Gateway response
    """
    if not profile_id:
        raise ResponseError(400, {"error": "profileId path parameter is required"})

    try:
        success = profile_mgmt.delete(profile_id)

        if success:
            return generate_response(200, {"message": "Profile deleted"})
        else:
            raise ResponseError(500, {"error": "Failed to delete profile"})
    except ValueError as e:
        raise ResponseError(400, {"error": str(e)})
    except Exception as e:
        raise ResponseError(500, {"error": f"Failed to delete profile: {str(e)}"})
