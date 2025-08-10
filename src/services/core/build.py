#!/usr/bin/env python3
"""
Core Service Lambda Build Script
"""

from core.build_utils import ServiceBuilder


class CoreServiceBuilder(ServiceBuilder):
    def __init__(self):
        cfg = {
            "aws_layers": [{"name": "core_layer", "requirements": "requirements.json"}],
            "aws_lambdas": [],
        }
        super().__init__("core", cfg=cfg)


def main(action=None):
    builder = CoreServiceBuilder()
    builder.build()


if __name__ == "__main__":
    main()
