"""
Shared settings for Vibe Lambda Functions

This module contains common configuration settings used by both auth and user services.
"""

from dataclasses import dataclass


@dataclass
class CoreSettings:
    record_id_length: int = 8
    max_profile_count: int = 5
