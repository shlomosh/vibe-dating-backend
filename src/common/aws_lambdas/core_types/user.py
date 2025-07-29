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
    profileIds: List[str] = msgspec.field(default_factory=list)
    status: UserStatus = UserStatus.ACTIVE
    statusData: UserStatusData = msgspec.field(default_factory=UserStatusData)
    preferences: Dict[str, Any] = msgspec.field(default_factory=dict)
    lastActiveAt: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    loginCount: int = 0
