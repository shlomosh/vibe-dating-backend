"""
User management utilities for the auth service

This module contains all user-related functions shared across services.
"""

import datetime
import logging
from typing import Any, Dict, Optional
from copy import deepcopy

import msgspec
from botocore.exceptions import ClientError
from core_types.user import UserRecord, UserStatus, UserStatusData

from core.manager import CommonManager
from core.settings import CoreSettings

logger = logging.getLogger(__name__)


class UserManager(CommonManager):
    def __init__(
        self, user_id: Optional[str] = None, platform: Optional[str] = None, platform_user_id: Optional[str] = None
    ):
        """
        Initialize UserManager with either user_id or platform + platform_user_id

        Args:
            user_id: Vibe user ID (if known)
            platform: Platform name (i.e. "telegram")
            platform_user_id: Platform user ID (to generate user_id)
        """
        self.platform = platform
        self.platform_user_id = platform_user_id

        if user_id is None and (platform is not None and platform_user_id is not None):
            ok_if_not_exists = True  # ok if user doesn't exist yet
            user_id = self.hash_string_to_id(f"{platform}:{platform_user_id}")
        else:
            ok_if_not_exists = True

        super().__init__(user_id, ok_if_not_exists=ok_if_not_exists)

    @classmethod
    def validate_user_record(cls, user_record: Dict[str, Any]) -> UserRecord:
        """Validate user record data using msgspec"""
        try:
            validated_record = msgspec.convert(user_record, UserRecord)
            return validated_record
        except (msgspec.ValidationError, ValueError) as e:
            logger.warning(
                f"User validation failed for user {user_record}: {str(e)}"
            )            
            raise ValueError(f"Invalid user data: {str(e)}")

    def upsert(
        self, platform: str, platform_user_id: str, platform_user_data: Dict[str, Any]
    ) -> bool:
        """Create or update user in DynamoDB"""
        now = datetime.datetime.now(datetime.timezone.utc)
        now_iso = now.isoformat()
        now_tag = now.strftime("%Y%m%d%H%M%S")
        
        if not self.user_data:
            # Create new user with all required fields
            user_data = {
                "platform": str(platform),
                "platformId": str(platform_user_id),
                "platformMetadata": platform_user_data,
                "allocatedProfileIds": self.allocate_ids(count=CoreSettings().max_profiles_count),
                "activeProfileIds": [],
                "status": UserStatus.ACTIVE,
                "statusData": UserStatusData(),
                "preferences": {},
                "loginCount": int(1),
                "lastActiveAt": now_iso,
                "updatedAt": now_iso,
                "createdAt": now_iso,
            }
        else:
            # Update existing user
            user_data = deepcopy(self.user_data)
            user_data.update({
                "loginCount": int(user_data.get("loginCount", 0) + 1),
                "lastActiveAt": now_iso,
                "updatedAt": now_iso
            })

        # Validate and convert to UserRecord
        try:
            validated_user_data = self.validate_user_record(user_data)
            user_data = msgspec.to_builtins(validated_user_data)
        except (ValueError, TypeError) as e:
            logger.error(f"User data validation failed for {self.user_id}: {str(e)}")
            raise ValueError(f"Invalid user data: {str(e)}")

        try:
            self.table.put_item(
                Item={
                    "PK": f"USER#{self.user_id}",
                    "SK": "METADATA",
                    "GSI1PK": f"USER#{self.user_id}",
                    "GSI1SK": "METADATA",
                    "GSI2PK": f"TIME#{now_tag[:8]}",
                    "GSI2SK": f"{now_tag}#USER#{self.user_id}",
                    "GSI3PK": "USER#ALL",
                    "GSI3SK": f"USER#{self.user_id}",
                    **user_data
                }
            )

            # Refresh cache
            self.user_data = user_data
            logger.info(f"User {self.user_id} created/updated successfully")
            return True

        except ClientError as e:
            logger.error(f"Failed to create/update user {self.user_id}: {str(e)} {e.response}")
            raise RuntimeError(f"Failed to create/update user: {str(e)} {e.response}")

    def is_banned(self) -> bool:
        """
        Check if user is currently banned

        Returns:
            bool: True if user is banned and ban hasn't expired
        """
        if not self.user_data:
            return False

        status = self.user_data.get("status", UserStatus.ACTIVE.value)
        if status != UserStatus.BANNED.value:
            return False

        # Check statusData for ban information
        status_data = self.user_data.get("statusData", {})
        ban_to = status_data.get("banTo")

        if not ban_to:
            # Permanent ban
            return True

        # Check if ban has expired
        try:
            ban_expiry = datetime.datetime.fromisoformat(ban_to.replace("Z", "+00:00"))
            now = datetime.datetime.now(datetime.timezone.utc)
            return now < ban_expiry
        except (ValueError, AttributeError):
            # If we can't parse the date, assume permanent ban
            return True

    def get(self) -> Dict[str, Any]:
        """
        Get user record

        Returns:
            Dict containing user data
        """
        if not self.user_data:
            raise ValueError("User not found")

        return self.user_data
