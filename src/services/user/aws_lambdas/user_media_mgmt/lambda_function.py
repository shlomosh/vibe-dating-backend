import base64
import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError
from core_types.media import MediaStatus

from core.auth_utils import extract_user_id_from_context
from core.aws import DynamoDBService
from core.media_utils import MediaManager
from core.profile_utils import ProfileManager
from core.rest_utils import ResponseError, generate_response, parse_request_body
from core.settings import CoreSettings


class UserMediaMgmtHandler:
    """Handles user media management operations"""

    def __init__(self, user_id: str, profile_id: str):
        self.user_id = user_id
        self.profile_id = profile_id
        s3_region = os.environ.get("MEDIA_S3_REGION")
        self.s3_client = boto3.client(
            "s3",
            region_name=s3_region,
            endpoint_url=f"https://s3.{s3_region}.amazonaws.com",
        )
        self.media_bucket = os.environ.get("MEDIA_S3_BUCKET")
        self.media_mgmt = MediaManager(user_id, profile_id)
        self.core_settings = CoreSettings()

    def _decode_media_blob(self, media_blob_b64: str) -> Dict[str, Any]:
        """Decode base64 mediaBlob with error handling"""
        try:
            media_meta_json = base64.b64decode(media_blob_b64).decode("utf-8")
            return json.loads(media_meta_json)
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ResponseError(400, {"error": f"Invalid mediaBlob format: {str(e)}"})

    def _validate_file_size(self, size: int) -> None:
        """Validate file size against limits"""
        if size > self.core_settings.media_max_file_size:
            raise ResponseError(
                400,
                {
                    "error": f"File size exceeds limit: {self.core_settings.media_max_file_size}"
                },
            )

    def _validate_file_format(self, format_str: str) -> None:
        """Validate file format against allowed formats"""
        file_format = format_str.lower()
        if file_format not in self.core_settings.media_allowed_formats:
            raise ResponseError(400, {"error": f"Unsupported format: {file_format}"})

    def validate_upload_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate upload request data and decode mediaBlob"""
        required_fields = ["mediaType", "mediaBlob", "mediaSize"]

        # Check required fields
        for field in required_fields:
            if field not in request_data:
                raise ResponseError(400, {"error": f"Missing required field: {field}"})

        media_type = request_data["mediaType"]
        media_class, media_format = media_type.split("/")
        media_size = request_data["mediaSize"]

        # Validate media type
        if media_class != "image":
            raise ResponseError(400, {"error": "Only image media class supported"})

        # Decode and validate mediaBlob
        media_blob = self._decode_media_blob(request_data["mediaBlob"])

        # Validate file size and format
        self._validate_file_size(media_size)
        self._validate_file_format(media_format)

        return media_type, media_blob, media_size

    def generate_presigned_upload_url(
        self, media_id: str, content_type: str
    ) -> Dict[str, Any]:
        """Generate secure presigned upload URL"""
        date = datetime.utcnow().strftime("%Y%m%d")
        s3_key = f"uploads/{date}/{self.user_id}/{self.profile_id}/{media_id}.{content_type.split('/')[-1]}"

        try:
            presigned_url = self.s3_client.generate_presigned_post(
                Bucket=self.media_bucket,
                Key=s3_key,
                Fields={"Content-Type": content_type},
                Conditions=[
                    {"Content-Type": content_type},
                    [
                        "content-length-range",
                        1024,
                        self.core_settings.media_max_file_size,
                    ],
                ],
                ExpiresIn=self.core_settings.media_upload_expiry_hours * 3600,
            )

            return {
                "uploadUrl": presigned_url["url"],
                "uploadMethod": "POST",
                "uploadHeaders": presigned_url["fields"],
                "s3Key": s3_key,
            }
        except ClientError as e:
            raise ResponseError(
                500, {"error": f"Failed to generate upload URL: {str(e)}"}
            )

    def request_upload(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle upload URL request"""
        # Validate request and decode mediaBlob
        media_type, media_blob, media_size = self.validate_upload_request(request_data)

        # Get available pre-allocated media ID
        media_id = self.media_mgmt.get_available_media_id()
        if not media_id:
            raise ResponseError(
                400, {"error": "No available media slots for this profile"}
            )

        # Generate presigned upload URL
        upload_data = self.generate_presigned_upload_url(media_id, media_type)
        upload_s3_key = upload_data["s3Key"]

        # Create media record and store pending upload with mediaSize
        self.media_mgmt.upsert_media_record(
            media_id,
            upload_s3_key,
            media_blob,
            media_type,
            size=media_size,
            dimensions=media_blob.get("dimensions", None),
            duration=media_blob.get("duration", None),
            error_msg=media_blob.get("error_msg", None),
            status=MediaStatus.PENDING,
        )

        # Return response with expiration
        expires_at = datetime.utcnow() + timedelta(
            hours=self.core_settings.media_upload_expiry_hours
        )

        return {
            "mediaId": media_id,
            "uploadUrl": upload_data["uploadUrl"],
            "uploadMethod": upload_data["uploadMethod"],
            "uploadHeaders": upload_data["uploadHeaders"],
            "expiresAt": expires_at.isoformat(),
        }

    def _get_and_validate_media_item(self, media_id: str) -> Dict[str, Any]:
        """Get media item and validate it's in PENDING status"""
        try:
            media_item = self.media_mgmt.get_media_record(media_id)
            if not media_item:
                raise ResponseError(404, {"error": "Media item not found"})

            if media_item.get("status") != MediaStatus.PENDING.value:
                raise ResponseError(
                    400, {"error": "Media item is not in PENDING status"}
                )

            return media_item

        except ValueError as e:
            raise ResponseError(404, {"error": f"Media item not found: {str(e)}"})
        except Exception as e:
            raise ResponseError(
                500, {"error": f"Failed to retrieve media item: {str(e)}"}
            )

    def complete_upload(
        self, media_id: str, request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle upload completion"""
        # Validate completion data
        if not request_data.get("uploadSuccess"):
            raise ResponseError(400, {"error": "Upload was not successful"})

        # Validate media ID is allocated for this profile
        if not self.media_mgmt.validate_media_id(media_id, is_existing=True):
            raise ResponseError(
                400, {"error": "Media ID is not allocated for this profile"}
            )

        # Get and validate media item
        media_item = self._get_and_validate_media_item(media_id)

        # Update media status to processing and activate media ID
        try:
            self.media_mgmt.update_media_status(
                media_id,
                MediaStatus.PROCESSING,
                uploadedAt=datetime.utcnow().isoformat(),
            )

            # Activate the media ID
            self.media_mgmt.activate_media_id(media_id)

        except Exception as e:
            raise ResponseError(
                500, {"error": f"Failed to update media status: {str(e)}"}
            )

        return {
            "mediaId": media_id,
            "status": MediaStatus.PROCESSING.value,
            "estimatedProcessingTime": 30,
        }

    def delete_media(self, media_id: str) -> dict:
        """Delete media file and record"""
        # Check profile ownership
        profile_mgmt = ProfileManager(self.user_id)
        if not profile_mgmt.validate_profile_id(self.profile_id, is_existing=True):
            raise ResponseError(
                403, {"error": "Access denied: Profile not owned by user"}
            )

        try:
            # Get media record first using MediaManager
            media_record = self.media_mgmt.get_media_record(media_id)
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

            # Delete from DynamoDB using MediaManager
            self.media_mgmt.delete_media_record(media_id)

            return {
                "mediaId": media_id,
                "deleted": True,
                "deletedAt": datetime.utcnow().isoformat(),
            }

        except (ClientError, ValueError) as e:
            raise ResponseError(500, {"error": f"Failed to delete media: {str(e)}"})

    def reorder_media(self, order_data: dict) -> dict:
        """Reorder profile media"""
        # Check profile ownership
        profile_mgmt = ProfileManager(self.user_id)
        if not profile_mgmt.validate_profile_id(self.profile_id, is_existing=True):
            raise ResponseError(
                403, {"error": "Access denied: Profile not owned by user"}
            )

        sorted_media_ids = order_data.get("sortedMediaIds", [])
        if not sorted_media_ids:
            raise ResponseError(400, {"error": "sortedMediaIds array is required"})

        try:
            # Get the profile record to access activeMediaIds
            profile_record = profile_mgmt.profiles_data.get(self.profile_id)
            if not profile_record:
                raise ResponseError(404, {"error": "Profile not found"})

            current_active_media_ids = profile_record.get("activeMediaIds", [])

            # Validate that sorted_media_ids and current_active_media_ids contain the same items
            if set(sorted_media_ids) != set(current_active_media_ids):
                raise ResponseError(
                    400,
                    {
                        "error": "sortedMediaIds must contain the same items as current activeMediaIds, just in different order"
                    },
                )

            # Update the profile item with the new activeMediaIds order using MediaManager's table access
            table = self.media_mgmt.table
            table.update_item(
                Key={"PK": f"PROFILE#{self.profile_id}", "SK": "METADATA"},
                UpdateExpression="SET activeMediaIds = :active_media_ids, updatedAt = :updated_at",
                ExpressionAttributeValues={
                    ":active_media_ids": sorted_media_ids,
                    ":updated_at": datetime.utcnow().isoformat(),
                },
            )

            return {
                "profileId": self.profile_id,
                "activeMediaIds": sorted_media_ids,
                "updatedAt": datetime.utcnow().isoformat(),
            }

        except ClientError as e:
            raise ResponseError(500, {"error": f"Failed to reorder media: {str(e)}"})


def _validate_path_parameters(
    path_parameters: Dict[str, Any], required_params: list
) -> None:
    """Validate required path parameters"""
    for param in required_params:
        if not path_parameters.get(param):
            raise ResponseError(400, {"error": f"{param} path parameter is required"})


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for media upload operations

    Args:
        event: Lambda event object
        context: Lambda context object

    Returns:
        Dict[str, Any]: API Gateway response
    """
    try:
        print(f"Media Upload Event: {json.dumps(event)}")

        # Extract user ID from JWT token context
        user_id = extract_user_id_from_context(event)

        # Get HTTP method and path parameters
        http_method = event.get("httpMethod", "")
        path_parameters = event.get("pathParameters", {}) or {}

        # Validate required path parameters
        _validate_path_parameters(path_parameters, ["profileId"])
        profile_id = path_parameters["profileId"]

        # Create media upload handler
        handler = UserMediaMgmtHandler(user_id, profile_id)

        # Route based on HTTP method
        if http_method == "POST":
            request_data = parse_request_body(event)

            # Check if this is a complete upload request
            if "mediaId" in path_parameters:
                _validate_path_parameters(path_parameters, ["mediaId"])
                media_id = path_parameters["mediaId"]

                return generate_response(
                    200,
                    handler.complete_upload(media_id, request_data),
                )
            else:
                # Request upload URL
                return generate_response(200, handler.request_upload(request_data))
        elif http_method == "DELETE":
            # Delete media
            media_id = path_parameters.get("mediaId")
            if not media_id:
                raise ResponseError(
                    400, {"error": "mediaId path parameter is required"}
                )

            return generate_response(200, handler.delete_media(media_id))
        elif http_method == "PUT":
            # Reorder media
            request_body = parse_request_body(event)
            return generate_response(200, handler.reorder_media(request_body))
        else:
            raise ResponseError(405, {"error": f"Method {http_method} not allowed"})

    except ResponseError as e:
        return e.to_dict()

    except Exception as e:
        print(f"Error: {str(e)}")
        return generate_response(500, {"error": f"Internal server error: {str(e)}"})
