import base64
import logging
import os
import uuid
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError

from core.aws import DynamoDBService, SecretsManagerService
from core.settings import CoreSettings

logger = logging.getLogger(__name__)


class CommonManager:
    def __init__(self, user_id: str, ok_if_not_exists: bool = False):
        # Validate user_id format
        if not self.validate_id(user_id):
            raise ValueError("Invalid user-id")

        self.user_id = user_id
        self.table = DynamoDBService.get_table()

        self.user_data = self._get_user_record(ok_if_not_exists=ok_if_not_exists)

    def _get_user_record(self, ok_if_not_exists: bool = False) -> Dict[str, Any]:
        """Get the complete user record from USER entry in DB"""
        try:
            response = self.table.get_item(
                Key={"PK": f"USER#{self.user_id}", "SK": "METADATA"}
            )
            user_record = response.get("Item", {})
            if not user_record:
                if ok_if_not_exists:
                    return None
                else:
                    logger.warning(f"No user record found for user_id: {self.user_id}")
                    raise ValueError(
                        f"User record not found for user_id: {self.user_id}"
                    )
            return user_record

        except ClientError as e:
            logger.error(f"Failed to get user record for {self.user_id}: {str(e)}")
            raise RuntimeError(f"Failed to get user record: {str(e)}")

    @classmethod
    def hash_string_to_id(cls, platform_id_string: str) -> str:
        """
        Convert platform ID string to Vibe user ID using UUID v5

        Args:
            platform_id_string: String in format "tg:123456789" or "userId:profileIndex"
            length: Length of the final user ID (default: 8)

        Returns:
            str: Base64 encoded user ID
        """
        # Get UUID namespace from AWS Secrets Manager
        uuid_namespace_arn = os.environ.get("UUID_NAMESPACE_SECRET_ARN")
        if not uuid_namespace_arn:
            raise Exception("UUID_NAMESPACE_SECRET_ARN environment variable not set")

        uuid_namespace = SecretsManagerService.get_secret(uuid_namespace_arn)
        if not uuid_namespace:
            raise Exception("Failed to retrieve UUID namespace from Secrets Manager")

        # Create UUID v5 with namespace from Secrets Manager
        namespace_uuid = uuid.UUID(uuid_namespace)
        user_uuid = uuid.uuid5(namespace_uuid, platform_id_string)

        # Convert UUID to base64
        uuid_bytes = user_uuid.bytes
        base64_string = base64.b64encode(uuid_bytes).decode("utf-8")

        # Remove padding and return first N characters
        return base64_string.rstrip("=")[: CoreSettings().record_id_length]

    @classmethod
    def validate_id(cls, some_id: str) -> bool:
        """
        Validate that a user/profile ID has the correct format and length

        Args:
            user_id: The user/profile ID to validate

        Returns:
            bool: True if the ID is valid, False otherwise
        """
        if not some_id or not isinstance(some_id, str):
            return False

        # Check if the ID matches the expected length from CoreSettings
        expected_length = CoreSettings().record_id_length
        if len(some_id) != expected_length:
            return False

        # Validate that the ID contains only valid base64 characters (A-Z, a-z, 0-9, +, /)
        # Note: Since hash_string_to_id removes padding (=), we don't expect padding in valid IDs
        import re

        base64_pattern = r"^[A-Za-z0-9+/]+$"
        if not re.match(base64_pattern, some_id):
            return False

        # Additional validation: ensure the ID is not empty and doesn't contain invalid characters
        if not some_id.strip():
            return False

        return True
