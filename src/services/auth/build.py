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
                    "name": "auth_platform",
                    "extra_files": [
                        Path("src/common/aws_lambdas/core") / "settings.py",
                        Path("src/common/aws_lambdas/core") / "auth_utils.py",
                        Path("src/common/aws_lambdas/core") / "rest_utils.py",
                        Path("src/common/aws_lambdas/core") / "dynamo_utils.py",
                    ],
                    "drop_prefixes": ["src/common/aws_lambdas"],
                },
                {
                    "name": "auth_jwt_authorizer",
                    "extra_files": [
                        Path("src/common/aws_lambdas/core") / "settings.py",
                        Path("src/common/aws_lambdas/core") / "auth_utils.py",
                        Path("src/common/aws_lambdas/core") / "rest_utils.py",
                        Path("src/common/aws_lambdas/core") / "dynamo_utils.py",
                    ],
                    "drop_prefixes": ["src/common/aws_lambdas"],
                },
            ],
        }
        super().__init__("auth", cfg=cfg)


def main(action=None):
    builder = AuthServiceBuilder()
    builder.build()


if __name__ == "__main__":
    main()
