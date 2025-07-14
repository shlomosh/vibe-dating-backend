#!/usr/bin/env python3
"""
Auth Service Lambda Build Script
"""

from pathlib import Path

from core.build_utils import ServiceBuilder


class AuthServiceBuilder(ServiceBuilder):
    def __init__(self):
        cfg = {
            "aws_layers": [{"name": "auth_layer", "requirements": "requirements.txt"}],
            "aws_lambdas": [
                {
                    "name": "platform_auth",
                    "extra_files": [
                        Path("core") / "auth_utils.py",
                        Path("core") / "rest_utils.py",
                        Path("core") / "dynamo_utils.py",
                    ],
                },
                {
                    "name": "user_jwt_authorizer",
                    "extra_files": [
                        Path("core") / "auth_utils.py",
                        Path("core") / "rest_utils.py",
                        Path("core") / "dynamo_utils.py",
                    ],
                },
            ],
        }
        super().__init__("auth", cfg=cfg)


def main(action=None):
    builder = AuthServiceBuilder()
    builder.build()


if __name__ == "__main__":
    main()
