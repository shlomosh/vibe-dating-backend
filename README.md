# Vibe Dating App Backend

A serverless backend for the Vibe dating application, built with AWS Lambda, API Gateway, and DynamoDB.

## Quick Start

### Prerequisites

- Python 3.11+
- [Poetry](https://python-poetry.org/docs/#installation) for dependency management
- [AWS CLI](https://aws.amazon.com/cli/) configured with appropriate credentials
- [Docker](https://www.docker.com/) (optional, for local development)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd vibe-dating-backend
   ```

2. **Install dependencies with Poetry**
   ```bash
   poetry install
   ```

3. **Install Lambda dependencies**
   ```bash
   poetry install --with lambda
   ```

## Development

### Code Quality

The project uses several tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **mypy**: Type checking
- **flake8**: Linting
- **pytest**: Testing

Run all quality checks:
```bash
poetry run test-lambda
```

### Lambda Development

The authentication service includes Lambda functions for:
- Telegram WebApp authentication
- JWT token validation

#### Building Lambda Packages
```bash
poetry run build-lambda
```

This creates:
- `build/lambda/vibe_base_layer.zip`: Shared Python dependencies
- `build/lambda/telegram_auth.zip`: Telegram authentication function
- `build/lambda/jwt_authorizer.zip`: JWT authorization function

#### Testing Lambda Functions
```bash
poetry run test-lambda
```

This runs:
- Lambda layer dependency tests
- Code structure tests
- Authentication function tests
- Unit tests
- Code linting

#### Deploying to AWS
```bash
poetry run deploy-auth
```

This:
1. Builds Lambda packages
2. Uploads to S3
3. Deploys CloudFormation stack
4. Shows deployment outputs

## Project Structure

```
vibe-dating-backend/
├── src/
│   └── services/
│       └── auth/                    # Authentication service
│           ├── aws_lambdas/         # Lambda functions
│           │   ├── core/            # Shared utilities
│           │   ├── telegram_auth/   # Telegram auth function
│           │   ├── jwt_authorizer/  # JWT authorizer function
│           │   └── test/            # Lambda tests
│           ├── cloudformation/      # Infrastructure as Code
│           └── README.md            # Service documentation
├── scripts/                         # Poetry-based deployment scripts
│   ├── build.py                     # Lambda package building
│   ├── deploy.py                    # AWS deployment
│   ├── test.py                      # Testing framework
│   ├── manage_secrets.py            # AWS Secrets Manager integration
│   └── requirements-secrets.txt     # Secrets management dependencies
├── tests/                           # Unit tests
├── pyproject.toml                   # Poetry configuration
└── README.md                        # This file
```

## Configuration

### Environment Variables

Set these environment variables for deployment:

```bash
export AWS_REGION=il-central-1
export ENVIRONMENT=dev
export AWS_PROFILE=vibe-dating
```

### CloudFormation Parameters

Update `src/config/cloudformation/parameters.yaml` with deployment parameters

### Secrets Management

The project includes a comprehensive AWS Secrets Manager integration for secure secret management:

```bash
# Install secrets management dependencies
pip install -r scripts/requirements-secrets.txt

# Setup core secrets interactively
python scripts/manage_secrets.py setup

# Setup core secrets
python scripts/manage_secrets.py setup

# List all secrets
python scripts/manage_secrets.py list

# Export secrets to environment file
python scripts/manage_secrets.py export --output .env

# Validate all secrets
python scripts/manage_secrets.py validate

# Rotate JWT secret
python scripts/manage_secrets.py rotate --secret jwt_secret

# Get a secret value
python scripts/manage_secrets.py get --secret telegram_bot_token
```

**Supported Secrets**:
- **Core**: `telegram_bot_token`, `jwt_secret` (auto-generated), `uuid_namespace` (auto-generated)

**Environment Configuration**:
```bash
export ENVIRONMENT=dev|staging|prod
export AWS_REGION=il-central-1
export AWS_PROFILE=vibe-dating
```

## Deployment

### Full Deployment Workflow
```bash
# Install dependencies
poetry install --with lambda

# Run tests
poetry run test-lambda

# Deploy to AWS
poetry run deploy-auth
```

### Step-by-Step Deployment
```bash
# 1. Build Lambda packages
poetry run build-lambda

# 2. Test functions
poetry run test-lambda

# 3. Deploy infrastructure
poetry run deploy-auth
```

### Environment-Specific Deployment
```bash
# Development
export ENVIRONMENT=dev
poetry run deploy-auth

# Staging
export ENVIRONMENT=staging
poetry run deploy-auth

# Production
export ENVIRONMENT=prod
poetry run deploy-auth
```

## Testing

### Comprehensive Test Suite
```bash
# Run all tests
poetry run test-lambda
```

### Individual Test Categories
```bash
# Lambda layer tests
poetry run python src/services/auth/aws_lambdas/test/test_layer.py

# Code structure tests
poetry run python src/services/auth/aws_lambdas/test/test_structure.py

# Authentication tests
poetry run python src/services/auth/aws_lambdas/test/test_auth.py

# Unit tests
poetry run pytest tests/
```

### Manual Testing
```bash
# Test Lambda layer dependencies
poetry run python -c "import jwt, boto3, requests; print('All dependencies available')"

# Test function imports
poetry run python -c "from src.services.auth.aws_lambdas.core.auth_utils import verify_jwt_token; print('Auth utils imported')"
```

## Documentation

- [Technical Context](docs/context.md) - Comprehensive technical documentation
- [Deployment Guide](docs/deployment.md) - Complete deployment and build documentation
- [Authentication Service](src/services/auth/README.md) - Service-specific documentation
- [Authentication Service](src/services/auth/README.md) - Complete service documentation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `poetry run test-lambda`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.