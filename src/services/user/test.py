#!/usr/bin/env python3
"""
User Service Lambda Test Script
"""

import sys
from pathlib import Path

# Add the src directory to the path so we can import from core
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.test_utils import ServiceTester


class UserServiceTester(ServiceTester):
    def __init__(self):
        super().__init__("user", cfg={})

    def test_cloudformation_templates(self):
        """Test CloudFormation templates"""
        print("• Testing CloudFormation templates...")

        templates = ["01-s3.yaml", "02-lambda.yaml", "03-apigateway.yaml"]
        for template in templates:
            template_path = self.service_dir / "cloudformation" / template
            if not template_path.exists():
                print(f"[FAIL] Template not found: {template_path}")
                sys.exit(1)

        print("[PASS] All CloudFormation templates found")

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

    def test(self):
        """Run all tests"""
        print("🧪 Testing User Service...")

        self.test_cloudformation_templates()
        self.test_build_script()
        self.test_deploy_script()

        print("✅ All User Service tests passed!")


def main(action=None):
    tester = UserServiceTester()
    tester.test()


if __name__ == "__main__":
    main()
