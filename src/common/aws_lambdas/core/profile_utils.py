"""
Profile management utilities for the user service

This module contains all profile-related functions shared across services.
"""

import datetime
import logging
from typing import Any, Dict, List, Optional
from copy import deepcopy

import msgspec
from botocore.exceptions import ClientError
from core_types.profile import *

from core.aws import DynamoDBService
from core.manager import CommonManager
from core.settings import CoreSettings

logger = logging.getLogger(__name__)


class ProfileManager(CommonManager):
    def __init__(self, user_id: str, profile_id: Optional[str] = None, ok_if_not_exists: bool = False):
        super().__init__(user_id, ok_if_not_exists=ok_if_not_exists)

        self.dynamodb = DynamoDBService.get_dynamodb()
        self.table = DynamoDBService.get_table()

        # get allocated/active profile ids for the user
        if self.user_data:            
            self.allocated_profile_ids = self.user_data.get("allocatedProfileIds", [])
            self.active_profile_ids = self.user_data.get("activeProfileIds", [])
        else:
            self.allocated_profile_ids = []
            self.active_profile_ids = []

        if profile_id is not None:
            profile_ids_to_fetch = [profile_id]
        else:
            profile_ids_to_fetch = self.active_profile_ids

        # get profiles data from DB
        self.profiles_data = self._get_profiles_records(profile_ids_to_fetch=profile_ids_to_fetch)

        # validate profile_id if provided
        if profile_id is not None:
            if not self.validate_profile_id(profile_id, is_existing=True):
                raise ValueError(f"Invalid profile_id: {profile_id}")
        self.profile_id = profile_id

        # Use ProfileRecord fields directly instead of separate enum
        self.profile_fields = [field for field in ProfileRecord.__struct_fields__]

    def _get_profiles_records(self, profile_ids_to_fetch: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get all active profiles for a user with batch optimization"""        
        try:
            if not profile_ids_to_fetch:
               return {}

            # Use batch_get_item for better performance
            request_items = {
                self.table.name: {
                    "Keys": [
                        {"PK": f"PROFILE#{profile_id}", "SK": "METADATA"}
                        for profile_id in profile_ids_to_fetch
                    ]
                }
            }

            response = self.dynamodb.batch_get_item(RequestItems=request_items)
            profiles_data = {}

            # Handle partial failures in batch operations
            unprocessed_keys = response.get("UnprocessedKeys", {})
            if unprocessed_keys:
                logger.warning(
                    f"Unprocessed keys in batch get for user {self.user_id}: {unprocessed_keys}"
                )

            for item in response.get("Responses", {}).get(self.table.name, []):
                profile_id = item.get("PK", "").replace("PROFILE#", "")
                if profile_id:
                    profiles_data[profile_id] = item

            return profiles_data

        except ClientError as e:
            logger.error(
                f"Failed to get active profiles data for user {self.user_id}: {str(e)}"
            )
            raise RuntimeError(f"Failed to get active profiles data: {str(e)}")

    def validate_profile_id(self, profile_id: str, is_existing: Optional[bool] = None) -> bool:
        """Validate profile ID format
        Args:
            profile_id: The profile ID to validate
            is_existing: Whether the profile ID is existing (if None, both allocated and active profiles are checked)

        Returns:
            bool: True if the profile ID is valid, False otherwise
        """
        if not self.validate_id(profile_id):
            return False
        
        if not profile_id in self.allocated_profile_ids:
            return False
        
        if is_existing == True:
            return profile_id in self.active_profile_ids
        elif is_existing == False:
            return profile_id not in self.active_profile_ids
        
        return True

    def validate_profile_record(self, profile_record: Dict[str, Any]) -> ProfileRecord:
        """Validate profile record data using msgspec"""
        try:
            validated_record = msgspec.convert(profile_record, ProfileRecord)
            return validated_record
        except (msgspec.ValidationError, ValueError) as e:
            logger.warning(
                f"Profile validation failed for user {profile_record}: {str(e)}"
            )
            raise ValueError(f"Invalid profile data: {str(e)}")

    def upsert(self, profile_id: str, profile_record: Dict[str, Any]) -> bool:
        """Create or update profile in DynamoDB"""
        if not self.validate_profile_id(profile_id, is_existing=None):
            raise ValueError(f"Invalid profile_id: {profile_id}")
        
        now = datetime.datetime.now(datetime.timezone.utc)
        now_iso = now.isoformat()
        now_tag = now.strftime("%Y%m%d%H%M%S")

        if profile_id not in self.profiles_data:
            # Create new profile
            profile_data = {
                "userId": self.user_id,
                "allocatedMediaIds": self.allocate_ids(count=CoreSettings().max_profiles_count),
                "activeMediaIds": [],
                "createdAt": now_iso,
                "updatedAt": now_iso,
                **profile_record
            }
        else:
            # Update existing profile
            profile_data = deepcopy(self.profiles_data[profile_id])
            profile_data.update({
                "updatedAt": now_iso,
                **profile_record
            })

        # Validate and convert to ProfileRecord
        try:
            validated_profile_data = self.validate_profile_record(profile_data)
            profile_data = msgspec.to_builtins(validated_profile_data)
        except (ValueError, TypeError) as e:
            logger.error(f"Profile data validation failed for {profile_id}: {str(e)}")
            raise ValueError(f"Invalid profile data: {str(e)}")

        try:
            self.table.put_item(
                Item={
                    "PK": f"PROFILE#{profile_id}",
                    "SK": "METADATA",
                    "GSI1PK": f"USER#{self.user_id}",
                    "GSI1SK": f"PROFILE#{profile_id}",
                    "GSI2PK": f"TIME#{now_tag[:8]}",
                    "GSI2SK": f"{now_tag}#PROFILE#{profile_id}",
                    "GSI3PK": "PROFILE#ALL",
                    "GSI3SK": f"PROFILE#{profile_id}",
                    **profile_data
                }
            )
            
            # Update in-memory cache
            self.profiles_data[profile_id] = profile_data
            
            # If this is a new profile, add to active list
            if profile_id not in self.active_profile_ids:
                self._update_user_active_profile_ids(profile_id, action="add")

            logger.info(f"Profile {profile_id} upserted successfully for user {self.user_id}")
            return True

        except ClientError as e:
            logger.error(f"Failed to upsert profile {profile_id} for user {self.user_id}: {str(e)} {e.response}")
            raise ValueError(f"Failed to upsert profile: {str(e)} {e.response}")

    def delete(self, profile_id: str) -> bool:
        """
        Delete a profile

        Args:
            profile_id: The profile ID

        Returns:
            bool: True if deletion was successful

        Raises:
            ValueError: If profile deletion fails
        """
        if self.profile_id is not None and self.profile_id != profile_id:
            raise ValueError("Profile delete is not allowed in current manager-mode.")

        if not self.validate_profile_id(profile_id, is_existing=True):
            raise ValueError("Profile-Id is invalid or not created.")

        try:
            # Delete only the profile metadata (no more lookup entries)
            request_items = {
                self.table.name: [
                    {
                        "DeleteRequest": {
                            "Key": {
                                "PK": f"PROFILE#{profile_id}",
                                "SK": "METADATA",
                            },
                        }
                    }
                ]
            }

            # Execute batch write
            response = self.dynamodb.meta.client.batch_write_item(RequestItems=request_items)

            # Handle unprocessed items (retry if needed)
            unprocessed_items = response.get("UnprocessedItems", {})
            if unprocessed_items:
                logger.warning(f"Unprocessed items in batch delete: {unprocessed_items}")
                # Retry unprocessed items once
                retry_response = self.dynamodb.meta.client.batch_write_item(RequestItems=unprocessed_items)
                if retry_response.get("UnprocessedItems"):
                    raise ValueError("Failed to delete all items after retry")

            # Update in-memory cache by removing the deleted profile
            if profile_id in self.profiles_data:
                del self.profiles_data[profile_id]

            # Remove profile_ids from user's activeProfileIds list
            self._update_user_active_profile_ids(profile_id, action="remove")

            logger.info(f"Profile {profile_id} deleted successfully for user {self.user_id}")
            return True

        except ClientError as e:
            logger.error(f"Failed to delete profile {profile_id} for user {self.user_id}: {str(e)} {e.response}")
            raise ValueError(f"Failed to delete profile: {str(e)} {e.response}")

    def get(self, profile_id: str) -> Dict[str, Any]:
        """
        Get a profile by ID

        Args:
            profile_id: The profile ID to retrieve

        Returns:
            Dict containing profile data

        Raises:
            ValueError: If profile ID is invalid or not found
        """
        if not self.validate_id(profile_id):
            raise ValueError("Invalid profile_id format")

        if profile_id not in self.allocated_profile_ids:
            raise ValueError("Profile-Id is invalid")

        # If profile is not in cache, try to fetch it directly from DynamoDB
        if profile_id not in self.profiles_data:
            try:
                response = self.table.get_item(
                    Key={"PK": f"PROFILE#{profile_id}", "SK": "METADATA"}
                )
                if "Item" in response:
                    profile_item = response["Item"]
                    # Update cache
                    self.profiles_data[profile_id] = profile_item
                    if profile_id not in self.active_profile_ids:
                        self.active_profile_ids.append(profile_id)
                    return profile_item
                else:
                    raise ValueError("Profile not found")
            except ClientError as e:
                logger.error(f"Failed to get profile {profile_id} from DynamoDB: {str(e)}")
                raise ValueError(f"Profile not found: {str(e)}")

        return self.profiles_data[profile_id]

    def refresh_cache(self) -> None:
        """
        Refresh the in-memory cache by re-fetching data from DynamoDB
        Useful when GSI consistency issues occur
        """
        try:
            self.profiles_data = self._get_profiles_records(profile_ids_to_fetch=self.active_profile_ids)
            logger.info(f"Cache refreshed for user {self.user_id}")
        except Exception as e:
            logger.error(f"Failed to refresh cache for user {self.user_id}: {str(e)}")

    def _update_user_active_profile_ids(self, profile_id: str, action: str = "add") -> bool:
        """
        Update the user's activeProfileIds list in DynamoDB
        
        Args:
            profile_id: The profile ID to add/remove
            action: Either "add" or "remove"
            
        Returns:
            bool: True if update was successful
        """
        try:
            if action == "add":
                # Add profile_id to activeProfileIds if not already present
                if profile_id not in self.active_profile_ids:
                    self.active_profile_ids.append(profile_id)
                    
                    # Update DynamoDB user item
                    update_expression = "SET activeProfileIds = :profile_ids, updatedAt = :updated_at"
                    expression_attribute_values = {
                        ":profile_ids": self.active_profile_ids,
                        ":updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
                    }
                    
                    self.table.update_item(
                        Key={"PK": f"USER#{self.user_id}", "SK": "METADATA"},
                        UpdateExpression=update_expression,
                        ExpressionAttributeValues=expression_attribute_values
                    )
                    
                    logger.info(f"Added profile {profile_id} to activeProfileIds for user {self.user_id}")
                    
            elif action == "remove":
                # Remove profile_id from activeProfileIds if present
                if profile_id in self.active_profile_ids:
                    self.active_profile_ids.remove(profile_id)
                    
                    # Update DynamoDB user item
                    update_expression = "SET activeProfileIds = :profile_ids, updatedAt = :updated_at"
                    expression_attribute_values = {
                        ":profile_ids": self.active_profile_ids,
                        ":updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
                    }
                    
                    self.table.update_item(
                        Key={"PK": f"USER#{self.user_id}", "SK": "METADATA"},
                        UpdateExpression=update_expression,
                        ExpressionAttributeValues=expression_attribute_values
                    )
                    
                    logger.info(f"Removed profile {profile_id} from activeProfileIds for user {self.user_id}")
            
            return True
            
        except ClientError as e:
            logger.error(f"Failed to update user activeProfileIds for user {self.user_id}: {str(e)}")
            raise ValueError(f"Failed to update user activeProfileIds: {str(e)}")
