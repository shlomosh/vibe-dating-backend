"""
User management utilities for the auth service

This module contains all user-related functions shared across services.
"""

import datetime
import logging
from typing import Any, Dict

import msgspec
from botocore.exceptions import ClientError
from core_types.user import UserRecord, UserStatus, UserStatusData

from core.manager import CommonManager

logger = logging.getLogger(__name__)


class UserManager(CommonManager):
    def __init__(
        self, user_id: str = None, platform: str = None, platform_user_id: str = None
    ):
        """
        Initialize UserManager with either user_id or platform + platform_user_id

        Args:
            user_id: Vibe user ID (if known)
            platform: Platform name (e.g. "telegram")
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

        self.allocated_profile_ids = self.get_allocated_profile_ids(self.user_id)

    @classmethod
    def get_allocated_profile_ids(cls, user_id: str) -> list:
        """
        Get allocated profile IDs for a user

        Args:
            user_id: The user ID

        Returns:
            list: List of allocated profile IDs for the user
        """
        from core.settings import CoreSettings

        core_settings = CoreSettings()

        return [
            cls.hash_string_to_id(f"{user_id}:{profile_idx}")
            for profile_idx in range(0, core_settings.max_profile_count)
        ]

    @classmethod
    def validate_user_record(cls, user_record: Dict[str, Any]) -> UserRecord:
        """Validate user record data using msgspec"""
        try:
            validated_record = msgspec.convert(user_record, UserRecord)
            return validated_record
        except (msgspec.ValidationError, ValueError) as e:
            raise ValueError(f"Invalid user data: {str(e)}")

    def upsert(
        self, platform: str, platform_user_id: str, platform_user_data: Dict[str, Any]
    ) -> bool:
        """
        Create or update user in DynamoDB

        Args:
            platform: Platform name (e.g. "telegram")
            platform_user_id: The platform user ID
            platform_user_data: The platform user data dictionary

        Returns:
            bool: True if operation was successful
        """
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Start with existing user data if available
        if self.user_data:
            user_record = self.user_data.copy()
        else:
            user_record = {}

        # Only update fields that are missing or need updating
        updates_needed = {}
        expression_parts = []
        expression_values = {}
        expression_names = {}

        # Check and update platform if missing or different
        if not user_record.get("platform") or user_record.get("platform") != platform:
            updates_needed["platform"] = platform
            expression_parts.append("platform = :platform")
            expression_values[":platform"] = platform

        # Check and update platformId if missing or different
        if (
            not user_record.get("platformId")
            or user_record.get("platformId") != platform_user_id
        ):
            updates_needed["platformId"] = platform_user_id
            expression_parts.append("platformId = :pid")
            expression_values[":pid"] = platform_user_id

        # Check and update platformMetadata if missing or different
        if (
            not user_record.get("platformMetadata")
            or user_record.get("platformMetadata") != platform_user_data
        ):
            updates_needed["platformMetadata"] = platform_user_data
            expression_parts.append("platformMetadata = :pmd")
            expression_values[":pmd"] = platform_user_data

        # Check and update preferences if missing
        if not user_record.get("preferences"):
            updates_needed["preferences"] = {"notifications": True, "privacy": "public"}
            expression_parts.append("#prefs = :prefs")
            expression_names["#prefs"] = "preferences"
            expression_values[":prefs"] = {"notifications": True, "privacy": "public"}

        # Check and update status if missing
        if not user_record.get("status"):
            updates_needed["status"] = UserStatus.ACTIVE.value
            expression_parts.append("#status = :status")
            expression_names["#status"] = "status"
            expression_values[":status"] = UserStatus.ACTIVE.value

        # Check and update statusData if missing
        if not user_record.get("statusData"):
            status_data_obj = UserStatusData()
            updates_needed["statusData"] = msgspec.to_builtins(status_data_obj)
            expression_parts.append("statusData = :sd")
            expression_values[":sd"] = msgspec.to_builtins(status_data_obj)

        # Check and update profileIds if missing
        if not user_record.get("profileIds"):
            updates_needed["profileIds"] = self.allocated_profile_ids
            expression_parts.append("profileIds = :apids")
            expression_values[":apids"] = self.allocated_profile_ids

        # Increment loginCount on each login
        current_login_count = user_record.get("loginCount", 0)
        new_login_count = current_login_count + 1
        expression_parts.append("loginCount = :lc")
        expression_values[":lc"] = new_login_count

        # Always update lastActiveAt and updatedAt
        expression_parts.append("lastActiveAt = :laa")
        expression_parts.append("updatedAt = :ua")
        expression_values[":laa"] = now
        expression_values[":ua"] = now

        # Add GSI keys
        expression_parts.append("GSI1PK = :gsi1pk")
        expression_parts.append("GSI1SK = :gsi1sk")
        expression_values[":gsi1pk"] = f"USER#{self.user_id}"
        expression_values[":gsi1sk"] = "METADATA"

        # Add createdAt only if this is a new user
        if not self.user_data:
            expression_parts.append("createdAt = :ca")
            expression_values[":ca"] = now

        try:
            if expression_parts:
                update_expression = "SET " + ", ".join(expression_parts)

                update_kwargs = {
                    "Key": {"PK": f"USER#{self.user_id}", "SK": "METADATA"},
                    "UpdateExpression": update_expression,
                    "ExpressionAttributeValues": expression_values,
                }
                
                if expression_names:
                    update_kwargs["ExpressionAttributeNames"] = expression_names

                self.table.update_item(**update_kwargs)

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
