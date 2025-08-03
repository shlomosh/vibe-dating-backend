"""
Media Processing Lambda Function

Handles S3 event notifications for uploaded media files.
Processes images to generate thumbnails, optimize files, and update metadata.
"""

import io
import json
import os
from datetime import datetime
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError
from PIL import Image

from core.aws import DynamoDBService


class MediaProcessor:
    """Handles media processing operations"""

    def __init__(self):
        self.s3_client = boto3.client("s3")
        self.cloudfront_client = boto3.client("cloudfront")
        self.table = DynamoDBService.get_table()
        self.media_bucket = os.environ.get("MEDIA_S3_BUCKET")
        self.cloudfront_domain = os.environ.get("CLOUDFRONT_DOMAIN")
        self.cloudfront_distribution_id = os.environ.get("CLOUDFRONT_DISTRIBUTION_ID")

        # Configuration
        self.thumbnail_width = 300
        self.thumbnail_height = 400
        self.thumbnail_quality = 85
        self.max_original_size = 1920  # Max width/height for original

    def extract_media_id_from_s3_key(self, s3_key: str) -> str:
        """Extract media ID from S3 key"""
        # Expected format: uploads/profile-images/{media_id}.{extension}
        parts = s3_key.split("/")
        if len(parts) >= 3:
            filename = parts[-1]
            return filename.split(".")[0]
        raise ValueError(f"Invalid S3 key format: {s3_key}")

    def get_media_record(self, media_id: str) -> Dict[str, Any]:
        """Get media record from DynamoDB"""
        try:
            # Query for media record
            response = self.table.query(
                IndexName="GSI5",  # Media Management GSI
                KeyConditionExpression="GSI5PK = :pk",
                ExpressionAttributeValues={":pk": f"MEDIA#{media_id}"},
            )

            items = response.get("Items", [])
            if not items:
                raise ValueError(f"Media record not found for ID: {media_id}")

            return items[0]
        except ClientError as e:
            raise RuntimeError(f"Failed to get media record: {str(e)}")

    def download_image_from_s3(self, s3_key: str) -> Image.Image:
        """Download image from S3"""
        try:
            response = self.s3_client.get_object(Bucket=self.media_bucket, Key=s3_key)
            image_data = response["Body"].read()
            return Image.open(io.BytesIO(image_data))
        except ClientError as e:
            raise RuntimeError(f"Failed to download image from S3: {str(e)}")

    def validate_image(self, image: Image.Image) -> None:
        """Validate image format and dimensions"""
        if image.format not in ["JPEG", "PNG", "WEBP"]:
            raise ValueError(f"Unsupported image format: {image.format}")

        if image.size[0] < 100 or image.size[1] < 100:
            raise ValueError("Image dimensions too small")

        if image.size[0] > 4000 or image.size[1] > 4000:
            raise ValueError("Image dimensions too large")

    def generate_thumbnail(self, image: Image.Image) -> Image.Image:
        """Generate thumbnail maintaining aspect ratio"""
        # Calculate aspect ratio
        aspect_ratio = image.size[0] / image.size[1]

        # Calculate thumbnail dimensions maintaining aspect ratio
        if aspect_ratio > (self.thumbnail_width / self.thumbnail_height):
            # Image is wider than target aspect ratio
            new_width = self.thumbnail_width
            new_height = int(self.thumbnail_width / aspect_ratio)
        else:
            # Image is taller than target aspect ratio
            new_height = self.thumbnail_height
            new_width = int(self.thumbnail_height * aspect_ratio)

        # Resize image
        thumbnail = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Create new image with target dimensions and paste thumbnail
        result = Image.new(
            "RGB", (self.thumbnail_width, self.thumbnail_height), (255, 255, 255)
        )

        # Calculate centering offset
        x_offset = (self.thumbnail_width - new_width) // 2
        y_offset = (self.thumbnail_height - new_height) // 2

        result.paste(thumbnail, (x_offset, y_offset))
        return result

    def optimize_image(self, image: Image.Image, max_size: int = None) -> Image.Image:
        """Optimize image size and quality"""
        if max_size and (image.size[0] > max_size or image.size[1] > max_size):
            # Calculate new dimensions maintaining aspect ratio
            aspect_ratio = image.size[0] / image.size[1]
            if aspect_ratio > 1:
                new_width = max_size
                new_height = int(max_size / aspect_ratio)
            else:
                new_height = max_size
                new_width = int(max_size * aspect_ratio)

            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        return image

    def upload_image_to_s3(
        self, image: Image.Image, s3_key: str, format: str = "JPEG", quality: int = 85
    ) -> str:
        """Upload image to S3 and return URL"""
        try:
            # Convert image to bytes
            buffer = io.BytesIO()
            if format.upper() == "JPEG":
                image = image.convert("RGB")

            image.save(buffer, format=format, quality=quality, optimize=True)
            buffer.seek(0)

            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.media_bucket,
                Key=s3_key,
                Body=buffer.getvalue(),
                ContentType=f"image/{format.lower()}",
                CacheControl="public, max-age=31536000",  # 1 year cache
            )

            # Return CloudFront URL
            return f"https://{self.cloudfront_domain}/{s3_key}"

        except ClientError as e:
            raise RuntimeError(f"Failed to upload image to S3: {str(e)}")

    def invalidate_cloudfront_cache(self, paths: list) -> None:
        """Invalidate CloudFront cache for specified paths"""
        if not self.cloudfront_distribution_id:
            print(
                "Warning: CloudFront distribution ID not configured, skipping cache invalidation"
            )
            return

        try:
            self.cloudfront_client.create_invalidation(
                DistributionId=self.cloudfront_distribution_id,
                InvalidationBatch={
                    "Paths": {"Quantity": len(paths), "Items": paths},
                    "CallerReference": f"media-processing-{datetime.utcnow().isoformat()}",
                },
            )
            print(f"CloudFront cache invalidation created for paths: {paths}")
        except ClientError as e:
            print(f"Warning: Failed to invalidate CloudFront cache: {e}")

    def update_media_record(
        self, media_id: str, profile_id: str, update_data: dict
    ) -> None:
        """Update media record in DynamoDB"""
        try:
            update_expression = "SET "
            expression_attrs = {}
            expression_attr_names = {}

            for key, value in update_data.items():
                update_expression += f"#{key} = :{key}, "
                expression_attrs[f":{key}"] = value
                expression_attr_names[f"#{key}"] = key

            update_expression = update_expression.rstrip(", ")

            self.table.update_item(
                Key={"PK": f"PROFILE#{profile_id}", "SK": f"MEDIA#{media_id}"},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attrs,
                ExpressionAttributeNames=expression_attr_names,
            )
        except ClientError as e:
            raise RuntimeError(f"Failed to update media record: {str(e)}")

    def process_profile_image(self, s3_key: str) -> None:
        """Process uploaded profile image"""
        try:
            # Extract media ID from S3 key
            media_id = self.extract_media_id_from_s3_key(s3_key)
            print(f"Processing media ID: {media_id}")

            # Get media record
            media_record = self.get_media_record(media_id)
            profile_id = media_record.get("profileId")

            if not profile_id:
                raise ValueError("Profile ID not found in media record")

            # Download original image
            print(f"Downloading image from S3: {s3_key}")
            original_image = self.download_image_from_s3(s3_key)

            # Validate image
            self.validate_image(original_image)

            # Optimize original image
            optimized_image = self.optimize_image(
                original_image, self.max_original_size
            )

            # Generate thumbnail
            thumbnail_image = self.generate_thumbnail(original_image)

            # Upload processed images
            original_s3_key = f"original/{media_id}.jpg"
            thumbnail_s3_key = f"thumb/{media_id}.jpg"

            print("Uploading original image")
            original_url = self.upload_image_to_s3(
                optimized_image, original_s3_key, "JPEG", 90
            )

            print("Uploading thumbnail")
            thumbnail_url = self.upload_image_to_s3(
                thumbnail_image, thumbnail_s3_key, "JPEG", self.thumbnail_quality
            )

            # Update media record
            update_data = {
                "status": "completed",
                "originalUrl": original_url,
                "thumbnailUrl": thumbnail_url,
                "processedAt": datetime.utcnow().isoformat(),
                "updatedAt": datetime.utcnow().isoformat(),
                "s3Key": original_s3_key,
                "s3Bucket": self.media_bucket,
            }

            self.update_media_record(media_id, profile_id, update_data)

            # Invalidate CloudFront cache
            cache_paths = [f"/{original_s3_key}", f"/{thumbnail_s3_key}"]
            self.invalidate_cloudfront_cache(cache_paths)

            print(f"Successfully processed media ID: {media_id}")

        except Exception as e:
            print(f"Error processing media: {str(e)}")
            # Update status to failed
            try:
                if "media_id" in locals() and "profile_id" in locals():
                    self.update_media_record(
                        media_id,
                        profile_id,
                        {
                            "status": "failed",
                            "updatedAt": datetime.utcnow().isoformat(),
                        },
                    )
            except Exception as update_error:
                print(f"Failed to update status to failed: {update_error}")
            raise


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for media processing

    Args:
        event: Lambda event object (S3 event notification)
        context: Lambda context object

    Returns:
        Dict[str, Any]: Processing result
    """
    try:
        print(f"Media Processing Event: {json.dumps(event)}")

        processor = MediaProcessor()

        # Process S3 event notifications
        for record in event.get("Records", []):
            if record.get("eventSource") == "aws:s3":
                s3_event = record.get("s3", {})
                bucket_name = s3_event.get("bucket", {}).get("name")
                s3_key = s3_event.get("object", {}).get("key")

                # URL decode the S3 key
                import urllib.parse

                s3_key = urllib.parse.unquote_plus(s3_key)

                print(f"Processing S3 event: bucket={bucket_name}, key={s3_key}")

                # Only process uploads to the uploads directory
                if s3_key.startswith("uploads/profile-images/"):
                    processor.process_profile_image(s3_key)
                else:
                    print(f"Skipping non-upload file: {s3_key}")

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Media processing completed successfully"}),
        }

    except Exception as e:
        print(f"Error in media processing: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Media processing failed: {str(e)}"}),
        }


if __name__ == "__main__":
    # Test handler
    test_event = {
        "Records": [
            {
                "eventSource": "aws:s3",
                "s3": {
                    "bucket": {"name": "test-bucket"},
                    "object": {"key": "uploads/profile-images/test123.jpg"},
                },
            }
        ]
    }

    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
