"""
Profile type definitions for the user service

This module contains all profile-related type definitions shared across services.
"""

from enum import Enum
from typing import List, Optional

import msgspec


class SexualPosition(str, Enum):
    BOTTOM = "bottom"
    VERS_BOTTOM = "versBottom"
    VERS = "vers"
    VERS_TOP = "versTop"
    TOP = "top"
    SIDE = "side"
    BLOWER = "blower"
    BLOWIE = "blowie"


class BodyType(str, Enum):
    PETITE = "petite"
    SLIM = "slim"
    AVERAGE = "average"
    FIT = "fit"
    MUSCULAR = "muscular"
    STOCKY = "stocky"
    CHUBBY = "chubby"
    LARGE = "large"


class SexualityType(str, Enum):
    GAY = "gay"
    BISEXUAL = "bisexual"
    CURIOUS = "curious"
    TRANS = "trans"
    FLUID = "fluid"


class HostingType(str, Enum):
    HOST_AND_TRAVEL = "hostAndTravel"
    HOST_ONLY = "hostOnly"
    TRAVEL_ONLY = "travelOnly"


class TravelDistanceType(str, Enum):
    NONE = "none"
    BLOCK = "block"
    NEIGHBOURHOOD = "neighbourhood"
    CITY = "city"
    METROPOLITAN = "metropolitan"
    STATE = "state"


class EggplantSizeType(str, Enum):
    SMALL = "small"
    AVERAGE = "average"
    LARGE = "large"
    EXTRA_LARGE = "extraLarge"
    GIGANTIC = "gigantic"


class PeachShapeType(str, Enum):
    SMALL = "small"
    AVERAGE = "average"
    BUBBLE = "bubble"
    SOLID = "solid"
    LARGE = "large"


class HealthPracticesType(str, Enum):
    CONDOMS = "condoms"
    BB = "bb"
    CONDOMS_OR_BB = "condomsOrBb"
    NO_PENETRATIONS = "noPenetrations"


class HivStatusType(str, Enum):
    NEGATIVE = "negative"
    POSITIVE = "positive"
    POSITIVE_UNDETECTABLE = "positiveUndetectable"


class PreventionPracticesType(str, Enum):
    NONE = "none"
    PREP = "prep"
    DOXYPEP = "doxypep"
    PREP_AND_DOXYPEP = "prepAndDoxypep"


class MeetingTimeType(str, Enum):
    NOW = "now"
    TODAY = "today"
    WHENEVER = "whenever"


class ChatStatusType(str, Enum):
    ONLINE = "online"
    BUSY = "busy"
    OFFLINE = "offline"


class ProfileRecord(msgspec.Struct):
    """Profile record validation using msgspec - matches frontend interface"""
    nickName: Optional[str] = None
    aboutMe: Optional[str] = None
    age: Optional[str] = None
    sexualPosition: Optional[SexualPosition] = None
    bodyType: Optional[BodyType] = None
    eggplantSize: Optional[EggplantSizeType] = None
    peachShape: Optional[PeachShapeType] = None
    healthPractices: Optional[HealthPracticesType] = None
    hivStatus: Optional[HivStatusType] = None
    preventionPractices: Optional[PreventionPracticesType] = None
    hosting: Optional[HostingType] = None
    travelDistance: Optional[TravelDistanceType] = None
    allocatedMediaIds: List[str] = msgspec.field(default_factory=list)
    activeMediaIds: List[str] = msgspec.field(default_factory=list)

    def __post_init__(self):
        """Additional validation after struct creation"""
        self.aboutMe = self.aboutMe.strip() if self.aboutMe is not None else None
        self.nickName = self.nickName.strip() if self.nickName is not None else None

        if self.allocatedMediaIds:
            expected_length = 8  # CoreSettings().record_id_length
            for media_id in self.allocatedMediaIds:
                if not isinstance(media_id, str):
                    raise ValueError(f"Media ID must be a string, got {type(media_id)}")
                if len(media_id) != expected_length:
                    raise ValueError(f"Media ID must be {expected_length} characters long, got {len(media_id)} for '{media_id}'")

        if self.activeMediaIds:
            for media_id in self.activeMediaIds:
                if media_id not in self.allocatedMediaIds:
                    raise ValueError(f"Media ID is not allocated: {media_id}")
