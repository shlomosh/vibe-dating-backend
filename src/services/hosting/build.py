#!/usr/bin/env python3
"""
Hosting Service Build Script
Builds and uploads frontend assets to S3 for CloudFront hosting
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Add the src directory to the path so we can import from core
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.build_utils import ServiceBuilder


class HostingServiceBuilder(ServiceBuilder):
    def __init__(self):
        cfg = {
            "aws_layers": [],
            "aws_lambdas": [],
        }
        super().__init__("hosting", cfg=cfg)

        # Get frontend path from environment variable
        self.frontend_path = os.getenv("VIBE_FRONTEND_PATH")
        if not self.frontend_path:
            self.frontend_path = input("Enter vibe-dating-frontend Directory: ")

        self.frontend_path = Path(self.frontend_path)
        if not self.frontend_path.exists():
            raise ValueError(f"Frontend directory not found: {self.frontend_path}")

    def check_frontend_prerequisites(self):
        """Check that frontend build prerequisites are met"""
        print("• Checking frontend build prerequisites...")

        # Check if frontend directory exists
        if not self.frontend_path.exists():
            print(f"❌ Frontend directory not found: {self.frontend_path}")
            sys.exit(1)

        # Check if package.json exists
        package_json = self.frontend_path / "package.json"
        if not package_json.exists():
            print(f"❌ package.json not found in frontend directory: {package_json}")
            sys.exit(1)

        # Check if node_modules exists
        node_modules = self.frontend_path / "node_modules"
        if not node_modules.exists():
            print(
                "⚠️  node_modules not found. Run 'npm install' in frontend directory first."
            )
            print("   This script will attempt to install dependencies...")

        print("✅ Frontend prerequisites check completed")

    def install_frontend_dependencies(self):
        """Install frontend dependencies if needed"""
        print("• Installing frontend dependencies...")

        try:
            # Change to frontend directory
            original_cwd = os.getcwd()
            os.chdir(self.frontend_path)

            # Check if node_modules exists
            if not (self.frontend_path / "node_modules").exists():
                print("  Installing npm dependencies...")
                subprocess.run(["npm", "install"], check=True)
            else:
                print("  Dependencies already installed")

            # Restore original directory
            os.chdir(original_cwd)
            print("✅ Frontend dependencies installed")

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install frontend dependencies: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error installing frontend dependencies: {e}")
            sys.exit(1)

    def build_frontend(self):
        """Build frontend using Vite"""
        print("• Building frontend with Vite...")

        try:
            # Change to frontend directory
            original_cwd = os.getcwd()
            os.chdir(self.frontend_path)

            # Run Vite build
            print("  Running 'npm run build'...")
            subprocess.run(["npm", "run", "build"], check=True)

            # Restore original directory
            os.chdir(original_cwd)

            # Check if dist directory was created
            dist_dir = self.frontend_path / "dist"
            if not dist_dir.exists():
                print("❌ Frontend build failed: dist directory not found")
                sys.exit(1)

            print(f"✅ Frontend built successfully: {dist_dir}")

        except subprocess.CalledProcessError as e:
            print(f"❌ Frontend build failed: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error building frontend: {e}")
            sys.exit(1)

    def upload_frontend_assets(self):
        """Upload frontend assets to S3"""
        print("• Uploading frontend assets to S3...")

        try:
            # Get S3 bucket name from hosting stack
            from core.config_utils import ServiceConfigUtils

            config = ServiceConfigUtils(
                "hosting", region=self.region, environment=self.environment
            )
            stack_outputs = config.get_stacks_outputs()

            if "s3" in stack_outputs:
                bucket_name = stack_outputs["s3"].get("FrontendBucketName")
                if not bucket_name:
                    print("❌ Frontend bucket name not found in stack outputs")
                    sys.exit(1)
            else:
                # Fallback to constructing bucket name
                bucket_name = f"vibe-frontend-{self.environment}"

            # Upload dist directory to S3
            dist_dir = self.frontend_path / "dist"
            s3_path = f"s3://{bucket_name}/"

            print(f"  Uploading {dist_dir} to {s3_path}")
            subprocess.run(
                [
                    "aws",
                    "s3",
                    "sync",
                    str(dist_dir),
                    s3_path,
                    "--delete",  # Remove files that don't exist in source
                    "--cache-control",
                    "max-age=31536000,public",  # Cache for 1 year
                ],
                check=True,
            )

            print(f"✅ Frontend assets uploaded to S3: {s3_path}")

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to upload frontend assets: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error uploading frontend assets: {e}")
            sys.exit(1)

    def invalidate_cloudfront_cache(self):
        """Invalidate CloudFront cache after deployment"""
        print("• Invalidating CloudFront cache...")

        try:
            # Get CloudFront distribution ID from stack outputs
            from core.config_utils import ServiceConfigUtils

            config = ServiceConfigUtils(
                "hosting", region=self.region, environment=self.environment
            )
            stack_outputs = config.get_stacks_outputs()

            if "cloudfront" in stack_outputs:
                distribution_id = stack_outputs["cloudfront"].get(
                    "CloudFrontDistributionId"
                )
                if distribution_id:
                    print(f"  Invalidating CloudFront distribution: {distribution_id}")
                    subprocess.run(
                        [
                            "aws",
                            "cloudfront",
                            "create-invalidation",
                            "--distribution-id",
                            distribution_id,
                            "--paths",
                            "/*",
                        ],
                        check=True,
                    )
                    print("✅ CloudFront cache invalidation initiated")
                else:
                    print(
                        "⚠️  CloudFront distribution ID not found, skipping cache invalidation"
                    )
            else:
                print(
                    "⚠️  CloudFront stack outputs not found, skipping cache invalidation"
                )

        except subprocess.CalledProcessError as e:
            print(f"⚠️  Failed to invalidate CloudFront cache: {e}")
            # Don't exit on cache invalidation failure
        except Exception as e:
            print(f"⚠️  Error invalidating CloudFront cache: {e}")
            # Don't exit on cache invalidation failure

    def build(self, upload_to_s3: bool = True):
        """Main build process for hosting service"""
        print("• Starting Hosting Service build...")

        try:
            # Check frontend prerequisites
            self.check_frontend_prerequisites()

            # Install frontend dependencies
            self.install_frontend_dependencies()

            # Build frontend
            self.build_frontend()

            # Upload to S3 if requested
            if upload_to_s3:
                self.upload_frontend_assets()

                # Invalidate CloudFront cache
                self.invalidate_cloudfront_cache()

            print("\n✅ Hosting Service build completed successfully!")
            print(f"   Frontend built: {self.frontend_path / 'dist'}")
            if upload_to_s3:
                print("   Assets uploaded to S3")
                print("   CloudFront cache invalidation initiated")

        except Exception as e:
            print(f"❌ Hosting Service build failed: {e}")
            sys.exit(1)


def main(action=None):
    builder = HostingServiceBuilder()
    builder.build()


if __name__ == "__main__":
    main()
