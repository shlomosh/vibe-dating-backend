#!/usr/bin/env python3
"""
Core Service Test Script
Runs tests for the core service infrastructure and shared components
"""

import os
import subprocess
import sys
from pathlib import Path

# Add the src directory to the path so we can import from core
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.test_utils import ServiceTester


class CoreServiceTester(ServiceTester):
    def __init__(self):
        """Initialize the core service tester."""
        super().__init__("core", cfg={})

        # Override lambda_dir since core service doesn't have Lambda functions
        self.lambda_dir = self.service_dir / "aws_lambdas"

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

        # Check if aws_lambdas directory exists
        if not self.lambda_dir.exists():
            print(f"[FAIL] aws_lambdas directory not found: {self.lambda_dir}")
            sys.exit(1)

        print("[PASS] All test prerequisites met")

    def test_structure(self):
        """Test the core service structure"""
        print("• Testing core service structure...")

        # Check required directories
        required_dirs = [
            self.service_dir / "aws_lambdas",
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
            self.service_dir / "aws_lambdas" / "requirements.json",
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
            "02-dynamodb.yaml",
            "03-iam.yaml",
            "04-lambda.yaml",
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

    def test_requirements_json(self):
        """Test requirements.json format"""
        print("• Testing requirements.json...")

        requirements_file = self.service_dir / "aws_lambdas" / "requirements.json"
        if not requirements_file.exists():
            print(f"[FAIL] requirements.json not found: {requirements_file}")
            sys.exit(1)

        try:
            import json
            with open(requirements_file, 'r') as f:
                requirements = json.load(f)
            
            # Check that it's a valid JSON object
            if not isinstance(requirements, dict):
                print("[FAIL] requirements.json is not a valid JSON object")
                sys.exit(1)
            
            # Check for required packages
            required_packages = ["PyJWT", "python-dateutil", "msgspec"]
            for package in required_packages:
                if not any(pkg.startswith(package) for pkg in requirements.keys()):
                    print(f"[FAIL] Required package not found: {package}")
                    sys.exit(1)
            
            print("[PASS] requirements.json is valid")
        except json.JSONDecodeError as e:
            print(f"[FAIL] requirements.json is not valid JSON: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"[FAIL] Error reading requirements.json: {e}")
            sys.exit(1)

        print("[PASS] requirements.json test passed")

    def test_parameters_integration(self):
        """Test parameters.yaml integration"""
        print("• Testing parameters.yaml integration...")

        # Check that required parameters exist
        required_params = [
            "Environment",
            "DeploymentUUID",
            "ApiRegion",
        ]

        for param in required_params:
            if param not in self.parameters:
                print(f"[FAIL] Required parameter not found: {param}")
                sys.exit(1)
            print(f"[PASS] Parameter exists: {param}")

        print("[PASS] Parameters integration test passed")

    def test_shared_core_modules(self):
        """Test that shared core modules are accessible"""
        print("• Testing shared core modules...")

        try:
            # Add the common aws_lambdas directory to the path
            common_aws_lambdas_dir = self.project_dir / "src" / "common" / "aws_lambdas"
            sys.path.insert(0, str(common_aws_lambdas_dir))
            
            # Test importing core modules
            from core.aws import DynamoDBService
            from core.auth_utils import extract_user_id_from_context
            from core.profile_utils import ProfileManager
            from core.rest_utils import generate_response
            from core.settings import CoreSettings
            from core_types.profile import ProfileRecord
            from core_types.user import UserRecord
            
            print("[PASS] All core modules can be imported")
        except ImportError as e:
            print(f"[FAIL] Failed to import core module: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"[FAIL] Error testing core modules: {e}")
            sys.exit(1)

        print("[PASS] Shared core modules test passed")

    def run_tests(self):
        """Run all core service tests"""
        print("🧪 Starting Core Service Tests")
        print("=" * 50)

        try:
            # Check prerequisites
            self.check_prerequisites()

            # Run tests
            self.test_structure()
            self.test_cloudformation_templates()
            self.test_build_script()
            self.test_deploy_script()
            self.test_requirements_json()
            self.test_parameters_integration()
            self.test_shared_core_modules()

            print("\n" + "=" * 50)
            print("🎉 All Core Service tests passed!")
            print("=" * 50)

        except Exception as e:
            print(f"\n[FAIL] Core Service tests failed: {e}")
            sys.exit(1)


def main(action=None):
    """Main entry point for core service tests"""
    tester = CoreServiceTester()
    tester.run_tests()


if __name__ == "__main__":
    main() 