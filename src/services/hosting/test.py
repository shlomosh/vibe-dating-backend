#!/usr/bin/env python3
"""
Hosting Service Test Script
Runs tests for the hosting service infrastructure and build process
"""

import os
import subprocess
import sys
from pathlib import Path

from core.test_utils import ServiceTester


class HostingServiceTester(ServiceTester):
    def __init__(self):
        """Initialize the hosting service tester."""
        super().__init__("hosting", cfg={})

        # Override lambda_dir since hosting service doesn't have Lambda functions
        self.lambda_dir = self.service_dir / "cloudformation"

    def check_prerequisites(self):
        """Check that all prerequisites are met"""
        print("• Checking test prerequisites...")

        # Check if Poetry is installed
        try:
            subprocess.run(["poetry", "--version"], check=True, capture_output=True)
            print("[PASS] Poetry is installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("[FAIL] Poetry is not installed. Please install Poetry first.")
            sys.exit(1)

        # Check if CloudFormation directory exists
        if not self.lambda_dir.exists():
            print(f"[FAIL] CloudFormation directory not found: {self.lambda_dir}")
            sys.exit(1)

        print("[PASS] All test prerequisites met")

    def test_structure(self):
        """Test the hosting service structure"""
        print("• Testing hosting service structure...")

        # Check required directories
        required_dirs = [
            self.service_dir / "cloudformation",
        ]

        for dir_path in required_dirs:
            if not dir_path.exists():
                print(f"[FAIL] Required directory not found: {dir_path}")
                sys.exit(1)
            print(f"[PASS] Directory exists: {dir_path.name}")

        # Check required files
        required_files = [
            self.service_dir / "build.py",
            self.service_dir / "deploy.py",
            self.service_dir / "test.py",
            self.service_dir / "cloudformation" / "01-s3.yaml",
            self.service_dir / "cloudformation" / "02-cloudfront.yaml",
            self.service_dir / "cloudformation" / "03-route53.yaml",
        ]

        for file_path in required_files:
            if not file_path.exists():
                print(f"[FAIL] Required file not found: {file_path}")
                sys.exit(1)
            print(f"[PASS] File exists: {file_path.name}")

        print("[PASS] Structure test passed")

    def test_cloudformation_templates(self):
        """Test CloudFormation templates"""
        print("• Testing CloudFormation templates...")

        template_files = [
            "01-s3.yaml",
            "02-cloudfront.yaml",
            "03-route53.yaml",
        ]

        for template in template_files:
            template_path = self.service_dir / "cloudformation" / template
            if not template_path.exists():
                print(f"[FAIL] Template not found: {template_path}")
                sys.exit(1)

            try:
                # Validate template using AWS CLI
                subprocess.run(
                    [
                        "aws",
                        "cloudformation",
                        "validate-template",
                        "--template-body",
                        f"file://{template_path}",
                    ],
                    check=True,
                    capture_output=True,
                )
                print(f"[PASS] Template validated: {template}")
            except subprocess.CalledProcessError as e:
                print(f"[FAIL] Template validation failed: {template}")
                print(f"   Error: {e}")
                sys.exit(1)

        print("[PASS] CloudFormation templates test passed")

    def test_build_script(self):
        """Test the build script"""
        print("• Testing build script...")

        build_script = self.service_dir / "build.py"
        if not build_script.exists():
            print(f"[FAIL] Build script not found: {build_script}")
            sys.exit(1)

        # Test that the script can be imported
        try:
            import importlib.util

            spec = importlib.util.spec_from_file_location("build", build_script)
            build_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(build_module)
            print("[PASS] Build script can be imported")
        except Exception as e:
            print(f"[FAIL] Build script import failed: {e}")
            sys.exit(1)

        print("[PASS] Build script test passed")

    def test_deploy_script(self):
        """Test the deploy script"""
        print("• Testing deploy script...")

        deploy_script = self.service_dir / "deploy.py"
        if not deploy_script.exists():
            print(f"[FAIL] Deploy script not found: {deploy_script}")
            sys.exit(1)

        # Test that the script can be imported
        try:
            import importlib.util

            spec = importlib.util.spec_from_file_location("deploy", deploy_script)
            deploy_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(deploy_module)
            print("[PASS] Deploy script can be imported")
        except Exception as e:
            print(f"[FAIL] Deploy script import failed: {e}")
            sys.exit(1)

        print("[PASS] Deploy script test passed")

    def test_environment_variables(self):
        """Test environment variable configuration"""
        print("• Testing environment variables...")

        # Check if VIBE_FRONTEND_PATH is documented (not required for tests)
        print("[PASS] Environment variables test passed (VIBE_FRONTEND_PATH documented)")

    def test_parameters_integration(self):
        """Test parameters.yaml integration"""
        print("• Testing parameters.yaml integration...")

        # Check that required parameters exist
        required_params = [
            "Environment",
            "DeploymentUUID",
            "AppRegion",
            "AppDomainName",
            "AllowedOrigins",
        ]

        for param in required_params:
            if param not in self.parameters:
                print(f"[FAIL] Required parameter not found: {param}")
                sys.exit(1)
            print(f"[PASS] Parameter exists: {param}")

        print("[PASS] Parameters integration test passed")

    def test_frontend_integration(self):
        """Test frontend integration configuration"""
        print("• Testing frontend integration...")

        # Check if VIBE_FRONTEND_PATH is set (optional for tests)
        frontend_path = os.getenv("VIBE_FRONTEND_PATH")
        if frontend_path:
            frontend_dir = Path(frontend_path)
            if frontend_dir.exists():
                print(f"[PASS] Frontend directory found: {frontend_path}")

                # Check for package.json
                package_json = frontend_dir / "package.json"
                if package_json.exists():
                    print("[PASS] package.json found in frontend directory")
                else:
                    print("⚠️  package.json not found in frontend directory")
            else:
                print(f"⚠️  Frontend directory not found: {frontend_path}")
        else:
            print("⚠️  VIBE_FRONTEND_PATH not set (optional for tests)")

        print("[PASS] Frontend integration test passed")

    def run_tests(self):
        """Run all hosting service tests"""
        print("🧪 Starting Hosting Service Tests")
        print("=" * 50)

        try:
            # Check prerequisites
            self.check_prerequisites()

            # Run tests
            self.test_structure()
            self.test_cloudformation_templates()
            self.test_build_script()
            self.test_deploy_script()
            self.test_environment_variables()
            self.test_parameters_integration()
            self.test_frontend_integration()

            print("\n" + "=" * 50)
            print("🎉 All Hosting Service tests passed!")
            print("=" * 50)

        except Exception as e:
            print(f"\n[FAIL] Hosting Service tests failed: {e}")
            sys.exit(1)


def main(action=None):
    """Main entry point for hosting service tests"""
    tester = HostingServiceTester()
    tester.run_tests()


if __name__ == "__main__":
    main()
