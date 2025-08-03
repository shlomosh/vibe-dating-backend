"""
Media Management Lambda Function

Handles media status checking, deletion, and reordering operations.
Provides CRUD operations for profile media management.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

from core.auth_utils import extract_user_id_from_context
from core.aws import DynamoDBService
from core.profile_utils import ProfileManager
from core.rest_utils import ResponseError, generate_response, parse_request_body


class MediaManager:
    """Handles media management operations"""

    def __init__(self):
        self.s3_client = boto3.client("s3")
        self.table = DynamoDBService.get_table()
        self.media_bucket = os.environ.get("MEDIA_S3_BUCKET")

    def check_profile_ownership(self, user_id: str, profile_id: str) -> bool:
        """Verify user owns the profile"""
        profile_mgmt = ProfileManager(user_id)
        return profile_mgmt.validate_profile_id(profile_id, is_existing=True)

    def get_media_status(self, profile_id: str, media_id: str, user_id: str) -> dict:
        """Get media processing status"""
        # Check profile ownership
        if not self.check_profile_ownership(user_id, profile_id):
            raise ResponseError(
                403, {"error": "Access denied: Profile not owned by user"}
            )

        try:
            response = self.table.get_item(
                Key={"PK": f"PROFILE#{profile_id}", "SK": f"MEDIA#{media_id}"}
            )

            media_record = response.get("Item")
            if not media_record:
                raise ResponseError(404, {"error": "Media record not found"})

            return {
                "mediaId": media_id,
                "status": media_record.get("status", "unknown"),
                "urls": {
                    "original": media_record.get("originalUrl"),
                    "thumbnail": media_record.get("thumbnailUrl"),
                },
                "processedAt": media_record.get("processedAt"),
                "metadata": media_record.get("metadata", {}),
            }

        except ClientError as e:
            raise ResponseError(500, {"error": f"Failed to get media status: {str(e)}"})

    def delete_media(self, profile_id: str, media_id: str, user_id: str) -> dict:
        """Delete media file and record"""
        # Check profile ownership
        if not self.check_profile_ownership(user_id, profile_id):
            raise ResponseError(
                403, {"error": "Access denied: Profile not owned by user"}
            )

        try:
            # Get media record first
            response = self.table.get_item(
                Key={"PK": f"PROFILE#{profile_id}", "SK": f"MEDIA#{media_id}"}
            )

            media_record = response.get("Item")
            if not media_record:
                raise ResponseError(404, {"error": "Media record not found"})

            # Delete files from S3
            s3_keys_to_delete = []

            # Original file
            if media_record.get("s3Key"):
                s3_keys_to_delete.append(media_record["s3Key"])

            # Thumbnail file
            thumbnail_key = f"thumb/{media_id}.jpg"
            s3_keys_to_delete.append(thumbnail_key)

            # Upload file (if still exists)
            upload_key = f"uploads/profile-images/{media_id}.jpg"
            s3_keys_to_delete.append(upload_key)

            # Delete from S3
            if s3_keys_to_delete:
                try:
                    self.s3_client.delete_objects(
                        Bucket=self.media_bucket,
                        Delete={
                            "Objects": [{"Key": key} for key in s3_keys_to_delete],
                            "Quiet": True,
                        },
                    )
                except ClientError as e:
                    print(f"Warning: Failed to delete some S3 objects: {e}")

            # Delete from DynamoDB
            self.table.delete_item(
                Key={"PK": f"PROFILE#{profile_id}", "SK": f"MEDIA#{media_id}"}
            )

            return {
                "mediaId": media_id,
                "deleted": True,
                "deletedAt": datetime.utcnow().isoformat(),
            }

        except ClientError as e:
            raise ResponseError(500, {"error": f"Failed to delete media: {str(e)}"})

    def reorder_media(self, profile_id: str, user_id: str, order_data: dict) -> dict:
        """Reorder profile media"""
        # Check profile ownership
        if not self.check_profile_ownership(user_id, profile_id):
            raise ResponseError(
                403, {"error": "Access denied: Profile not owned by user"}
            )

        image_order = order_data.get("imageOrder", [])
        if not image_order:
            raise ResponseError(400, {"error": "imageOrder array is required"})

        try:
            # Get all media for this profile
            response = self.table.query(
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
                ExpressionAttributeValues={
                    ":pk": f"PROFILE#{profile_id}",
                    ":sk_prefix": "MEDIA#",
                },
            )

            existing_media = response.get("Items", [])
            existing_media_ids = {item.get("mediaId") for item in existing_media}

            # Validate that all ordered IDs exist
            for media_id in image_order:
                if media_id not in existing_media_ids:
                    raise ResponseError(
                        400, {"error": f"Media ID not found: {media_id}"}
                    )

            # Update order for each media item
            for order_index, media_id in enumerate(image_order, 1):
                self.table.update_item(
                    Key={"PK": f"PROFILE#{profile_id}", "SK": f"MEDIA#{media_id}"},
                    UpdateExpression="SET #order = :order, updatedAt = :updatedAt",
                    ExpressionAttributeNames={"#order": "order"},
                    ExpressionAttributeValues={
                        ":order": order_index,
                        ":updatedAt": datetime.utcnow().isoformat(),
                    },
                )

            return {
                "profileId": profile_id,
                "imageOrder": image_order,
                "updatedAt": datetime.utcnow().isoformat(),
            }

        except ClientError as e:
            raise ResponseError(500, {"error": f"Failed to reorder media: {str(e)}"})

    def list_profile_media(self, profile_id: str, user_id: str) -> dict:
        """List all media for a profile"""
        # Check profile ownership
        if not self.check_profile_ownership(user_id, profile_id):
            raise ResponseError(
                403, {"error": "Access denied: Profile not owned by user"}
            )

        try:
            response = self.table.query(
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
                ExpressionAttributeValues={
                    ":pk": f"PROFILE#{profile_id}",
                    ":sk_prefix": "MEDIA#",
                },
            )

            media_items = response.get("Items", [])

            # Sort by order
            media_items.sort(key=lambda x: x.get("order", 0))

            return {
                "profileId": profile_id,
                "media": [
                    {
                        "mediaId": item.get("mediaId"),
                        "status": item.get("status"),
                        "order": item.get("order"),
                        "urls": {
                            "original": item.get("originalUrl"),
                            "thumbnail": item.get("thumbnailUrl"),
                        },
                        "metadata": item.get("metadata", {}),
                        "uploadedAt": item.get("uploadedAt"),
                        "processedAt": item.get("processedAt"),
                    }
                    for item in media_items
                ],
            }

        except ClientError as e:
            raise ResponseError(
                500, {"error": f"Failed to list profile media: {str(e)}"}
            )


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for media management operations

    Args:
        event: Lambda event object
        context: Lambda context object

    Returns:
        Dict[str, Any]: API Gateway response
    """
    try:
        print(f"Media Management Event: {json.dumps(event)}")

        # Extract user ID from JWT token context
        user_id = extract_user_id_from_context(event)
        manager = MediaManager()

        # Get HTTP method and path parameters
        http_method = event.get("httpMethod", "")
        path_parameters = event.get("pathParameters", {}) or {}

        # Validate profile ID
        profile_id = path_parameters.get("profileId")
        if not profile_id:
            raise ResponseError(400, {"error": "profileId path parameter is required"})

        # Route based on HTTP method and path
        if http_method == "GET":
            if "mediaId" in path_parameters:
                # Get media status
                media_id = path_parameters.get("mediaId")
                if not media_id:
                    raise ResponseError(
                        400, {"error": "mediaId path parameter is required"}
                    )

                return generate_response(
                    200, manager.get_media_status(profile_id, media_id, user_id)
                )
            else:
                # List profile media
                return generate_response(
                    200, manager.list_profile_media(profile_id, user_id)
                )

        elif http_method == "DELETE":
            # Delete media
            media_id = path_parameters.get("mediaId")
            if not media_id:
                raise ResponseError(
                    400, {"error": "mediaId path parameter is required"}
                )

            return generate_response(
                200, manager.delete_media(profile_id, media_id, user_id)
            )

        elif http_method == "PUT":
            # Reorder media
            request_body = parse_request_body(event)
            return generate_response(
                200, manager.reorder_media(profile_id, user_id, request_body)
            )

        else:
            raise ResponseError(405, {"error": f"Method {http_method} not allowed"})

    except ResponseError as e:
        return e.to_dict()

    except Exception as e:
        print(f"Error: {str(e)}")
        return generate_response(500, {"error": f"Internal server error: {str(e)}"})


if __name__ == "__main__":
    # Test handler
    test_event = {
        "httpMethod": "GET",
        "pathParameters": {"profileId": "test123", "mediaId": "test456"},
        "body": None,
    }

    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
