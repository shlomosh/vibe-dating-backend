#!/usr/bin/env python3
"""
User Service Lambda Build Script
"""

from pathlib import Path

from core.build_utils import ServiceBuilder


class UserServiceBuilder(ServiceBuilder):
    def __init__(self):
        cfg = {
            "aws_layers": [{"name": "user_layer", "requirements": "requirements.txt"}],
            "aws_lambdas": [
                {
                    "name": "profiles",
                    "extra_files": [
                        Path("src/common/aws_lambdas/core") / "settings.py",
                        Path("src/common/aws_lambdas/core") / "auth_utils.py",
                        Path("src/common/aws_lambdas/core") / "rest_utils.py",
                        Path("src/common/aws_lambdas/core") / "profile_utils.py",
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