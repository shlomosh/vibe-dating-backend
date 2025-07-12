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
  - DateUtil functionality

### `test_structure.py`
Tests the code structure and import functionality.
- **Purpose**: Verifies that the modular code structure works correctly
- **Tests**:
  - Core auth utilities import
  - Platform auth function import
  - JWT authorizer function import
  - Telegram module import
  - Core utilities import
  - Auth functions functionality

### `test_auth.py`
Tests the authentication functionality.
- **Purpose**: Verifies that authentication functions work correctly
- **Tests**:
  - User ID generation using UUID v5
  - JWT token generation and validation
  - Telegram data verification
  - Platform authentication flow
  - JWT authorizer functionality
  - Error handling
  - DynamoDB operations (mocked)

## Running Tests

Run tests from the lambda directory:

```bash
cd src/services/auth/aws_lambdas

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
- AWS Secrets Manager integration (mocked)
- DynamoDB operations (mocked)

## Expected Output

All tests should output:
- ✓ PASS for successful tests
- ✗ FAIL for failed tests
- Summary of all test results
- Clear error messages for debugging

## Test Coverage

The tests cover:
1. **Lambda Layer Dependencies**: All required packages and their functionality
2. **Code Structure**: Import paths and modular design
3. **Authentication Flow**: Complete platform authentication process
4. **JWT Operations**: Token generation, validation, and authorization
5. **User Management**: User ID generation and database operations
6. **Error Handling**: Proper error responses and validation
7. **Security**: Telegram data verification and JWT security

## Mocking Strategy

Tests use comprehensive mocking to avoid external dependencies:
- AWS Secrets Manager calls are mocked
- DynamoDB operations are mocked
- Telegram API calls are mocked
- JWT verification is mocked where appropriate

This ensures tests can run locally without requiring actual AWS resources or external APIs. 