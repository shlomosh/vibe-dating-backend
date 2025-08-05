#!/usr/bin/env python3
"""
Test the structure and imports of the core service
"""

import os
import sys
import traceback
from pathlib import Path

# Add the lambda directories to the path
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
service_aws_lambdas_dir = project_root / "src" / "services" / "core" / "aws_lambdas"
common_aws_lambdas_dir = project_root / "src" / "common" / "aws_lambdas"

print(f"Adding {service_aws_lambdas_dir} to sys.path")
sys.path.insert(0, str(service_aws_lambdas_dir))
print(f"Adding {common_aws_lambdas_dir} to sys.path")
sys.path.insert(0, str(common_aws_lambdas_dir))


def test_service_structure():
    """Test that the core service has proper structure"""
    current_dir = Path(__file__).parent.parent.parent

    required_files = [
        "build.py",
        "deploy.py",
        "test.py",
        "aws_lambdas/requirements.json",
    ]

    passed = 0
    failed = 0

    print("Testing core service structure...")
    for file_name in required_files:
        file_path = current_dir / file_name
        if file_path.exists():
            print(f"✓ {file_name}")
            passed += 1
        else:
            print(f"✗ {file_name}: File does not exist")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_core_imports():
    """Test that core modules can be imported"""
    core_modules = [
        "core.aws",
        "core.auth_utils",
        "core.profile_utils",
        "core.rest_utils",
        "core.settings",
        "core.manager",
        "core.platform",
        "core.user_utils",
    ]

    passed = 0
    failed = 0

    print("\nTesting core module imports...")
    for module in core_modules:
        try:
            __import__(module)
            print(f"✓ {module}")
            passed += 1
        except Exception as e:
            print(f"✗ {module}: {e}")
            traceback.print_exc()
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_core_types_imports():
    """Test that core types can be imported"""
    core_types = [
        "core_types.profile",
        "core_types.user",
    ]

    passed = 0
    failed = 0

    print("\nTesting core types imports...")
    for module in core_types:
        try:
            __import__(module)
            print(f"✓ {module}")
            passed += 1
        except Exception as e:
            print(f"✗ {module}: {e}")
            traceback.print_exc()
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def main():
    """Run all structure tests"""
    print("Core Service Structure Tests")
    print("=" * 40)

    all_passed = True

    # Test service structure
    all_passed &= test_service_structure()

    # Test core imports
    all_passed &= test_core_imports()

    # Test core types imports
    all_passed &= test_core_types_imports()

    print("\n" + "=" * 40)
    if all_passed:
        print("All structure tests PASSED")
        return 0
    else:
        print("Some structure tests FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 