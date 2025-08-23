#!/usr/bin/env python3
"""
Media Service Lambda Build Script
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

from core.build_utils import ServiceBuilder


class DataServiceBuilder(ServiceBuilder):
    def __init__(self):
        cfg = {
            "aws_layers": [],
            "aws_lambdas": [
                {
                    "name": "data_media_processing",
                    "extra_files": [
                        Path("src/common/aws_lambdas/core") / "settings.py",
                        Path("src/common/aws_lambdas/core") / "aws.py",
                        Path("src/common/aws_lambdas/core") / "manager.py",
                        Path("src/common/aws_lambdas/core_types") / "profile.py",
                    ],
                    "drop_prefixes": ["src/common/aws_lambdas"],
                }
            ],
        }
        super().__init__("data", cfg=cfg)


def main(action=None):
    builder = DataServiceBuilder()
    builder.build()


if __name__ == "__main__":
    main()
