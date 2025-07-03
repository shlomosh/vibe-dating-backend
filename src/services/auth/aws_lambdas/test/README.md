# Vibe Authentication Lambda Tests

This directory contains test files for the Vibe authentication Lambda functions.

## Test Files

### `test_layer.py`
Tests the Lambda layer functionality and dependencies.
- **Purpose**: Verifies that all required Python packages are available
- **Tests**: 
  - Package imports (PyJWT, boto3, requests, urllib3, python-dateutil)
  - Python path configuration
  - JWT functionality
  - Boto3 functionality

### `test_structure.py`
Tests the code structure and import functionality.
- **Purpose**: Verifies that the modular code structure works correctly
- **Tests**:
  - Auth utilities import
  - JWT authorizer function import
  - Telegram auth function import
  - Auth functions functionality

### `test_auth.py`
Tests the authentication functionality.
- **Purpose**: Verifies that authentication functions work correctly
- **Tests**:
  - Telegram data verification
  - User ID generation
  - JWT token generation and validation
  - DynamoDB operations (mocked)

## Running Tests

Run tests from the lambda directory:

```bash
cd src/services/auth/lambda

# Run all tests
python test/test_layer.py
python test/test_structure.py
python test/test_auth.py

# Or run from the test directory
cd test
python test_layer.py
python test_structure.py
python test_auth.py
```

## Test Dependencies

Tests require the following to be available:
- Python 3.11+
- Required packages (installed via Lambda layer)
- Proper directory structure
- Environment variables (for some tests)

## Test Environment

Tests are designed to run in the local development environment and verify:
- Code structure integrity
- Import functionality
- Lambda layer dependencies
- Authentication logic

## Expected Output

All tests should output:
- ✓ PASS for successful tests
- ✗ FAIL for failed tests
- Summary of all test results
- Clear error messages for debugging 