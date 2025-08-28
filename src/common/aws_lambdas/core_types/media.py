"""
Media type definitions for the user service

This module contains all media-related type definitions shared across services.
"""

from enum import Enum
from typing import Any, Dict, Optional

import msgspec


class MediaStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class MediaRecord(msgspec.Struct):
    """Media record validation using msgspec"""
    mediaId: str
    profileId: str
    userId: str
    s3Key: str
    status: MediaStatus = MediaStatus.PENDING
    mediaBlob: Dict[str, Any] = msgspec.field(default_factory=dict)
    mediaType: Optional[str] = None
    size: Optional[int] = None
    dimensions: Optional[Dict[str, int]] = None
    duration: Optional[float] = None
    error_msg: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

    def __post_init__(self):
        """Additional validation after struct creation"""
        import datetime
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Validate media ID format
        if not isinstance(self.mediaId, str):
            raise ValueError(f"Media ID must be a string, got {type(self.mediaId)}")
        
        # Validate profile ID format
        if not isinstance(self.profileId, str):
            raise ValueError(f"Profile ID must be a string, got {type(self.profileId)}")
        
        # Validate user ID format
        if not isinstance(self.userId, str):
            raise ValueError(f"User ID must be a string, got {type(self.userId)}")
        
        # Validate S3 key
        if not isinstance(self.s3Key, str) or not self.s3Key:
            raise ValueError("S3 key must be a non-empty string")

        # Validate file size if provided
        if self.size is not None and (not isinstance(self.size, int) or self.size <= 0):
            raise ValueError("File size must be a positive integer")
        
        # Validate dimensions if provided
        if self.dimensions is not None:
            if not isinstance(self.dimensions, dict):
                raise ValueError("Dimensions must be a dictionary")
            for key, value in self.dimensions.items():
                if not isinstance(value, int) or value <= 0:
                    raise ValueError(f"Dimension {key} must be a positive integer")
        
        # Validate duration if provided
        if self.duration is not None and (not isinstance(self.duration, (int, float)) or self.duration <= 0):
            raise ValueError("Duration must be a positive number")
        
        # Set timestamps if not provided
        if not self.createdAt:
            self.createdAt = now
        elif self.createdAt > now:
            raise ValueError(f"CreatedAt is in the future: {self.createdAt}")

        if not self.updatedAt:
            self.updatedAt = now
        elif self.updatedAt > now:
            raise ValueError(f"UpdatedAt is in the future: {self.updatedAt}")
