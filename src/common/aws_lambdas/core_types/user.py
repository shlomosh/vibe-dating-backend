"""
User type definitions for the user service

This module contains all user-related type definitions shared across services.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

import msgspec


class UserStatus(str, Enum):
    ACTIVE = "active"
    BANNED = "banned"


class UserStatusData(msgspec.Struct):
    banFrom: Optional[str] = None
    banTo: Optional[str] = None
    banReason: Optional[str] = None
    banHistory: Optional[List[Dict[str, Any]]] = None
    banCount: int = 0
    reportedCount: int = 0


class UserRecord(msgspec.Struct):
    """User record validation using msgspec"""
    platform: str
    platformId: str
    platformMetadata: Dict[str, Any] = msgspec.field(default_factory=dict)
    allocatedProfileIds: List[str] = msgspec.field(default_factory=list)
    activeProfileIds: List[str] = msgspec.field(default_factory=list)
    status: UserStatus = UserStatus.ACTIVE
    statusData: UserStatusData = msgspec.field(default_factory=UserStatusData)
    preferences: Dict[str, Any] = msgspec.field(default_factory=dict)
    lastActiveAt: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    loginCount: int = 0

    def __post_init__(self):
        """Additional validation after struct creation"""
        import datetime
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        if self.allocatedProfileIds:
            expected_length = 8  # CoreSettings().record_id_length
            for profile_id in self.allocatedProfileIds:
                if not isinstance(profile_id, str):
                    raise ValueError(f"Profile ID must be a string, got {type(profile_id)}")
                if len(profile_id) != expected_length:
                    raise ValueError(f"Profile ID must be {expected_length} characters long, got {len(profile_id)} for '{profile_id}'")

        if self.activeProfileIds:
            for profile_id in self.activeProfileIds:
                if profile_id not in self.allocatedProfileIds:
                    raise ValueError(f"Profile ID is not allocated: {profile_id}")

        if not self.createdAt:
            self.createdAt = now
        elif self.createdAt > now:
            raise ValueError(f"CreatedAt is in the future: {self.createdAt}")

        if not self.updatedAt:
            self.updatedAt = now
        elif self.updatedAt > now:
            raise ValueError(f"UpdatedAt is in the future: {self.updatedAt}")

        if not self.lastActiveAt:
            self.lastActiveAt = now
        elif self.lastActiveAt > now:
            raise ValueError(f"LastActiveAt is in the future: {self.lastActiveAt}")

        if self.statusData.banFrom and self.statusData.banFrom > now:
            raise ValueError(f"BanFrom is in the future: {self.statusData.banFrom}")
