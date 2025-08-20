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
            return DynamoDBService.convert_dynamodb_types_to_python(user_record)

        except ClientError as e:
            logger.error(f"Failed to get user record for {self.user_id}: {str(e)}")
            raise RuntimeError(f"Failed to get user record: {str(e)}")

    @classmethod
    def allocate_ids(cls, count: int, prefix: Optional[str] = None) -> list:
        """
        Get allocated IDs

        Args:
            count: The number of IDs to allocate
            prefix: The prefix to use for the IDs (optional. If not provided, random IDs will be generated)

        Returns:
            list: List of allocated IDs
        """

        if prefix is None:
            return [
                cls.generate_random_id()
                for _ in range(0, count)
            ]
        else:
            return [
                cls.hash_string_to_id(f"{prefix}:{_}")
                for _ in range(0, count)
            ]

    @classmethod
    def hash_string_to_id(cls, string_to_hash: str) -> str:
        """
        Convert platform ID string to Vibe user ID using UUID v5

        Args:
            string_to_hash: String in format "telegram:123456789" or "userId:profileIndex"
            length: Length of the final user ID (default: 8)

        Returns:
            str: URL-safe base64 encoded user ID
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
        user_uuid = uuid.uuid5(namespace_uuid, string_to_hash)

        # Convert UUID to URL-safe base64
        uuid_bytes = user_uuid.bytes
        base64_string = base64.urlsafe_b64encode(uuid_bytes).decode("utf-8")

        # Remove padding and return first N characters
        return base64_string.rstrip("=")[: CoreSettings().record_id_length]

    @classmethod
    def generate_random_id(cls) -> str:
        """
        Generate a random ID using UUID v4

        Returns:
            str: URL-safe base64 encoded random ID
        """
        # Generate random UUID v4
        random_uuid = uuid.uuid4()

        # Convert UUID to URL-safe base64
        uuid_bytes = random_uuid.bytes
        base64_string = base64.urlsafe_b64encode(uuid_bytes).decode("utf-8")

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
        base64_pattern = r"^[A-Za-z0-9\-_]+$"
        if not re.match(base64_pattern, some_id):
            return False

        # Additional validation: ensure the ID is not empty and doesn't contain invalid characters
        if not some_id.strip():
            return False

        return True
