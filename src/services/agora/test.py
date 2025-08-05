#!/usr/bin/env python3
"""
Agora Service Test Script
Runs tests for the agora service infrastructure and real-time communication components
"""

import os
import subprocess
import sys
from pathlib import Path

# Add the src directory to the path so we can import from core
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.test_utils import ServiceTester


class AgoraServiceTester(ServiceTester):
    def __init__(self):
        """Initialize the agora service tester."""
        super().__init__("agora", cfg={})

        # Override lambda_dir since agora service doesn't have Lambda functions yet
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
        """Test the agora service structure"""
        print("• Testing agora service structure...")

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
            self.service_dir / "test.py",
            self.service_dir / "cloudformation" / "template.yaml",
            self.service_dir / "cloudformation" / "parameters.yaml",
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
            "template.yaml",
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

    def test_agora_integration_plan(self):
        """Test that Agora integration is properly planned"""
        print("• Testing Agora integration plan...")

        # Check if Agora-related parameters are documented
        agora_params = [
            "AgoraAppId",
            "AgoraAppCertificate",
            "AgoraApiKey",
        ]

        for param in agora_params:
            if param in self.parameters:
                print(f"[PASS] Agora parameter configured: {param}")
            else:
                print(f"⚠️  Agora parameter not configured: {param} (optional for development)")

        print("[PASS] Agora integration plan test passed")

    def run_tests(self):
        """Run all agora service tests"""
        print("🧪 Starting Agora Service Tests")
        print("=" * 50)

        try:
            # Check prerequisites
            self.check_prerequisites()

            # Run tests
            self.test_structure()
            self.test_cloudformation_templates()
            self.test_parameters_integration()
            self.test_agora_integration_plan()

            print("\n" + "=" * 50)
            print("🎉 All Agora Service tests passed!")
            print("=" * 50)

        except Exception as e:
            print(f"\n[FAIL] Agora Service tests failed: {e}")
            sys.exit(1)


def main(action=None):
    """Main entry point for agora service tests"""
    tester = AgoraServiceTester()
    tester.run_tests()


if __name__ == "__main__":
    main() 