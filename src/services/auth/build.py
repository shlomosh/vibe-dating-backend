#!/usr/bin/env python3
"""
Auth Service Lambda Build Script

This script builds Lambda layers and function packages specifically for the auth service
using the common build utilities.
"""

import sys

from core.build_utils import ServiceBuilder


class AuthServiceBuilder(ServiceBuilder):
    """Builds Lambda packages for the auth service"""
    
    def __init__(self):
        super().__init__()
        self.auth_service_dir = self.project_root / "src" / "services" / "auth"
        self.lambda_dir = self.auth_service_dir / "aws_lambdas"
        self.layer_dir = self.build_dir / "layer"
        
    def build(self):
        """Main build process for auth service"""
        print("• Starting Auth Service Lambda build...")
        
        try:
            # Clean and prepare build directory
            self.clean_build_directory()
            
            # Install dependencies to layer
            requirements_file = self.lambda_dir / "requirements.txt"
            self.install_dependencies_to_layer(requirements_file, self.layer_dir)
            
            # Copy auth service code
            self.copy_service_code(
                self.lambda_dir,
                self.build_dir,
                exclude_patterns=["__pycache__", "*.pyc", ".pytest_cache", "test"]
            )
            
            # Create Lambda layer
            layer_zip = self.build_dir / "vibe_base_layer.zip"
            self.create_lambda_layer(self.layer_dir, layer_zip)
            
            # Create function packages
            packages = []
            
            # Telegram auth function
            telegram_func_dir = self.build_dir / "telegram_auth"
            if telegram_func_dir.exists():
                telegram_zip = self.build_dir / "telegram_auth.zip"
                additional_files = [self.build_dir / "core" / "auth_utils.py"]
                self.create_function_package(
                    telegram_func_dir,
                    telegram_zip,
                    additional_files
                )
                packages.append(telegram_zip)
            
            # JWT authorizer function
            jwt_func_dir = self.build_dir / "jwt_authorizer"
            if jwt_func_dir.exists():
                jwt_zip = self.build_dir / "jwt_authorizer.zip"
                additional_files = [self.build_dir / "core" / "auth_utils.py"]
                self.create_function_package(
                    jwt_func_dir,
                    jwt_zip,
                    additional_files
                )
                packages.append(jwt_zip)
            
            # Add layer to packages list for summary
            packages.insert(0, layer_zip)
            
            # Print build summary
            self.print_build_summary(packages)
            
        except Exception as e:
            print(f"❌ Auth service build failed: {e}")
            sys.exit(1)


def main():
    """Entry point for the auth service build"""
    builder = AuthServiceBuilder()
    builder.build()


if __name__ == "__main__":
    main() 