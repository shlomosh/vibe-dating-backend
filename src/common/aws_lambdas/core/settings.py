"""
Shared settings for Vibe Lambda Functions

This module contains common configuration settings used by both auth and user services.
"""

from dataclasses import dataclass, field


@dataclass
class CoreSettings:
    record_id_length: int = 8
    max_profiles_count: int = 5
    max_medias_per_profile: int = 5
    media_max_file_size: int = 10485760
    media_allowed_formats: list[str] = field(default_factory=lambda: ["jpeg", "jpg", "png", "webp"])
    media_upload_expiry_hours: int = 1

