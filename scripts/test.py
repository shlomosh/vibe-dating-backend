#!/usr/bin/env python3
"""
Poetry-based test script for Vibe Lambda Functions

This script runs tests for the Lambda functions using Poetry for dependency management.
"""

import os
import sys
import subprocess
from pathlib import Path

os.environ["AWS_PROFILE"] = "vibe-dev"
os.environ["AWS_REGION"] = "il-central-1"

class LambdaTester:
    """Tests Lambda functions using Poetry"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.lambda_dir = self.project_root / "src" / "services" / "auth" / "aws_lambdas"
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
            ], check=True, cwd=self.project_root)
            print("✅ Test dependencies installed")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install test dependencies: {e}")
            sys.exit(1)
            
    def run_lambda_layer_test(self):
        """Run Lambda layer test"""
        print("\n• Running Lambda layer test...")
        
        test_file = self.test_dir / "test_layer.py"
        if not test_file.exists():
            print(f"⚠️  Lambda layer test not found: {test_file}")
            return False
            
        try:
            result = subprocess.run([
                "poetry", "run", "python", str(test_file)
            ], check=True, cwd=self.project_root, capture_output=True, text=True)
            
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
        print("\n• Running code structure test...")
        
        test_file = self.test_dir / "test_structure.py"
        if not test_file.exists():
            print(f"⚠️  Structure test not found: {test_file}")
            return False
            
        try:
            result = subprocess.run([
                "poetry", "run", "python", str(test_file)
            ], check=True, cwd=self.project_root, capture_output=True, text=True)
            
            print(result.stdout)
            print("✅ Code structure test passed")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Code structure test failed:")
            print(e.stdout)
            print(e.stderr)
            return False
            
    def run_auth_test(self):
        """Run authentication test"""
        print("\n• Running authentication test...")
        
        test_file = self.test_dir / "test_auth.py"
        if not test_file.exists():
            print(f"⚠️  Authentication test not found: {test_file}")
            return False
            
        try:
            result = subprocess.run([
                "poetry", "run", "python", str(test_file)
            ], check=True, cwd=self.project_root, capture_output=True, text=True)
            
            print(result.stdout)
            print("✅ Authentication test passed")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Authentication test failed:")
            print(e.stdout)
            print(e.stderr)
            return False
            
    def run_unit_tests(self):
        """Run unit tests using pytest"""
        print("\n• Running unit tests...")
        
        tests_dir = self.project_root / "tests"
        if not tests_dir.exists():
            print(f"⚠️  Tests directory not found: {tests_dir}")
            return True  # Not a failure if no tests exist
            
        try:
            result = subprocess.run([
                "poetry", "run", "pytest", str(tests_dir), "-v"
            ], check=True, cwd=self.project_root, capture_output=True, text=True)
            
            print(result.stdout)
            print("✅ Unit tests passed")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Unit tests failed:")
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
                "poetry", "run", "black", "--check", str(self.project_root / "src")
            ], check=True, cwd=self.project_root, capture_output=True)
            print("  ✅ Black passed")
            
            # Run isort
            print("  Running isort...")
            subprocess.run([
                "poetry", "run", "isort", "--check-only", str(self.project_root / "src")
            ], check=True, cwd=self.project_root, capture_output=True)
            print("  ✅ isort passed")
            
            # Run mypy
            print("  Running mypy...")
            subprocess.run([
                "poetry", "run", "mypy", str(self.project_root / "src")
            ], check=True, cwd=self.project_root, capture_output=True)
            print("  ✅ mypy passed")
            
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
                ("Authentication", self.run_auth_test),
                ("Unit Tests", self.run_unit_tests),
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


def test_lambda_functions():
    """Entry point for Poetry script"""
    tester = LambdaTester()
    success = tester.test()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    test_lambda_functions() 