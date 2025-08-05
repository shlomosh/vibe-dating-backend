#!/usr/bin/env python3
"""
Test the structure and imports of the user service Lambda functions
"""

import os
import sys
import traceback
from pathlib import Path

# Add the lambda directories to the path
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
service_aws_lambdas_dir = project_root / "src" / "services" / "user" / "aws_lambdas"
common_aws_lambdas_dir = project_root / "src" / "common" / "aws_lambdas"

print(f"Adding {service_aws_lambdas_dir} to sys.path")
sys.path.insert(0, str(service_aws_lambdas_dir))
print(f"Adding {common_aws_lambdas_dir} to sys.path")
sys.path.insert(0, str(common_aws_lambdas_dir))


def test_lambda_structure():
    """Test that the profile management Lambda function directory exists and has proper structure"""
    current_dir = Path(__file__).parent.parent

    lambda_functions = ["user_profile_mgmt"]

    passed = 0
    failed = 0

    print("Testing Lambda function structure...")

    for func_name in lambda_functions:
        func_dir = current_dir / func_name
        lambda_file = func_dir / "lambda_function.py"
        init_file = func_dir / "__init__.py"

        if not func_dir.exists():
            print(f"✗ {func_name}: Directory does not exist")
            failed += 1
            continue

        if not lambda_file.exists():
            print(f"✗ {func_name}: lambda_function.py does not exist")
            failed += 1
            continue

        if not init_file.exists():
            print(f"✗ {func_name}: __init__.py does not exist")
            failed += 1
            continue

        print(f"✓ {func_name}: Structure correct")
        passed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_lambda_imports():
    """Test that the profile management Lambda function module can be imported"""
    current_dir = Path(__file__).parent.parent

    # Add the parent directory to Python path for imports
    sys.path.insert(0, str(current_dir))

    lambda_modules = [("user_profile_mgmt", "user_profile_mgmt.lambda_function")]

    passed = 0
    failed = 0

    print("\nTesting Lambda function imports...")

    for func_name, module_name in lambda_modules:
        try:
            module = __import__(module_name, fromlist=[""])

            # Check if lambda_handler function exists
            if hasattr(module, "lambda_handler"):
                print(f"✓ {func_name}: Import successful and lambda_handler found")
                passed += 1
            else:
                print(f"✗ {func_name}: lambda_handler function not found")
                failed += 1

        except Exception as e:
            print(f"✗ {func_name}: Import failed - {e}")
            traceback.print_exc()
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_core_structure():
    """Test that core modules exist and have proper structure"""
    project_root = Path(__file__).parent.parent.parent.parent.parent.parent
    core_dir = project_root / "src" / "common" / "aws_lambdas" / "core"

    core_files = [
        "__init__.py",
        "auth_utils.py",
        "profile_utils.py",
        "rest_utils.py",
        "settings.py",
        "aws.py",
        "manager.py",
        "platform.py",
        "user_utils.py",
    ]

    passed = 0
    failed = 0

    print("\nTesting core module structure...")

    if not core_dir.exists():
        print("✗ Core directory does not exist")
        return False

    for core_file in core_files:
        file_path = core_dir / core_file
        if file_path.exists():
            print(f"✓ core/{core_file}")
            passed += 1
        else:
            print(f"✗ core/{core_file}: File does not exist")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def main():
    """Run all structure tests"""
    print("User Service Structure Tests")
    print("=" * 40)

    all_passed = True

    # Test Lambda structure
    all_passed &= test_lambda_structure()

    # Test Lambda imports
    all_passed &= test_lambda_imports()

    # Test core structure
    all_passed &= test_core_structure()

    print("\n" + "=" * 40)
    if all_passed:
        print("All structure tests PASSED")
        return 0
    else:
        print("Some structure tests FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
