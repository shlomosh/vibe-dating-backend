# Vibe Dating App - Authentication Service

This service provides secure authentication for the Vibe dating application using Telegram WebApp authentication and JWT tokens.

## Overview

The authentication service consists of:

1. **Telegram Authentication Lambda** - Validates Telegram WebApp data and issues JWT tokens
2. **JWT Authorizer Lambda** - Validates JWT tokens for API Gateway requests
3. **DynamoDB Table** - Stores user data with single-table design
4. **API Gateway** - Provides REST API endpoints with JWT authorization
5. **KMS Encryption** - Secures sensitive data at rest

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway    │    │   Lambda        │
│   (Telegram     │───▶│   (JWT Auth)     │───▶│   Functions     │
│   Mini-App)     │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   DynamoDB       │    │   CloudWatch    │
                       │   (User Data)    │    │   (Logs)        │
                       └──────────────────┘    └─────────────────┘
```

## Features

- ✅ Telegram WebApp authentication validation
- ✅ Deterministic user ID generation using UUID v5
- ✅ JWT token generation and validation
- ✅ DynamoDB single-table design
- ✅ KMS encryption for data at rest
- ✅ API Gateway with custom authorizer
- ✅ CORS support for Telegram domains
- ✅ Security headers implementation
- ✅ CloudWatch logging and monitoring
- ✅ Automated deployment with CloudFormation

## API Endpoints

### Authentication

- `POST /auth/telegram` - Authenticate with Telegram WebApp data
  - **Request Body:**
    ```json
    {
      "initData": "telegram_init_data_string",
      "telegramUser": {
        "id": 123456789,
        "username": "username",
        "first_name": "John",
        "last_name": "Doe"
      }
    }
    ```
  - **Response:**
    ```json
    {
      "token": "jwt_token_string",
      "userId": "aB3cD4eF",
      "telegramUser": {
        "id": 123456789,
        "username": "username",
        "firstName": "John",
        "lastName": "Doe"
      }
    }
    ```

## DynamoDB Schema

### User Entity
```json
{
  "PK": "USER#{userId}",
  "SK": "METADATA",
  "telegramId": "123456789",
  "telegramUsername": "username",
  "telegramFirstName": "John",
  "telegramLastName": "Doe",
  "createdAt": "2024-01-01T00:00:00Z",
  "lastActiveAt": "2024-01-01T12:00:00Z",
  "isBanned": false,
  "banReason": null,
  "banExpiresAt": null,
  "preferences": {
    "notifications": true,
    "privacy": "public"
  },
  "GSI1PK": "USER#{userId}",
  "GSI1SK": "METADATA"
}
```

## User ID Generation

The service uses a deterministic hashing process to convert Telegram user IDs to Vibe user IDs:

1. **Platform Identifier**: `tg:{telegram_user_id}`
2. **UUID v5 Generation**: Uses fixed namespace UUID
3. **Base64 Encoding**: Converts UUID to Base64 string
4. **Truncation**: Takes first 8 characters for final user ID

Example:
- Telegram ID: `123456789`
- Platform String: `tg:123456789`
- Final User ID: `aB3cD4eF`

## Security Features

### JWT Token Security
- **Algorithm**: HS256
- **Expiration**: 7 days
- **Claims**: user_id, iat, exp, iss
- **Secret**: Environment variable (KMS encrypted)

### Data Protection
- **DynamoDB Encryption**: KMS customer-managed keys
- **API Gateway**: HTTPS only
- **Security Headers**: XSS protection, content type options, frame options
- **CORS**: Restricted to Telegram domains

### Input Validation
- Telegram data integrity verification
- JWT token validation
- Request body validation

## Deployment

### Prerequisites

1. **AWS CLI** installed and configured
2. **AWS Credentials** with appropriate permissions
3. **Telegram Bot Token** from @BotFather
4. **JWT Secret** (secure random string)

### Quick Deployment

1. **Update Parameters**:
   ```bash
   # Edit src/services/auth/cloudformation/parameters.yaml
   # Set your actual TelegramBotToken and JWTSecret
   ```

2. **Build and Deploy**:
   ```bash
   cd src/services/auth
   ./deploy.sh deploy
   ```
   This will automatically:
   - Build Lambda function packages
   - Upload packages to S3
   - Deploy/update CloudFormation stack

3. **Verify Deployment**:
   ```bash
   ./deploy.sh status
   ```

### Manual Build and Deploy

```bash
# Build Lambda packages only
./build.sh

# Deploy stack only (if packages already built)
./deploy.sh deploy
```

### Manual Deployment

```bash
# Validate template
aws cloudformation validate-template \
  --template-body file://cloudformation/template.yaml

# Create stack
aws cloudformation create-stack \
  --stack-name vibe-auth-service \
  --template-body file://cloudformation/template.yaml \
  --parameters file://cloudformation/parameters.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --tags Key=Environment,Value=dev Key=Service,Value=auth

# Wait for completion
aws cloudformation wait stack-create-complete \
  --stack-name vibe-auth-service
```

### Deployment Scripts

- `./deploy.sh deploy` - Deploy or update stack
- `./deploy.sh delete` - Delete stack
- `./deploy.sh status` - Show stack status
- `./deploy.sh validate` - Validate template

## Environment Variables

### Required
- `TELEGRAM_BOT_TOKEN` - Telegram bot token for WebApp validation
- `JWT_SECRET` - Secret key for JWT token signing
- `DYNAMODB_TABLE` - DynamoDB table name (auto-set by CloudFormation)

### Optional
- `ENVIRONMENT` - Environment name (dev/staging/prod)

## Testing

### Local Testing

1. **Install Dependencies**:
   ```bash
   pip install -r lambda/requirements.txt
   ```

2. **Test Telegram Auth Function**:
   ```python
   import json
   from lambda.telegram_auth import lambda_handler
   
   # Test event
   event = {
       "body": json.dumps({
           "initData": "your_telegram_init_data",
           "telegramUser": {
               "id": 123456789,
               "username": "testuser",
               "first_name": "Test",
               "last_name": "User"
           }
       })
   }
   
   response = lambda_handler(event, None)
   print(response)
   ```

### API Testing

1. **Get API Gateway URL**:
   ```bash
   aws cloudformation describe-stacks \
     --stack-name vibe-auth-service \
     --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
     --output text
   ```

2. **Test Authentication Endpoint**:
   ```bash
   curl -X POST https://your-api-gateway-url/dev/auth/telegram \
     -H "Content-Type: application/json" \
     -d '{
       "initData": "your_telegram_init_data",
       "telegramUser": {
         "id": 123456789,
         "username": "testuser",
         "first_name": "Test",
         "last_name": "User"
       }
     }'
   ```

## Monitoring

### CloudWatch Logs
- **Telegram Auth**: `/aws/lambda/vibe-telegram-auth-{env}`
- **JWT Authorizer**: `/aws/lambda/vibe-jwt-authorizer-{env}`

### CloudWatch Metrics
- API Gateway request count and latency
- Lambda function duration and errors
- DynamoDB read/write capacity

### Alarms
- High error rate
- High latency
- Authentication failures

## Troubleshooting

### Common Issues

1. **Template Validation Failed**
   - Check YAML syntax
   - Verify all required parameters

2. **Deployment Failed**
   - Check AWS credentials
   - Verify IAM permissions
   - Check CloudFormation events

3. **Authentication Errors**
   - Verify Telegram bot token
   - Check init data format
   - Validate JWT secret

4. **CORS Errors**
   - Verify allowed origins
   - Check API Gateway CORS settings

### Debug Commands

```bash
# Check stack events
aws cloudformation describe-stack-events \
  --stack-name vibe-auth-service

# Check Lambda logs
aws logs tail /aws/lambda/vibe-telegram-auth-dev --follow

# Test DynamoDB access
aws dynamodb scan --table-name vibe-dating-dev --limit 1
```

## Development

### Local Development

1. **Setup Local Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r lambda/requirements.txt
   ```

2. **Environment Variables**:
   ```bash
   export TELEGRAM_BOT_TOKEN="your_bot_token"
   export JWT_SECRET="your_jwt_secret"
   export DYNAMODB_TABLE="vibe-dating-dev"
   ```

3. **Run Tests**:
   ```bash
   python -m pytest tests/
   ```

### Code Structure

```
src/services/auth/
├── cloudformation/
│   ├── template.yaml      # CloudFormation template
│   └── parameters.yaml    # Deployment parameters
├── lambda/
│   ├── lambda_function.py # Combined Lambda function code
│   ├── requirements.txt   # Python dependencies
│   └── test_auth.py      # Local testing script
├── examples/
│   └── frontend_integration.js # Frontend integration example
├── build.sh               # Lambda package build script
├── deploy.sh              # Deployment script
├── validate_template.sh   # Template validation script
└── README.md             # This file
```

## Contributing

1. Follow the existing code style
2. Add tests for new features
3. Update documentation
4. Test deployment in dev environment

## License

This project is part of the Vibe Dating App backend services. 