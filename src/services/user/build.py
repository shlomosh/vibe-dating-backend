#!/usr/bin/env python3
"""
User Service Lambda Build Script
"""

from pathlib import Path

from core.build_utils import ServiceBuilder


class UserServiceBuilder(ServiceBuilder):
    def __init__(self):
        cfg = {
            "aws_layers": [],
            "aws_lambdas": [
                {
                    "name": "user_profile_mgmt",
                    "extra_files": [
                        Path("src/common/aws_lambdas/core") / "aws.py",
                        Path("src/common/aws_lambdas/core") / "manager.py",
                        Path("src/common/aws_lambdas/core") / "settings.py",
                        Path("src/common/aws_lambdas/core") / "auth_utils.py",
                        Path("src/common/aws_lambdas/core") / "rest_utils.py",
                        Path("src/common/aws_lambdas/core") / "profile_utils.py",
                        Path("src/common/aws_lambdas/core_types") / "profile.py",
                    ],
                    "drop_prefixes": ["src/common/aws_lambdas"],
                },
                {
                    "name": "user_media_mgmt",
                    "extra_files": [
                        Path("src/common/aws_lambdas/core") / "aws.py",
                        Path("src/common/aws_lambdas/core") / "manager.py",
                        Path("src/common/aws_lambdas/core") / "settings.py",
                        Path("src/common/aws_lambdas/core") / "auth_utils.py",
                        Path("src/common/aws_lambdas/core") / "rest_utils.py",
                        Path("src/common/aws_lambdas/core") / "user_utils.py",
                        Path("src/common/aws_lambdas/core") / "profile_utils.py",
                        Path("src/common/aws_lambdas/core") / "media_utils.py",
                        Path("src/common/aws_lambdas/core_types") / "user.py",
                        Path("src/common/aws_lambdas/core_types") / "profile.py",
                        Path("src/common/aws_lambdas/core_types") / "media.py",
                    ],
                    "drop_prefixes": ["src/common/aws_lambdas"],
                },
                {
                    "name": "user_media_processing",
                    "extra_files": [
                        Path("src/common/aws_lambdas/core") / "aws.py",
                        Path("src/common/aws_lambdas/core") / "manager.py",
                        Path("src/common/aws_lambdas/core") / "settings.py",
                        Path("src/common/aws_lambdas/core") / "auth_utils.py",
                        Path("src/common/aws_lambdas/core") / "rest_utils.py",
                        Path("src/common/aws_lambdas/core") / "user_utils.py",
                        Path("src/common/aws_lambdas/core") / "profile_utils.py",
                        Path("src/common/aws_lambdas/core") / "media_utils.py",
                        Path("src/common/aws_lambdas/core_types") / "user.py",
                        Path("src/common/aws_lambdas/core_types") / "profile.py",
                        Path("src/common/aws_lambdas/core_types") / "media.py",
                    ],
                    "drop_prefixes": ["src/common/aws_lambdas"],
                },                
            ],
        }
        super().__init__("user", cfg=cfg)


def main(action=None):
    builder = UserServiceBuilder()
    builder.build()


if __name__ == "__main__":
    main()
