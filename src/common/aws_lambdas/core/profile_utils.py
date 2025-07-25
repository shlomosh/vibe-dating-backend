"""
Profile management utilities for the user service

This module contains all profile-related functions shared across services.
"""

import datetime
import logging
import os
from typing import Any, Dict, List, Optional

import boto3
import msgspec
from botocore.exceptions import ClientError

from .auth_utils import validate_id
from ..types.profile import (
    SexualPosition, BodyType, SexualityType, HostingType, TravelDistanceType,
    EggplantSizeType, PeachShapeType, HealthPracticesType, HivStatusType,
    PreventionPracticesType, MeetingTimeType, ChatStatusType,
    ProfileImage, ProfileRecord
)

logger = logging.getLogger(__name__)

dynamodb = boto3.resource("dynamodb")

class ProfileManager:
    def __init__(self, user_id: str):
        # Validate user_id format
        if not validate_id(user_id):
            raise ValueError("Invalid user-id")
        
        self.user_id = user_id
        self.table = self._get_table()

        self.user_data = self._get_user_record()
        self.profiles_data = self._get_profiles_records()

        allocated_ids_str = self.user_data.get("allocatedProfileIds", "")
        # Optimized string parsing
        self.allocated_profile_ids = [pid for pid in allocated_ids_str.split(",") if (pid := pid.strip())] if allocated_ids_str else []
        self.active_profile_ids = list(self.profiles_data.keys())

        # Use ProfileRecord fields directly instead of separate enum
        self.profile_fields = [field for field in ProfileRecord.__struct_fields__]

    def _get_table(self):
        """Get DynamoDB table with lazy initialization"""
        dynamodb_table = os.environ.get("DYNAMODB_TABLE")
        if not dynamodb_table:
            logger.error("DYNAMODB_TABLE environment variable not set")
            raise ValueError("DYNAMODB_TABLE environment variable not set")

        try:
            return dynamodb.Table(dynamodb_table)
        except Exception as e:
            logger.error(f"Failed to initialize DynamoDB table {dynamodb_table}: {str(e)}")
            raise

    def _get_user_record(self) -> Dict[str, Any]:
        """Get the complete user record from USER entry in DB"""
        try:
            response = self.table.get_item(
                Key={"PK": f"USER#{self.user_id}", "SK": "METADATA"}
            )
            user_record = response.get("Item", {})
            if not user_record:
                logger.warning(f"No user record found for user_id: {self.user_id}")
            return user_record
        except ClientError as e:
            logger.error(f"Failed to get user record for {self.user_id}: {str(e)}")
            raise RuntimeError(f"Failed to get user record: {str(e)}")
    
    def _get_active_profile_ids(self) -> List[str]:
        """Get active profile IDs for a user using GSI query"""
        try:
            response = self.table.query(
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
                ExpressionAttributeValues={
                    ":pk": f"USER#{self.user_id}",
                    ":sk_prefix": "PROFILE#"
                },
                ProjectionExpression="profileId"
            )
            return [item.get("profileId") for item in response.get("Items", []) if item.get("profileId")]
        except ClientError as e:
            logger.error(f"Failed to get active profile IDs for user {self.user_id}: {str(e)}")
            return []
    
    def _get_profiles_records(self) -> Dict[str, Dict[str, Any]]:
        """Get all active profiles for a user with batch optimization"""
        try:
            profile_ids = self._get_active_profile_ids()
            if not profile_ids:
                return {}

            # Use batch_get_item for better performance
            request_items = {
                self.table.name: {
                    'Keys': [{
                        'PK': f'PROFILE#{profile_id}',
                        'SK': 'METADATA'
                    } for profile_id in profile_ids]
                }
            }
            
            response = dynamodb.batch_get_item(RequestItems=request_items)
            profiles_data = {}
            
            # Handle partial failures in batch operations
            unprocessed_keys = response.get('UnprocessedKeys', {})
            if unprocessed_keys:
                logger.warning(f"Unprocessed keys in batch get for user {self.user_id}: {unprocessed_keys}")
            
            for item in response.get('Responses', {}).get(self.table.name, []):
                profile_id = item.get('PK', '').replace('PROFILE#', '')
                if profile_id:
                    profiles_data[profile_id] = item
                    
            return profiles_data

        except ClientError as e:
            logger.error(f"Failed to get active profiles data for user {self.user_id}: {str(e)}")
            raise RuntimeError(f"Failed to get active profiles data: {str(e)}")


    def _serialize_dynamodb_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Efficiently serialize items for DynamoDB"""
        serialized = {}
        for key, value in item.items():
            if isinstance(value, str):
                serialized[key] = {'S': value}
            elif isinstance(value, (int, float)):
                serialized[key] = {'N': str(value)}
            elif isinstance(value, bool):
                serialized[key] = {'BOOL': value}
            elif isinstance(value, list):
                serialized[key] = {'L': [self._serialize_dynamodb_item([v])[0] if isinstance(v, dict) else {'S': str(v)} for v in value]}
            elif isinstance(value, dict):
                serialized[key] = {'M': self._serialize_dynamodb_item(value)}
            else:
                serialized[key] = {'S': str(value)}
        return serialized

    def validate_profile_id(self, profile_id: str, is_existing: bool = False) -> bool:
        """Validate profile ID format"""
        if not validate_id(profile_id):
            return False
        
        if profile_id not in self.allocated_profile_ids:
            return False

        if is_existing and profile_id not in self.active_profile_ids:
            return False

        return True

    def validate_profile_record(self, profile_record: Dict[str, Any]) -> ProfileRecord:
        """Validate profile record data using msgspec"""
        try:
            # Convert dict to ProfileRecord struct for validation
            validated_record = msgspec.convert(profile_record, ProfileRecord)
            return validated_record
        except (msgspec.ValidationError, ValueError) as e:
            logger.warning(f"Profile validation failed for user {self.user_id}: {str(e)}")
            raise ValueError(f"Invalid profile data: {str(e)}")

    def create(self, profile_id: str, profile_record: Dict[str, Any]) -> bool:
        """
        Create a new profile for a user

        Args:
            profile_id: The profile ID
            profile_record: Profile data dictionary

        Returns:
            bool: True if creation was successful

        Raises:
            ValueError: If profile creation fails
        """
        if not validate_id(profile_id):
            raise ValueError("Invalid profile_id format")
            
        if profile_id not in self.allocated_profile_ids:
            raise ValueError("Profile-Id is invalid")

        if profile_id in self.active_profile_ids:
            raise ValueError("Profile-Id already created")

        validated_record = self.validate_profile_record(profile_record)
        profile_record = msgspec.to_builtins(validated_record)
        
        # Use timezone-aware datetime
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        try:
            # Use transaction to ensure atomicity
            profile_item = {
                "PK": f"PROFILE#{profile_id}",
                "SK": "METADATA",
                "userId": self.user_id,
                **{k: v for k, v in profile_record.items() if k in self.profile_fields and v is not None},
                "createdAt": now,
                "updatedAt": now,
            }
            
            lookup_item = {
                "PK": f"USER#{self.user_id}",
                "SK": f"PROFILE#{profile_id}",
                "profileId": profile_id,
                "createdAt": now,
            }
            
            # Use optimized serialization
            dynamodb.meta.client.transact_write_items(
                TransactItems=[
                    {
                        'Put': {
                            'TableName': self.table.name,
                            'Item': self._serialize_dynamodb_item(profile_item),
                            'ConditionExpression': 'attribute_not_exists(PK)'
                        }
                    },
                    {
                        'Put': {
                            'TableName': self.table.name,
                            'Item': self._serialize_dynamodb_item(lookup_item)
                        }
                    }
                ]
            )
            
            logger.info(f"Profile {profile_id} created successfully for user {self.user_id}")
            return True

        except ClientError as e:
            logger.error(f"Failed to create profile {profile_id} for user {self.user_id}: {str(e)}")
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise ValueError("Profile already exists")
            raise ValueError(f"Failed to create profile: {str(e)}")

    def update(self, profile_id: str, profile_record: Dict[str, Any]) -> bool:
        """
        Update an existing profile

        Args:
            profile_id: The profile ID
            profile_record: Updated profile data

        Returns:
            bool: True if update was successful

        Raises:
            ValueError: If profile update fails
        """
        if not validate_id(profile_id):
            raise ValueError("Invalid profile_id format")
            
        if profile_id not in self.allocated_profile_ids:
            raise ValueError("Profile-Id is invalid")

        if profile_id not in self.active_profile_ids:
            raise ValueError("Profile-Id not created")

        validated_record = self.validate_profile_record(profile_record)
        profile_record = msgspec.to_builtins(validated_record)
        
        # Use timezone-aware datetime
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Optimized update expression building
        update_fields = []
        expression_attribute_values = {":updated_at": now}
        expression_attribute_names = {}

        for field in self.profile_fields:
            if field in profile_record:
                update_fields.append(f"#{field} = :{field}")
                expression_attribute_values[f":{field}"] = profile_record[field]
                expression_attribute_names[f"#{field}"] = field

        update_expression = f"SET updatedAt = :updated_at{f', ' + ', '.join(update_fields)}' if update_fields else "SET updatedAt = :updated_at"

        try:
            kwargs = {
                "Key": {"PK": f"PROFILE#{profile_id}", "SK": "METADATA"},
                "UpdateExpression": update_expression,
                "ExpressionAttributeValues": expression_attribute_values,
                "ReturnValues": "ALL_NEW",
            }

            if expression_attribute_names:
                kwargs["ExpressionAttributeNames"] = expression_attribute_names

            self.table.update_item(**kwargs)

            return True

        except ClientError as e:
            raise ValueError(f"Failed to update profile: {str(e)}")

    def upsert(self, profile_id: str, profile_record: Dict[str, Any]) -> bool:
        """
        Upsert a profile

        Args:
            profile_id: The profile ID
            profile_record: Upsert profile data

        Returns:
            bool: True if upsert was successful

        Raises:
            ValueError: If profile upsert fails
        """
        if profile_id not in self.allocated_profile_ids:
            raise ValueError("Profile-Id is invalid")

        if profile_id in self.active_profile_ids:
            return self.update(profile_id, profile_record)
        else:
            return self.create(profile_id, profile_record)

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
        if not validate_id(profile_id):
            raise ValueError("Invalid profile_id format")
            
        if profile_id not in self.allocated_profile_ids:
            raise ValueError("Profile-Id is invalid")

        if profile_id not in self.active_profile_ids:
            raise ValueError("Profile-Id not created")

        try:
            # Use transaction to ensure atomicity
            dynamodb.meta.client.transact_write_items(
                TransactItems=[
                    {
                        'Delete': {
                            'TableName': self.table.name,
                            'Key': {
                                'PK': {'S': f'PROFILE#{profile_id}'},
                                'SK': {'S': 'METADATA'}
                            }
                        }
                    },
                    {
                        'Delete': {
                            'TableName': self.table.name,
                            'Key': {
                                'PK': {'S': f'USER#{self.user_id}'},
                                'SK': {'S': f'PROFILE#{profile_id}'}
                            }
                        }
                    }
                ]
            )
            
            logger.info(f"Profile {profile_id} deleted successfully for user {self.user_id}")
            return True

        except ClientError as e:
            logger.error(f"Failed to delete profile {profile_id} for user {self.user_id}: {str(e)}")
            raise ValueError(f"Failed to delete profile: {str(e)}")

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
        if not validate_id(profile_id):
            raise ValueError("Invalid profile_id format")
            
        if profile_id not in self.allocated_profile_ids:
            raise ValueError("Profile-Id is invalid")
        
        if profile_id not in self.profiles_data:
            raise ValueError("Profile not found")
            
        return self.profiles_data[profile_id]
