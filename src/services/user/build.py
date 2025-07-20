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
                        Path("core") / "settings.py",
                        Path("core") / "auth_utils.py",
                        Path("core") / "rest_utils.py",
                        Path("core") / "profile_utils.py",
                    ],
                },
            ],
        }
        super().__init__("user", cfg=cfg)


def main(action=None):
    builder = UserServiceBuilder()
    builder.build()


if __name__ == "__main__":
    main()