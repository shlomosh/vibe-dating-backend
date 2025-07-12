#!/usr/bin/env python3
"""
Poetry-based test script for Vibe Lambda Functions

This script runs tests for the Lambda functions using Poetry for dependency management.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
from src.core.core_utils import ServiceConstructor

os.environ["AWS_PROFILE"] = "vibe-dev"


class ServiceTester(ServiceConstructor):
    def __init__(self, service: str, cfg: Dict[str, Any], region: Optional[str] = None, environment: Optional[str] = None):
        """Initialize the service deployer."""
        super().__init__(service, cfg)
        
        self.lambda_dir = self.service_dir / "aws_lambdas"
        self.test_dir = self.lambda_dir / "test"
        
    def check_prerequisites(self):
        """Check that all prerequisites are met"""
        print("• Checking test prerequisites...")
        
        # Check if Poetry is installed
        try:
            subprocess.run(["poetry", "--version"], check=True, capture_output=True)
            print("✅ Poetry is installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Poetry is not installed. Please install Poetry first.")
            sys.exit(1)
            
        # Check if Lambda directory exists
        if not self.lambda_dir.exists():
            print(f"❌ Lambda directory not found: {self.lambda_dir}")
            sys.exit(1)
            
        # Check if test directory exists
        if not self.test_dir.exists():
            print(f"❌ Test directory not found: {self.test_dir}")
            sys.exit(1)
            
        print("✅ All test prerequisites met")
        
    def install_test_dependencies(self):
        """Install test dependencies using Poetry"""
        print("• Installing test dependencies...")
        
        try:
            # Install lambda dependencies for testing
            subprocess.run([
                "poetry", "install", "--with", "lambda"
            ], check=True, cwd=self.project_dir)
            print("✅ Test dependencies installed")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install test dependencies: {e}")
            sys.exit(1)

    def run_lambda_layer_test(self):
        """Run Lambda layer test"""
        test_file = self.test_dir / "test_layer.py"
        if not test_file.exists():
            print(f"⚠️  Lambda layer test not found: {test_file}. Skipping test.")
            return False

        print("\n• Running Lambda layer test...")
        try:
            result = subprocess.run([
                "poetry", "run", "python", str(test_file)
            ], check=True, cwd=self.project_dir, capture_output=True, text=True)
            
            print(result.stdout)
            print("✅ Lambda layer test passed")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Lambda layer test failed:")
            print(e.stdout)
            print(e.stderr)
            return False

    def run_structure_test(self):
        """Run code structure test"""
        test_file = self.test_dir / "test_structure.py"
        if not test_file.exists():
            print(f"⚠️  Structure test not found: {test_file}. Skipping test.")
            return False

        print("\n• Running code structure test...")        
        try:
            result = subprocess.run([
                "poetry", "run", "python", str(test_file)
            ], check=True, cwd=self.project_dir, capture_output=True, text=True)
            
            print(result.stdout)
            print("✅ Code structure test passed")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Code structure test failed:")
            print(e.stdout)
            print(e.stderr)
            return False

    def run_functional_test(self):
        """Run functional test"""
        test_file = self.test_dir / "test_functional.py"
        if not test_file.exists():
            print(f"⚠️  Functional test not found: {test_file}. Skipping test.")
            return False

        print("\n• Running functional test...")        
        try:
            result = subprocess.run([
                "poetry", "run", "python", str(test_file)
            ], check=True, cwd=self.project_dir, capture_output=True, text=True)
            
            print(result.stdout)
            print("✅ Functional test passed")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Functional test failed:")
            print(e.stdout)
            print(e.stderr)
            return False

    def run_linting(self):
        """Run code linting"""
        print("\n• Running code linting...")
        
        try:
            # Run black
            print("  Running Black...")
            subprocess.run([
                "poetry", "run", "black", "--check", str(self.service_dir)
            ], check=True, cwd=self.project_dir, capture_output=True)
            print("  ✅ Black passed")
            
            # Run isort
            print("  Running isort...")
            subprocess.run([
                "poetry", "run", "isort", "--check-only", str(self.service_dir)
            ], check=True, cwd=self.project_dir, capture_output=True)
            print("  ✅ isort passed")

            print("✅ All linting checks passed")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Linting failed: {e}")
            return False
            
    def test(self):
        """Main test process"""
        print("• Starting Poetry-based Lambda testing...")
        
        try:
            self.check_prerequisites()
            self.install_test_dependencies()
            
            # Run all tests
            tests = [
                ("Lambda Layer", self.run_lambda_layer_test),
                ("Code Structure", self.run_structure_test),
                ("Code Functionality", self.run_functional_test),
                ("Linting", self.run_linting),
            ]
            
            results = []
            for test_name, test_func in tests:
                try:
                    result = test_func()
                    results.append((test_name, result))
                except Exception as e:
                    print(f"❌ {test_name} test failed with exception: {e}")
                    results.append((test_name, False))
                    
            # Show summary
            print("\n• Test Summary:")
            passed = 0
            total = len(results)
            
            for test_name, result in results:
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"  {test_name}: {status}")
                if result:
                    passed += 1
                    
            print(f"\nResults: {passed}/{total} tests passed")
            
            if passed == total:
                print("✅ All tests passed!")
                return True
            else:
                print("❌ Some tests failed")
                return False
                
        except Exception as e:
            print(f"❌ Testing failed: {e}")
            return False
