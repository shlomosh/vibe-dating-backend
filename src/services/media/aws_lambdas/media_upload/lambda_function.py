"""
Media Upload Lambda Function

Handles media upload requests, generates presigned URLs, and manages upload completion.
Supports profile image uploads with validation and processing pipeline integration.
"""

import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

from core.auth_utils import extract_user_id_from_context
from core.aws import DynamoDBService
from core.profile_utils import ProfileManager
from core.rest_utils import ResponseError, generate_response, parse_request_body


class MediaUploadHandler:
    """Handles media upload operations"""

    def __init__(self):
        self.s3_client = boto3.client("s3")
        self.table = DynamoDBService.get_table()
        self.media_bucket = os.environ.get("MEDIA_S3_BUCKET")
        self.cloudfront_domain = os.environ.get("CLOUDFRONT_DOMAIN")

        # Configuration
        self.max_file_size = int(os.environ.get("MAX_FILE_SIZE", "10485760"))  # 10MB
        self.max_images_per_profile = int(os.environ.get("MAX_IMAGES_PER_PROFILE", "5"))
        self.allowed_formats = ["jpeg", "jpg", "png", "webp"]
        self.upload_expiry_hours = 1

    def generate_media_id(self) -> str:
        """Generate unique media ID"""
        return str(uuid.uuid4()).replace("-", "")[:16]

    def validate_upload_request(self, request_data: dict) -> bool:
        """Validate upload request data"""
        required_fields = ["type", "aspectRatio", "metadata"]

        # Check required fields
        for field in required_fields:
            if field not in request_data:
                raise ResponseError(400, {"error": f"Missing required field: {field}"})

        # Validate image type
        if request_data["type"] != "image":
            raise ResponseError(400, {"error": "Only image type supported"})

        # Validate aspect ratio
        if request_data["aspectRatio"] != "3:4":
            raise ResponseError(400, {"error": "Only 3:4 aspect ratio supported"})

        # Validate metadata
        metadata = request_data["metadata"]
        if metadata["size"] > self.max_file_size:
            raise ResponseError(
                400, {"error": f"File size exceeds limit: {self.max_file_size}"}
            )

        if metadata["format"].lower() not in self.allowed_formats:
            raise ResponseError(
                400, {"error": f"Unsupported format: {metadata['format']}"}
            )

        return True

    def check_profile_ownership(self, user_id: str, profile_id: str) -> bool:
        """Verify user owns the profile"""
        profile_mgmt = ProfileManager(user_id)
        return profile_mgmt.validate_profile_id(profile_id, is_existing=True)

    def check_image_limit(self, profile_id: str) -> bool:
        """Check if profile has reached image limit"""
        try:
            response = self.table.query(
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
                ExpressionAttributeValues={
                    ":pk": f"PROFILE#{profile_id}",
                    ":sk_prefix": "MEDIA#",
                },
                ProjectionExpression="mediaId",
            )
            current_count = len(response.get("Items", []))
            return current_count < self.max_images_per_profile
        except ClientError as e:
            print(f"Error checking image limit: {e}")
            return False

    def generate_presigned_upload_url(self, media_id: str, content_type: str) -> dict:
        """Generate secure presigned upload URL"""
        s3_key = f"uploads/profile-images/{media_id}.{content_type.split('/')[-1]}"

        try:
            presigned_url = self.s3_client.generate_presigned_post(
                Bucket=self.media_bucket,
                Key=s3_key,
                Fields={"Content-Type": content_type},
                Conditions=[
                    {"Content-Type": content_type},
                    ["content-length-range", 1024, self.max_file_size],
                ],
                ExpiresIn=self.upload_expiry_hours * 3600,  # Convert to seconds
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

    def store_pending_upload(
        self,
        media_id: str,
        profile_id: str,
        user_id: str,
        upload_data: dict,
        request_data: dict,
    ) -> None:
        """Store pending upload record in DynamoDB"""
        expires_at = datetime.utcnow() + timedelta(hours=self.upload_expiry_hours)

        pending_record = {
            "PK": f"UPLOAD#{media_id}",
            "SK": "PENDING",
            "mediaId": media_id,
            "profileId": profile_id,
            "userId": user_id,
            "status": "pending",
            "uploadUrl": upload_data["uploadUrl"],
            "s3Key": upload_data["s3Key"],
            "metadata": request_data["metadata"],
            "order": request_data.get("order", 1),
            "expiresAt": expires_at.isoformat(),
            "createdAt": datetime.utcnow().isoformat(),
            "TTL": int(expires_at.timestamp()),
        }

        try:
            self.table.put_item(Item=pending_record)
        except ClientError as e:
            raise ResponseError(
                500, {"error": f"Failed to store pending upload: {str(e)}"}
            )

    def request_upload_url(
        self, profile_id: str, user_id: str, request_data: dict
    ) -> dict:
        """Handle upload URL request"""
        # Validate request
        self.validate_upload_request(request_data)

        # Check profile ownership
        if not self.check_profile_ownership(user_id, profile_id):
            raise ResponseError(
                403, {"error": "Access denied: Profile not owned by user"}
            )

        # Check image limit
        if not self.check_image_limit(profile_id):
            raise ResponseError(
                400,
                {
                    "error": f"Profile has reached maximum image limit: {self.max_images_per_profile}"
                },
            )

        # Generate media ID
        media_id = self.generate_media_id()

        # Generate presigned upload URL
        content_type = f"image/{request_data['metadata']['format']}"
        upload_data = self.generate_presigned_upload_url(media_id, content_type)

        # Store pending upload record
        self.store_pending_upload(
            media_id, profile_id, user_id, upload_data, request_data
        )

        # Return response
        expires_at = datetime.utcnow() + timedelta(hours=self.upload_expiry_hours)
        return {
            "mediaId": media_id,
            "uploadUrl": upload_data["uploadUrl"],
            "uploadMethod": upload_data["uploadMethod"],
            "uploadHeaders": upload_data["uploadHeaders"],
            "expiresAt": expires_at.isoformat(),
        }

    def complete_upload(
        self, profile_id: str, media_id: str, user_id: str, completion_data: dict
    ) -> dict:
        """Handle upload completion"""
        # Validate completion data
        if not completion_data.get("uploadSuccess"):
            raise ResponseError(400, {"error": "Upload was not successful"})

        # Get pending upload record
        try:
            response = self.table.get_item(
                Key={"PK": f"UPLOAD#{media_id}", "SK": "PENDING"}
            )
            pending_record = response.get("Item")

            if not pending_record:
                raise ResponseError(404, {"error": "Pending upload not found"})

            if (
                pending_record["userId"] != user_id
                or pending_record["profileId"] != profile_id
            ):
                raise ResponseError(403, {"error": "Access denied"})

        except ClientError as e:
            raise ResponseError(
                500, {"error": f"Failed to retrieve pending upload: {str(e)}"}
            )

        # Update status to processing
        try:
            self.table.update_item(
                Key={"PK": f"PROFILE#{profile_id}", "SK": f"MEDIA#{media_id}"},
                UpdateExpression="SET #status = :status, uploadedAt = :uploadedAt, updatedAt = :updatedAt",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":status": "processing",
                    ":uploadedAt": datetime.utcnow().isoformat(),
                    ":updatedAt": datetime.utcnow().isoformat(),
                },
            )
        except ClientError as e:
            raise ResponseError(
                500, {"error": f"Failed to update media status: {str(e)}"}
            )

        # Delete pending upload record
        try:
            self.table.delete_item(Key={"PK": f"UPLOAD#{media_id}", "SK": "PENDING"})
        except ClientError as e:
            print(f"Warning: Failed to delete pending upload record: {e}")

        return {
            "mediaId": media_id,
            "status": "processing",
            "estimatedProcessingTime": 30,
        }


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
        handler = MediaUploadHandler()

        # Get HTTP method and path parameters
        http_method = event.get("httpMethod", "")
        path_parameters = event.get("pathParameters", {}) or {}

        # Validate profile ID
        profile_id = path_parameters.get("profileId")
        if not profile_id:
            raise ResponseError(400, {"error": "profileId path parameter is required"})

        # Route based on HTTP method and path
        if http_method == "POST":
            request_body = parse_request_body(event)

            # Check if this is a complete upload request
            if "mediaId" in path_parameters:
                media_id = path_parameters.get("mediaId")
                if not media_id:
                    raise ResponseError(
                        400, {"error": "mediaId path parameter is required"}
                    )

                return generate_response(
                    200,
                    handler.complete_upload(
                        profile_id, media_id, user_id, request_body
                    ),
                )
            else:
                # Request upload URL
                return generate_response(
                    200, handler.request_upload_url(profile_id, user_id, request_body)
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
        "httpMethod": "POST",
        "pathParameters": {"profileId": "test123"},
        "body": json.dumps(
            {
                "type": "image",
                "aspectRatio": "3:4",
                "metadata": {
                    "width": 1440,
                    "height": 1920,
                    "size": 2048576,
                    "format": "jpeg",
                },
                "order": 1,
            }
        ),
    }

    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
