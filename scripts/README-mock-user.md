# Mock User Creation Script

This script creates realistic mock users for the Vibe Dating backend for testing and development purposes.

## Features

- **Authentic Telegram Authentication**: Creates valid Telegram WebApp signatures using the bot's secret key
- **Realistic Profile Data**: Generates randomized but realistic profile information
- **Profile Images**: Downloads and uploads random profile pictures from image services
- **Full Backend Integration**: Uses the actual REST API endpoints
- **Error Handling**: Robust error handling and retry logic

## Usage

### Basic Usage

```bash
# Using Poetry (recommended)
poetry run create-mock-user --env dev
poetry run create-mock-user --env dev --num-images 5 --output user.json

# Using Python directly
python scripts/create_mock_user.py --env dev
python scripts/create_mock_user.py --api-url https://api.vibe-dating.io
python scripts/create_mock_user.py --env dev --num-images 5
python scripts/create_mock_user.py --env dev --output mock_user.json
```

### Command Line Options

- `--env`: Environment (dev, staging, prod). Default: dev
- `--api-url`: Custom API base URL. If not provided, will use configuration
- `--bot-token`: Telegram bot token. If not provided, will fetch from AWS Secrets Manager
- `--num-images`: Number of profile images to upload. Default: 3
- `--output`: File to save complete user data JSON

### Prerequisites

1. **Install Dependencies**:
   ```bash
   # Option 1: Use poetry (recommended)
   poetry install
   
   # Option 2: Use pip
   pip install -r scripts/requirements-mock-user.txt
   ```

2. **AWS Configuration**: 
   - Ensure AWS credentials are configured for the target environment
   - Script uses profile name format: `vibe-{environment}` (e.g., `vibe-dev`)

3. **Telegram Bot Token**: 
   - Either provide via `--bot-token` parameter
   - Or ensure it exists in AWS Secrets Manager at: `vibe-dating/telegram-bot-token/{environment}`

## What the Script Creates

### 1. Telegram User
- Random realistic name and username
- Valid Telegram user ID
- Proper WebApp signature using bot token
- Profile photo URL

### 2. User Profile
- Random nickname and bio
- Age between 18-45
- All profile fields populated with realistic values:
  - Sexual position, body type, sexuality
  - Health practices and HIV status
  - Prevention practices
  - Hosting preferences and travel distance

### 3. Profile Images
- Downloads random images from multiple services:
  - Picsum Photos (landscapes)
  - Pravatar (avatars) 
  - Unsplash (portraits)
- Uploads through proper media pipeline
- Creates proper metadata and triggers processing

## Output

The script outputs:
- User ID and Profile ID
- Generated username and profile name  
- Number of successfully uploaded images
- Full JSON data (if `--output` specified)

Example output:
```
==================================================
MOCK USER CREATED SUCCESSFULLY!
==================================================
User ID: aB3cD4eF
Profile ID: xY9zA1bC
Username: @CoolGuy123
Profile Name: Alex
Images Uploaded: 3
```

## Error Handling

The script includes robust error handling for:
- Network failures with retry logic
- AWS authentication issues
- Image download failures
- Backend API errors
- Telegram signature validation

## Architecture Integration

The script follows the project's architecture patterns:
- Uses the same Telegram signature validation as the backend
- Imports actual type definitions from `core_types`
- Follows the same media upload flow as the frontend
- Uses proper JWT authentication
- Respects all backend validation rules

## Development Notes

- **Deterministic Images**: Uses user ID as seed for consistent but varied images
- **Realistic Data**: Names, bios, and settings are carefully chosen for authenticity  
- **Rate Limiting**: Includes delays and retry logic for external services
- **Security**: Generates proper cryptographic signatures for Telegram auth
- **Extensible**: Easy to add new data generators or image sources

## Troubleshooting

### Common Issues

1. **AWS Authentication Error**:
   - Check AWS credentials for environment
   - Ensure profile `vibe-{env}` exists

2. **Bot Token Error**:
   - Verify bot token exists in Secrets Manager
   - Or provide token via `--bot-token`

3. **API Connection Error**:
   - Check API URL is correct
   - Verify backend is deployed and running

4. **Image Upload Failure**:
   - Usually continues with other images
   - Check S3 permissions if all fail

5. **Profile Creation Error**:
   - Check user has allocated profile IDs
   - Verify all required profile fields are valid

### Debug Mode

Add `--verbose` flag (not implemented yet) or modify the script to add more logging as needed.