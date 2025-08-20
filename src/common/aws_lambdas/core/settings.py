"""
Shared settings for Vibe Lambda Functions

This module contains common configuration settings used by both auth and user services.
"""

from dataclasses import dataclass


@dataclass
class CoreSettings:
    record_id_length: int = 8
    max_profiles_count: int = 5
    max_medias_per_profile: int = 5
