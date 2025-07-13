# Vibe Dating App Backend

A production-ready, serverless backend for the Vibe dating application, built with AWS Lambda, API Gateway, and DynamoDB. Designed specifically for Telegram Mini-App integration with advanced features including real-time communication, media processing, and comprehensive user management.

## Quick Start

### Prerequisites

- **Python 3.11+** - Required for Lambda runtime compatibility
- **[Poetry](https://python-poetry.org/docs/#installation)** - Modern Python dependency management
- **[AWS CLI](https://aws.amazon.com/cli/)** - Configured with appropriate credentials
- **[Docker](https://www.docker.com/)** - Optional, for local development and testing

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

## Architecture Overview

The Vibe Dating App backend is built on a modern, scalable serverless architecture:

### Core Services
- **Authentication Service** - Telegram WebApp authentication with JWT tokens
- **Core Infrastructure** - S3, DynamoDB, IAM roles, and KMS encryption
- **User Service** - Profile and user management (planned)
- **Media Service** - File upload and processing (planned)
- **Agora Service** - Real-time communication integration (planned)

### Technology Stack
- **AWS Lambda** - Serverless compute with Python 3.11
- **API Gateway** - REST API with JWT authorization
- **DynamoDB** - Single-table design with 6 GSIs
- **S3 + CloudFront** - Media storage and CDN delivery
- **KMS** - Customer-managed encryption keys
- **CloudWatch** - Comprehensive monitoring and logging

## Development

### Code Quality

The project uses several tools to maintain code quality:

- **Black** - Code formatting
- **isort** - Import sorting
- **mypy** - Type checking
- **flake8** - Linting
- **pytest** - Testing

Run all quality checks:
```bash
poetry run service-test auth
```

### Lambda Development

The authentication service includes Lambda functions for:
- **Telegram WebApp Authentication** - Validates Telegram user data and issues JWT tokens
- **JWT Token Validation** - Lambda authorizer for API Gateway requests

#### Building Lambda Packages
```bash
poetry run build-lambda
```

This creates:
- `build/lambda/auth_layer.zip` - Shared Python dependencies
- `build/lambda/platform_auth.zip` - Telegram authentication function
- `build/lambda/user_jwt_authorizer.zip` - JWT authorization function

#### Testing Lambda Functions
```bash
poetry run service-test auth
```

This runs:
- Lambda layer dependency tests
- Code structure tests
- Authentication function tests
- Unit tests
- Code linting and formatting

#### Deploying Core Infrastructure
```bash
poetry run service-deploy core
```

This deploys the foundational AWS infrastructure:
1. **S3 Bucket** - For Lambda code storage with versioning and encryption
2. **DynamoDB Table** - Main application database with KMS encryption
3. **IAM Roles** - Execution roles for Lambda functions and API Gateway

#### Deploying Authentication Service
```bash
# Build and upload Lambda packages
poetry run service-build auth

# Deploy infrastructure or update functions
poetry run service-deploy auth
```

This:
1. **First time deployment**: Builds packages, uploads to S3, and deploys CloudFormation stack
2. **Updates**: Downloads existing packages from S3 and updates Lambda function code
3. Shows deployment outputs including API Gateway URLs

**Note**: For updates, run `poetry run service-build auth` first to ensure the latest code is uploaded to S3.

## Project Structure

```
vibe-dating-backend/
├── src/
│   ├── config/                      # Configuration files
│   │   └── parameters.json          # CloudFormation parameters
│   ├── core/                        # Core utilities
│   │   ├── build_utils.py           # Build system utilities
│   │   └── deploy_utils.py          # Deployment utilities
│   └── services/
│       ├── core/                    # Core infrastructure service
│       │   ├── cloudformation/      # Core infrastructure (S3, DynamoDB, IAM)
│       │   │   ├── 01-s3.yaml       # S3 bucket for Lambda code
│       │   │   ├── 02-dynamodb.yaml # Main database table
│       │   │   ├── 03-iam.yaml      # IAM roles and policies
│       │   │   └── deploy.py        # Core deployment script
│       │   └── README.md            # Core service documentation
│       ├── auth/                    # Authentication service
│       │   ├── aws_lambdas/         # Lambda functions
│       │   │   ├── core/            # Shared utilities
│       │   │   │   └── auth_utils.py # Common authentication functions
│       │   │   ├── platform_auth/   # Telegram auth function
│       │   │   ├── user_jwt_authorizer/  # JWT authorizer function
│       │   │   ├── test/            # Lambda tests
│       │   │   └── requirements.txt # Lambda dependencies
│       │   ├── cloudformation/      # Infrastructure as Code
│       │   │   ├── 01-apigateway.yaml # API Gateway configuration
│       │   │   └── 02-lambda.yaml   # Lambda functions and layers
│       │   └── README.md            # Service documentation
│       ├── user/                    # User service (planned)
│       ├── media/                   # Media service (planned)
│       └── agora/                   # Agora.io integration (planned)
├── scripts/                         # Poetry-based deployment scripts
│   ├── build.py                     # Lambda package building
│   ├── deploy.py                    # AWS deployment
│   ├── test.py                      # Testing framework
│   ├── manage_secrets.py            # AWS Secrets Manager integration
│   └── requirements-secrets.txt     # Secrets management dependencies
├── docs/                            # Comprehensive documentation
│   ├── context.md                   # Technical context and architecture
│   ├── deployment.md                # Deployment and build documentation
│   ├── frontend.md                  # Frontend integration guide
│   ├── api.md                       # API documentation
│   ├── build-system.md              # Build system documentation
│   ├── deployment-secrets_management.md # Secrets management guide
│   └── examples/                    # Code examples
│       └── frontend/                # Frontend integration examples
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
export AWS_PROFILE=vibe-dev
```

### CloudFormation Parameters

Update `src/config/parameters.json` with deployment parameters:

```json
{
  "Environment": "dev",
  "TelegramBotToken": "your-bot-token",
  "JWTSecret": "your-jwt-secret",
  "UUIDNamespace": "your-uuid-namespace"
}
```

### Secrets Management

The project includes a comprehensive AWS Secrets Manager integration for secure secret management:

```bash
# Install secrets management dependencies
pip install -r scripts/requirements-secrets.txt

# Setup core secrets interactively
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
export AWS_PROFILE=vibe-dev
```

## Deployment

### Full Deployment Workflow
```bash
# Install dependencies
poetry install --with lambda

# Run tests
poetry run service-test auth

# Deploy core infrastructure
poetry run service-deploy core

# Deploy authentication service
poetry run service-deploy auth
```

### Step-by-Step Deployment
```bash
# 1. Build Lambda packages
poetry run service-build auth

# 2. Test functions
poetry run service-test auth

# 3. Deploy core infrastructure (S3, DynamoDB, IAM)
poetry run service-deploy core

# 4. Deploy authentication service
poetry run service-deploy auth
```

### Environment-Specific Deployment
```bash
# Development
export ENVIRONMENT=dev
poetry run service-deploy core
poetry run service-deploy auth

# Staging
export ENVIRONMENT=staging
poetry run service-deploy core
poetry run service-deploy auth

# Production
export ENVIRONMENT=prod
poetry run service-deploy core
poetry run service-deploy auth
```

## Testing

### Comprehensive Test Suite
```bash
# Run all tests
poetry run service-test auth
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

- **[Technical Context](docs/context.md)** - Comprehensive technical documentation and architecture overview
- **[Deployment Guide](docs/deployment.md)** - Complete deployment and build documentation
- **[Frontend Integration](docs/frontend.md)** - Frontend integration guide and examples
- **[API Documentation](docs/api.md)** - Complete API reference and examples
- **[Build System](docs/build-system.md)** - Build system architecture and usage
- **[Secrets Management](docs/deployment-secrets_management.md)** - AWS Secrets Manager integration guide
- **[Authentication Service](src/services/auth/README.md)** - Complete authentication service documentation
- **[Core Service](src/services/core/README.md)** - Core infrastructure service documentation

## Security Features

### Authentication & Authorization
- **Telegram WebApp Authentication** - Secure validation of Telegram init data
- **JWT Token Management** - HS256 tokens with 7-day expiration
- **Deterministic User ID Generation** - UUID v5-based consistent identification
- **Lambda Authorizer** - Custom JWT validation for API Gateway

### Data Protection
- **KMS Encryption** - Customer-managed keys for data at rest
- **DynamoDB Encryption** - Automatic encryption of all data
- **API Gateway Security** - HTTPS only with security headers
- **CORS Protection** - Restricted to Telegram domains

### Infrastructure Security
- **IAM Least Privilege** - Minimal required permissions
- **VPC Isolation** - Network security (when applicable)
- **CloudTrail Logging** - Complete audit trail
- **Secrets Management** - AWS Secrets Manager integration

## Advanced Features

### Real-time Communication
- **Agora.io Integration** - Real-time messaging, voice, and video calls
- **Active User Tracking** - Real-time presence indicators
- **Typing Indicators** - Visual feedback for message composition
- **Message Management** - Edit, delete, and react to messages

### Media Processing
- **Frontend Processing** - Client-side crop, zoom, and EXIF removal
- **Backend Processing** - Thumbnail generation and video transcoding
- **CloudFront CDN** - Fast media delivery worldwide
- **Format Support** - JPEG, PNG, MP4, WebM with size limits

### User Management
- **Multi-Profile Support** - Users can create multiple profiles
- **Location-Based Matching** - Geohash-based proximity search
- **User Blocking & Banning** - Community moderation features
- **Privacy Controls** - Granular privacy settings

### Community Features
- **Subject-Based Rooms** - Themed discussion rooms
- **Message Moderation** - Community-driven content filtering
- **Report System** - User and content reporting
- **Room Analytics** - Participation and activity tracking

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `poetry run service-test auth`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions and support:
- Check the comprehensive documentation in the `docs/` directory
- Review the troubleshooting guides in each service README
- Open an issue for bugs or feature requests

---

**Vibe Dating App Backend** - A modern, scalable, and secure serverless backend for the Telegram Mini-App platform.