"""
Media management utilities for the user service

This module contains all media-related functions shared across services.
"""

import datetime
import logging
from typing import Any, Dict, List, Optional
from copy import deepcopy

import msgspec
from botocore.exceptions import ClientError

from core.aws import DynamoDBService
from core.profile_utils import ProfileManager
from core.settings import CoreSettings
from core_types.media import *

logger = logging.getLogger(__name__)


class MediaManager(ProfileManager):
    """Manages media operations for user profiles"""
    
    def __init__(self, user_id: str, profile_id: str):
        super().__init__(user_id, profile_id)
        self.table = DynamoDBService.get_table()
        
        # Get current profile data from parent class
        self.profile_data = self.get(profile_id)
        self.allocated_media_ids = self.profile_data.get("allocatedMediaIds", [])
        self.active_media_ids = self.profile_data.get("activeMediaIds", [])
        
        # Use MediaRecord fields directly instead of separate enum
        self.media_fields = [field for field in MediaRecord.__struct_fields__]
    
    def validate_media_record(self, media_record: Dict[str, Any]) -> MediaRecord:
        """Validate media record data using msgspec"""
        try:
            validated_record = msgspec.convert(media_record, MediaRecord)
            return validated_record
        except (msgspec.ValidationError, ValueError) as e:
            logger.warning(
                f"Media validation failed for media {media_record}: {str(e)}"
            )
            raise ValueError(f"Invalid media data: {str(e)}")
    
    def validate_media_id(self, media_id: str, is_existing: bool = False) -> bool:
        """Validate media ID"""
        if is_existing:
            if media_id not in self.allocated_media_ids:
                raise ValueError(f"Media ID {media_id} is not allocated for this profile")
        else:
            if media_id in self.allocated_media_ids:
                raise ValueError(f"Media ID {media_id} is already allocated for this profile")
        return True
    
    def get_available_media_id(self) -> Optional[str]:
        """Get the next available pre-allocated media ID"""
        available_ids = [
            media_id for media_id in self.allocated_media_ids 
            if media_id not in self.active_media_ids
        ]
        return available_ids[0] if available_ids else None
    
    def get_available_media_count(self) -> int:
        """Get count of available media slots"""
        return len(self.allocated_media_ids) - len(self.active_media_ids)
    
    def activate_media_id(self, media_id: str) -> bool:
        """Move media ID from allocated to active in profile"""
        if media_id not in self.allocated_media_ids:
            raise ValueError(f"Media ID {media_id} is not allocated for this profile")
        
        if media_id in self.active_media_ids:
            raise ValueError(f"Media ID {media_id} is already active")
        
        try:
            # Update profile's activeMediaIds
            updated_active_ids = self.active_media_ids + [media_id]
            
            update_expression = "SET activeMediaIds = :active_ids, updatedAt = :updated_at"
            expression_attribute_values = {
                ":active_ids": updated_active_ids,
                ":updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
            
            self.table.update_item(
                Key={"PK": f"PROFILE#{self.profile_id}", "SK": "METADATA"},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values
            )
            
            # Update local cache
            self.active_media_ids = updated_active_ids
            
            logger.info(f"Activated media ID {media_id} for profile {self.profile_id}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to activate media ID {media_id}: {str(e)}")
            raise ValueError(f"Failed to activate media ID: {str(e)}")
    
    def deactivate_media_id(self, media_id: str) -> bool:
        """Remove media ID from active list in profile"""
        if media_id not in self.active_media_ids:
            raise ValueError(f"Media ID {media_id} is not active")
        
        try:
            # Update profile's activeMediaIds
            updated_active_ids = [mid for mid in self.active_media_ids if mid != media_id]
            
            update_expression = "SET activeMediaIds = :active_ids, updatedAt = :updated_at"
            expression_attribute_values = {
                ":active_ids": updated_active_ids,
                ":updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
            
            self.table.update_item(
                Key={"PK": f"PROFILE#{self.profile_id}", "SK": "METADATA"},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values
            )
            
            # Update local cache
            self.active_media_ids = updated_active_ids
            
            logger.info(f"Deactivated media ID {media_id} for profile {self.profile_id}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to deactivate media ID {media_id}: {str(e)}")
            raise ValueError(f"Failed to deactivate media ID: {str(e)}")
    
    def upsert_media_record(
        self,
        media_id: str,
        upload_s3_key: str,
        media_blob: Dict[str, Any],
        media_type: str,
        size: Optional[int] = None,
        dimensions: Optional[Dict[str, int]] = None,
        duration: Optional[float] = None,
        error_msg: Optional[str] = None,
        status: MediaStatus = MediaStatus.PENDING,
        **kwargs
    ) -> bool:
        """Create or update media record in DynamoDB"""
        if media_id not in self.allocated_media_ids:
            raise ValueError(f"Media ID {media_id} is not allocated for this profile")
        
        now = datetime.datetime.now(datetime.timezone.utc)
        now_iso = now.isoformat()
        now_tag = now.strftime("%Y%m%d%H%M%S")
        
        # Prepare media data
        media_data = {
            "mediaId": media_id,
            "profileId": self.profile_id,
            "userId": self.user_id,
            "s3Key": upload_s3_key,
            "status": status,
            "mediaBlob": media_blob,
            "mediaType": media_type,
            "size": size if size is not None else 0,
            "dimensions": dimensions,
            "duration": duration,
            "error_msg": error_msg if error_msg is not None else "",
            "createdAt": now_iso,
            "updatedAt": now_iso,
            **kwargs
        }
        
        # Validate and convert to MediaRecord
        try:
            validated_media_data = self.validate_media_record(media_data)
            media_data = msgspec.to_builtins(validated_media_data)
        except (ValueError, TypeError) as e:
            logger.error(f"Media data validation failed for {media_id}: {str(e)}")
            raise ValueError(f"Invalid media data: {str(e)}")
        
        try:
            self.table.put_item(
                Item={
                    "PK": f"PROFILE#{self.profile_id}",
                    "SK": f"MEDIA#{media_id}",
                    "GSI1PK": f"MEDIA#{media_id}",
                    "GSI1SK": f"PROFILE#{self.profile_id}",
                    "GSI2PK": f"TIME#{now_tag[:8]}",
                    "GSI2SK": f"{now_tag}#MEDIA#{media_id}",
                    "GSI3PK": "MEDIA#ALL",
                    "GSI3SK": f"MEDIA#{media_id}",
                    **media_data
                }
            )
            
            logger.info(f"Media record for {media_id} upserted successfully in profile {self.profile_id}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to upsert media record for {media_id}: {str(e)}")
            raise ValueError(f"Failed to upsert media record: {str(e)}")
    
    def update_media_status(self, media_id: str, status: MediaStatus, **kwargs) -> bool:
        """Update media record status and additional fields"""
        if media_id not in self.allocated_media_ids:
            raise ValueError(f"Media ID {media_id} is not allocated for this profile")
        
        try:
            update_expression_parts = ["#status = :status", "updatedAt = :updated_at"]
            expression_attribute_names = {"#status": "status"}
            expression_attribute_values = {
                ":status": status,
                ":updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
            
            # Add any additional fields to update
            for key, value in kwargs.items():
                if key not in ["PK", "SK", "mediaId", "profileId", "userId", "createdAt"]:
                    update_expression_parts.append(f"{key} = :{key}")
                    expression_attribute_values[f":{key}"] = value
            
            update_expression = "SET " + ", ".join(update_expression_parts)
            
            self.table.update_item(
                Key={"PK": f"PROFILE#{self.profile_id}", "SK": f"MEDIA#{media_id}"},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values
            )
            
            logger.info(f"Updated media {media_id} status to {status}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to update media {media_id} status: {str(e)}")
            raise ValueError(f"Failed to update media status: {str(e)}")
    
    def delete_media_record(self, media_id: str) -> bool:
        """Delete media record from DynamoDB"""
        if media_id not in self.allocated_media_ids:
            raise ValueError(f"Media ID {media_id} is not allocated for this profile")
        
        try:
            self.table.delete_item(
                Key={"PK": f"PROFILE#{self.profile_id}", "SK": f"MEDIA#{media_id}"}
            )
            
            # Also deactivate the media ID if it's active
            if media_id in self.active_media_ids:
                self.deactivate_media_id(media_id)
            
            logger.info(f"Deleted media record for {media_id}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete media record for {media_id}: {str(e)}")
            raise ValueError(f"Failed to delete media record: {str(e)}")
    
    def get_media_record(self, media_id: str) -> Optional[Dict[str, Any]]:
        """Get media record from DynamoDB"""
        if media_id not in self.allocated_media_ids:
            raise ValueError(f"Media ID {media_id} is not allocated for this profile")
        
        try:
            response = self.table.get_item(
                Key={"PK": f"PROFILE#{self.profile_id}", "SK": f"MEDIA#{media_id}"}
            )
            return response.get("Item")
            
        except ClientError as e:
            logger.error(f"Failed to get media record for {media_id}: {str(e)}")
            raise ValueError(f"Failed to get media record: {str(e)}")
    
    def list_active_media(self) -> List[Dict[str, Any]]:
        """List all active media records for the profile"""
        if not self.active_media_ids:
            return []
        
        try:
            # Use batch_get_item for better performance
            request_items = {
                self.table.name: {
                    "Keys": [
                        {"PK": f"PROFILE#{self.profile_id}", "SK": f"MEDIA#{media_id}"}
                        for media_id in self.active_media_ids
                    ]
                }
            }
            
            response = DynamoDBService.get_dynamodb().batch_get_item(RequestItems=request_items)
            return response.get("Responses", {}).get(self.table.name, [])
            
        except ClientError as e:
            logger.error(f"Failed to list active media: {str(e)}")
            raise ValueError(f"Failed to list active media: {str(e)}")
    
    def refresh_media_cache(self) -> None:
        """
        Refresh the in-memory cache by re-fetching data from DynamoDB
        Useful when GSI consistency issues occur
        """
        try:
            # Refresh profile data to get updated media IDs
            self.profile_data = self.get(self.profile_id)
            self.allocated_media_ids = self.profile_data.get("allocatedMediaIds", [])
            self.active_media_ids = self.profile_data.get("activeMediaIds", [])
            logger.info(f"Media cache refreshed for profile {self.profile_id}")
        except Exception as e:
            logger.error(f"Failed to refresh media cache for profile {self.profile_id}: {str(e)}")
    
    def set_media_error(self, media_id: str, error_message: str) -> bool:
        """
        Set media status to ERROR with error message
        
        Args:
            media_id: The media ID to update
            error_message: The error message to store
            
        Returns:
            bool: True if update was successful
        """
        return self.update_media_status(
            media_id, 
            MediaStatus.ERROR, 
            error_msg=error_message
        )
    
    def set_media_ready(self, media_id: str) -> bool:
        """
        Set media status to READY
        
        Args:
            media_id: The media ID to update
            
        Returns:
            bool: True if update was successful
        """
        return self.update_media_status(media_id, MediaStatus.READY)