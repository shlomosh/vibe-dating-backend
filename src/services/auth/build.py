#!/usr/bin/env python3
"""
Auth Service Lambda Build Script
"""

from pathlib import Path

from core.build_utils import ServiceBuilder


class AuthServiceBuilder(ServiceBuilder):
    def __init__(self):
        cfg = {
            'aws_layers': [{
                "name": "auth_layer",
                "requirements": "requirements.txt"
            }],

            'aws_lambdas': [{
                "name": "telegram_auth",
                "extra_files": [
                    Path("core") / "auth_utils.py"
                ]
            }, {
                "name": "jwt_authorizer", 
                "extra_files": [
                    Path("core") / "auth_utils.py"
                ]
            }]
        }
        super().__init__("auth", cfg=cfg)

def main():
    builder = AuthServiceBuilder()      
    builder.build()


if __name__ == "__main__":
    main()
