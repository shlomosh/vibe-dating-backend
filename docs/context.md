# Vibe Dating App - Technical Context Document

## Application Overview
Vibe is a location-based dating application designed as a Telegram Mini-App for the gay community. The app focuses on profile-based interactions, location-aware features, real-time communication, and themed discussion rooms.

## Core Architecture

### Frontend Stack
- **Platform**: Telegram Mini-App
- **Framework**: React with TypeScript
- **Styling**: Tailwind CSS + shadcn/ui components
- **Build Tool**: Modern bundler (Vite)
- **State Management**: React hooks + Context API
- **Mobile-First**: Responsive design for mobile devices
- **Media Processing**: Client-side crop/zoom/EXIF handling for images, video compression for short videos

### Backend Stack
- **Architecture**: AWS Serverless
- **API**: REST API via AWS API Gateway
- **Compute**: AWS Lambda functions
- **Database**: DynamoDB (single-table design)
- **Storage**: AWS S3 for media files
- **CDN**: CloudFront for media delivery
- **Authentication**: Telegram-based authentication
- **Framework**: Python 3.11 +
- **Media Processing**: Thumbnail generation, video transcoding, and metadata extraction

### External Services
- **Chat & Communication**: Agora.io for real-time messaging, voice/video calls, presence management
- **Maps/Location**: Browser geolocation + geohash encoding
- **Media Processing**: Frontend handles initial processing, backend generates thumbnails and video previews

## Deployment & Build System

### Poetry-Based Development Environment
The project uses Poetry for dependency management and provides a modern, consistent development experience across all environments.

#### Prerequisites
- **Python 3.11+**: Required for Lambda runtime compatibility
- **Poetry**: Modern Python dependency management
- **AWS CLI**: Configured with appropriate credentials
- **Docker**: Optional, for local development and testing

#### Installation & Setup
```bash
# Clone repository
git clone <repository-url>
cd vibe-dating-backend

# Install all dependencies
poetry install

# Install Lambda-specific dependencies
poetry install --with lambda
```

### Build System

#### Lambda Package Building
The build system creates optimized Lambda packages with proper dependency management:

```bash
# Build Lambda packages
poetry run build-lambda
```

**Generated Artifacts**:
- `build/lambda/auth_layer.zip`: Shared Python dependencies layer
- `build/lambda/telegram_auth.zip`: Telegram authentication function
- **JWT Authorizer**: JWT authorization function

**Build Process**:
1. **Dependency Management**: Uses Poetry to export Lambda dependencies
2. **Layer Creation**: Creates shared dependency layer for code reuse
3. **Function Packaging**: Packages individual Lambda functions with minimal dependencies
4. **Optimization**: Removes unnecessary files and optimizes package sizes

#### Build Configuration
- **Dependencies**: Managed via `pyproject.toml` with separate `lambda` group
- **Python Version**: 3.11+ for Lambda compatibility
- **Package Optimization**: Automatic removal of development dependencies
- **Layer Strategy**: Shared dependencies in base layer, function-specific code in individual packages

### Deployment System

#### AWS Infrastructure Deployment
The deployment system uses CloudFormation for infrastructure as code:

```bash
# Deploy authentication service
poetry run deploy-auth
```

**Deployment Process**:
1. **Prerequisites Check**: Validates AWS credentials, Poetry installation, and build artifacts
2. **Lambda Building**: Automatically builds Lambda packages if not present
3. **S3 Upload**: Uploads packages to environment-specific S3 bucket
4. **CloudFormation Deployment**: Deploys/updates infrastructure stack
5. **Output Display**: Shows API Gateway URLs and other outputs

#### Environment Configuration
```bash
# Set deployment environment
export ENVIRONMENT=dev|staging|prod
export AWS_REGION=il-central-1
export AWS_PROFILE=vibe-dev
```

#### CloudFormation Stacks
- **Stack Name**: `vibe-dating-auth-service`
- **Region**: `il-central-1` (default)
- **Capabilities**: `CAPABILITY_NAMED_IAM` for IAM role creation
- **Tags**: Environment and Service tags for resource management

### Testing System

#### Comprehensive Test Suite
```bash
# Run all tests
poetry run test-lambda
```

**Test Categories**:
1. **Lambda Layer Tests**: Validates dependency availability and compatibility
2. **Structure Tests**: Ensures proper code organization and imports
3. **Authentication Tests**: Tests Telegram auth and JWT validation logic
4. **Unit Tests**: Pytest-based unit tests for individual components
5. **Code Quality**: Black, isort, and mypy for code formatting and type checking

#### Test Configuration
- **Framework**: pytest with coverage reporting
- **Linting**: Black (formatting), isort (imports), mypy (types)
- **Coverage**: Configurable coverage thresholds and exclusions
- **Markers**: Unit, integration, and slow test markers

### Service-Specific Deployment

#### Authentication Service
The authentication service is the primary deployment target, providing:
- **Telegram WebApp Authentication**: Validates Telegram user data
- **JWT Token Management**: Issues and validates JWT tokens
- **API Gateway Integration**: Lambda authorizer for protected endpoints

**Deployment Commands**:
```bash
# Full deployment workflow
poetry install --with lambda
poetry run test-lambda
poetry run auth-build      # Build and upload packages
poetry run auth-deploy     # Deploy infrastructure or update functions

# Individual steps
poetry run auth-build      # Build and upload packages only
poetry run test-lambda     # Run tests only
poetry run auth-deploy     # Deploy/update only
```

#### Future Services
The deployment system is designed to support additional services:
- **User Service**: Profile and user management
- **Media Service**: File upload and processing
- **Agora Service**: Real-time communication integration

### Development Workflow

#### Local Development
```bash
# Install development dependencies
poetry install --with dev

# Run code quality checks
poetry run black src/
poetry run isort src/
poetry run mypy src/

# Run tests
poetry run pytest tests/
```

#### CI/CD Integration
The Poetry-based system integrates well with CI/CD pipelines:
- **Dependency Caching**: Poetry lock file for reproducible builds
- **Environment Isolation**: Virtual environments for each deployment
- **Artifact Management**: S3-based package storage and versioning
- **Rollback Support**: CloudFormation stack rollback capabilities

### Monitoring & Maintenance

#### Deployment Monitoring
- **CloudFormation Events**: Real-time deployment status
- **Lambda Metrics**: Function performance and error rates
- **API Gateway Logs**: Request/response monitoring
- **CloudWatch Alarms**: Automated alerting for issues

#### Maintenance Tasks
```bash
# Update dependencies
poetry update

# Clean build artifacts
rm -rf build/

# Validate CloudFormation templates
aws cloudformation validate-template --template-body file://template.yaml
```

### Secrets Management

#### AWS Secrets Manager Integration
The project includes a comprehensive secrets management system using AWS Secrets Manager:

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

#### Supported Secrets
**Core Secrets** (Required):
- `telegram_bot_token`: Telegram Bot Token for WebApp authentication
- `jwt_secret`: Secret key for JWT token signing (auto-generated)
- `uuid_namespace`: UUID namespace for generating consistent UUIDs (auto-generated)

#### Secret Naming Convention
Secrets are stored with environment-specific naming:
- Format: `vibe-dating/{secret-name}/{environment}`
- Examples:
  - `vibe-dating/telegram-bot-token/dev`
  - `vibe-dating/jwt-secret/prod`
  - `vibe-dating/agora-app-id/staging`

#### Environment Configuration
```bash
# Set environment for secrets management
export ENVIRONMENT=dev|staging|prod
export AWS_REGION=il-central-1
export AWS_PROFILE=vibe-dev
```

#### Security Features
- **Automatic Tagging**: All secrets are tagged with environment and service information
- **Secure Generation**: JWT secrets are automatically generated using cryptographically secure methods
- **Access Control**: Secrets are managed through AWS IAM roles and policies
- **Audit Trail**: All secret operations are logged in CloudTrail
- **Recovery Window**: Deleted secrets have a 7-day recovery window by default
```

## Data Model & Identifiers

### ID System
- All application IDs are **16-character base64 strings**
- User ID: Generated from hash of Telegram user ID (1:1 mapping)
- Profile ID: Unique per profile (max 3 per user)
- Media ID: Unique per media item (max 5 per profile, supporting images and short videos)
- Room ID: Unique per subject-based room
- Message ID: Unique per room message
- Block ID: Unique per user block relationship

### Entity Relationships
```
User (1) -> Profiles (1-3) -> Media (0-5) [images/short-videos]
User (1) -> Agora Chat ID (1)
User (1) -> Blocked Users (many)
User (1) -> Banned Users (many)
Profile (1) -> Location History (many)
Profile (1) -> Room Messages (many)
Room (1) -> Messages (many) -> Media Attachments (0-many)
```

## Detailed DynamoDB Schema

### Single Table Design: `vibe-dating`

#### Partition Key (PK) and Sort Key (SK) Structure
```
PK: EntityType#{ID}
SK: MetadataType#{Timestamp/ID}
```

#### Core Entity Types

**1. User Entity**
```json
{
  "PK": "USER#{userId}",
  "SK": "METADATA",
  "platform": "tg",
  "platformId": "123456789",
  "platformMetadata": {
    "username": "username",
    "first_name": "John",
    "last_name": "Doe",
    "language_code": "en",
    "is_premium": false,
    "added_to_attachment_menu": false
  },
  "createdAt": "2024-01-01T00:00:00Z",
  "lastActiveAt": "2024-01-01T12:00:00Z",
  "chatId": "agora_chat_id",
  "isBanned": false,
  "banReason": null,
  "banExpiresAt": null,
  "preferences": {
    "notifications": true,
    "privacy": "public"
  },
  "TTL": 0
}
```

**2. Profile Entity**
```json
{
  "PK": "PROFILE#{profileId}",
  "SK": "METADATA",
  "userId": "userId",
  "name": "Profile Name",
  "age": 25,
  "bio": "Profile description",
  "interests": ["music", "travel", "sports"],
  "lookingFor": ["friendship", "relationship"],
  "location": {
    "latitude": 40.7128,
    "longitude": -74.0060,
    "geohash": "dr5ru",
    "precision": 5,
    "lastUpdated": "2024-01-01T12:00:00Z"
  },
  "media": {
    "mediaId1": {
      "type": "image",
      "url": "https://cdn.example.com/original/mediaId1.jpg",
      "thumbnailUrl": "https://cdn.example.com/thumb/mediaId1.jpg",
      "order": 1,
      "metadata": {
        "width": 1920,
        "height": 1080,
        "size": 2048576,
        "format": "jpeg"
      }
    },
    "mediaId2": {
      "type": "video",
      "url": "https://cdn.example.com/original/mediaId2.mp4",
      "thumbnailUrl": "https://cdn.example.com/thumb/mediaId2.jpg",
      "previewUrl": "https://cdn.example.com/preview/mediaId2.mp4",
      "order": 2,
      "metadata": {
        "width": 1920,
        "height": 1080,
        "size": 10485760,
        "format": "mp4",
        "duration": 15.5
      }
    }
  },
  "isActive": true,
  "createdAt": "2024-01-01T00:00:00Z",
  "updatedAt": "2024-01-01T12:00:00Z",
  "TTL": 0
}
```

**3. User-Profile Lookup (GSI)**
```json
{
  "PK": "USER#{userId}",
  "SK": "PROFILE#{profileId}",
  "profileId": "profileId",
  "isActive": true,
  "createdAt": "2024-01-01T00:00:00Z"
}
```

**4. Location History**
```json
{
  "PK": "PROFILE#{profileId}",
  "SK": "LOCATION#{timestamp}",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "geohash": "dr5ru",
  "precision": 5,
  "timestamp": "2024-01-01T12:00:00Z",
  "TTL": 604800  // 7 days
}
```

**5. Room Entity**
```json
{
  "PK": "ROOM#{roomId}",
  "SK": "METADATA",
  "name": "Dating Tips",
  "description": "Share dating advice and experiences",
  "category": "dating",
  "subject": "dating_tips",
  "participantCount": 150,
  "activeUserCount": 25,
  "lastActivityAt": "2024-01-01T12:00:00Z",
  "createdAt": "2024-01-01T00:00:00Z",
  "isActive": true,
  "moderationLevel": "community",
  "TTL": 0
}
```

**6. Room Message**
```json
{
  "PK": "ROOM#{roomId}",
  "SK": "MESSAGE#{messageId}",
  "messageId": "messageId",
  "userId": "userId",
  "profileId": "profileId",
  "content": "Message text content",
  "mediaAttachments": [
    {
      "mediaId": "mediaId",
      "type": "image",
      "url": "https://cdn.example.com/room/mediaId.jpg",
      "thumbnailUrl": "https://cdn.example.com/room/thumb/mediaId.jpg"
    }
  ],
  "replyTo": "parentMessageId",  // Optional reply chain
  "timestamp": "2024-01-01T12:00:00Z",
  "isEdited": false,
  "isDeleted": false,
  "deletedAt": null,
  "deletedBy": null,
  "reactions": {
    "like": ["userId1", "userId2"],
    "heart": ["userId3"]
  },
  "TTL": 2592000  // 30 days
}
```

**7. User Block Relationship**
```json
{
  "PK": "USER#{blockerId}",
  "SK": "BLOCK#{blockedId}",
  "blockedUserId": "blockedId",
  "blockedProfileId": "blockedProfileId",
  "reason": "harassment",
  "blockedAt": "2024-01-01T12:00:00Z",
  "isActive": true,
  "TTL": 0
}
```

**8. User Ban Relationship**
```json
{
  "PK": "USER#{bannerId}",
  "SK": "BAN#{bannedId}",
  "bannedUserId": "bannedId",
  "reason": "inappropriate_content",
  "bannedAt": "2024-01-01T12:00:00Z",
  "expiresAt": "2024-02-01T12:00:00Z",  // null for permanent
  "isActive": true,
  "TTL": 0
}
```

**9. Media Entity (for room attachments)**
```json
{
  "PK": "MEDIA#{mediaId}",
  "SK": "METADATA",
  "type": "image|video",
  "originalUrl": "https://cdn.example.com/original/mediaId.jpg",
  "thumbnailUrl": "https://cdn.example.com/thumb/mediaId.jpg",
  "previewUrl": "https://cdn.example.com/preview/mediaId.mp4",  // for videos
  "metadata": {
    "width": 1920,
    "height": 1080,
    "size": 2048576,
    "format": "jpeg|mp4",
    "duration": 15.5  // for videos
  },
  "uploadedBy": "userId",
  "uploadedAt": "2024-01-01T12:00:00Z",
  "isOrphaned": false,
  "TTL": 7776000  // 90 days for orphaned media
}
```

### Global Secondary Indexes (GSIs)

**1. User-Profile Lookup (GSI1)**
- PK: `USER#{userId}`
- SK: `PROFILE#{profileId}`

**2. Location Queries (GSI2)**
- PK: `LOCATION#{geohashPrefix}`
- SK: `PROFILE#{profileId}`

**3. Room Activity (GSI3)**
- PK: `ROOM#{roomId}`
- SK: `ACTIVITY#{timestamp}`

**4. User Activity (GSI4)**
- PK: `USER#{userId}`
- SK: `ACTIVITY#{timestamp}`

**5. Media Management (GSI5)**
- PK: `MEDIA#{mediaId}`
- SK: `OWNER#{userId}`

**6. Block/Ban Lookup (GSI6)**
- PK: `BLOCKED#{blockedId}`
- SK: `BLOCKER#{blockerId}`

## Core Features

### 1. Profile Management
- Users can create up to 3 profiles
- Each profile has independent identity, preferences, media gallery
- Profile switching within the app
- Media upload with frontend processing (crop, zoom, EXIF removal for images; compression for videos)
- Ordered media gallery (user-defined sequence)
- Support for both images and short videos (max 30 seconds)

### 2. Location Services
- Real-time location tracking per profile
- Geohash-based proximity calculations
- Location privacy (precision-controlled)
- Historical location data with TTL

### 3. Communication & Social Features
- **Chat**: Agora.io integration with user-level chat IDs
- **Profile Context**: Frontend passes profile IDs in chat messages
- **Local Storage**: Chat history stored on device
- **Subject Rooms**: Themed discussion rooms for community interaction
- **User Blocking**: Users can block other users from contacting them
- **User Banning**: Community moderation with temporary/permanent bans
- **Active User Tracking**: Real-time presence indicators
- **Typing Indicators**: Show when users are composing messages
- **Message Management**: Edit, delete, and react to messages

### 4. Subject-Based Rooms
- **Room Categories**: Predefined subjects (Dating, Lifestyle, Events, etc.)
- **Public Messaging**: Open discussion within each room
- **Media Support**: Images, videos, and other media in room messages
- **Moderation**: Community-driven content moderation with reporting
- **Real-time Updates**: Live message feeds within rooms
- **Reply Threading**: Support for reply chains within rooms
- **Message Reactions**: Like, heart, and other reaction types
- **Active User Display**: Show currently active users in each room

### 5. Media Management
- **Frontend Processing**: Crop, zoom, rotate, EXIF removal for images; compression for videos
- **Upload Flow**: Processed media -> Backend -> S3 -> CloudFront
- **Backend Processing**: Thumbnail generation, video transcoding, metadata extraction/storage
- **Delivery**: CloudFront CDN URLs for originals, thumbnails, and video previews
- **Cleanup**: TTL-based removal of orphaned media
- **Format Support**: JPEG, PNG for images; MP4, WebM for videos
- **Size Limits**: 10MB for images, 50MB for videos (max 30 seconds)

## Enhanced Agora.io Integration

### Core Chat Services
- **Real-time Messaging**: Instant message delivery between users
- **Message History**: Local storage with optional cloud backup
- **Profile Context**: Messages include sender's active profile information
- **Media Sharing**: Images and videos in private conversations

### Advanced Communication Features
- **Active User Tracking**: Real-time presence indicators showing online/offline status
- **Typing Indicators**: Visual feedback when users are composing messages
- **Message Status**: Delivered, read receipts for message tracking
- **Message Management**: Edit, delete, and recall sent messages
- **Message Reactions**: Emoji reactions to messages (like, heart, etc.)

### User Management & Safety
- **User Blocking**: Block specific users from contacting you
- **User Banning**: Community moderation with temporary/permanent bans
- **Report System**: Report inappropriate users or content
- **Privacy Controls**: Granular privacy settings for profile visibility
- **Block List Management**: View and manage blocked users

### Room-Based Features
- **Room Presence**: Show active users in each subject room
- **Room Typing Indicators**: Show when users are typing in specific rooms
- **Room Message Moderation**: Community-driven content filtering
- **Room User Management**: Kick/ban users from specific rooms
- **Room Analytics**: Track participation and activity levels

### Voice & Video Integration
- **Voice Calls**: One-on-one voice calling capability
- **Video Calls**: Face-to-face video calling with profile context
- **Call Quality**: Adaptive bitrate and quality optimization
- **Call Recording**: Optional call recording with consent
- **Group Calls**: Multi-user voice/video calls for room events

## API Design Patterns

### Authentication
- Telegram WebApp authentication
- JWT tokens for API access
- Profile-level authorization checks

### REST Endpoints Structure
```
GET    /api/v1/users/me                    - Get current user
PUT    /api/v1/users/me/active-profile     - Set active profile

GET    /api/v1/profiles                    - List user profiles
POST   /api/v1/profiles                    - Create new profile
GET    /api/v1/profiles/{id}               - Get profile details
PUT    /api/v1/profiles/{id}               - Update profile
DELETE /api/v1/profiles/{id}               - Delete profile

POST   /api/v1/profiles/{id}/media         - Upload processed media
PUT    /api/v1/profiles/{id}/media/order   - Reorder media
DELETE /api/v1/media/{id}                  - Delete media

PUT    /api/v1/profiles/{id}/location      - Update location
GET    /api/v1/discover                    - Find nearby profiles

GET    /api/v1/rooms                       - Get available rooms
GET    /api/v1/rooms/{id}                  - Get room details
GET    /api/v1/rooms/{id}/messages         - Get room messages
POST   /api/v1/rooms/{id}/messages         - Post message to room
PUT    /api/v1/rooms/{id}/messages/{msgId} - Edit room message
DELETE /api/v1/rooms/{id}/messages/{msgId} - Delete room message
POST   /api/v1/rooms/{id}/media            - Upload media to room
POST   /api/v1/rooms/{id}/messages/{msgId}/reactions - React to message

POST   /api/v1/users/{id}/block            - Block user
DELETE /api/v1/users/{id}/block            - Unblock user
GET    /api/v1/users/blocks                - Get blocked users

POST   /api/v1/users/{id}/ban              - Ban user (moderator only)
DELETE /api/v1/users/{id}/ban              - Unban user (moderator only)
GET    /api/v1/users/bans                  - Get banned users

GET    /api/v1/chat/token                 - Get Agora token for chat/calls
GET    /api/v1/chat/active-users          - Get active users
POST   /api/v1/chat/typing                - Send typing indicator
DELETE /api/v1/chat/typing                - Clear typing indicator

POST   /api/v1/reports                     - Report user/content
GET    /api/v1/reports                     - Get reports (moderator only)
```

### Error Handling
- Standardized error responses
- HTTP status codes
- Client-friendly error messages
- Logging for debugging

## Security & Privacy

### Data Protection
- Profile data isolation
- Location precision control
- Media access validation
- Room message privacy controls
- GDPR compliance with TTL
- User blocking and banning data protection

### API Security
- Input validation and sanitization
- Rate limiting
- CORS configuration
- SQL injection prevention (NoSQL)
- Content moderation for room messages
- User authentication and authorization

### Content Moderation
- Automated content filtering
- Community reporting system
- Moderator tools for room and user management
- Appeal process for content decisions
- Transparent moderation policies
- User safety and protection measures

### Platform Compliance
- Telegram Mini-App guidelines
- App store requirements (if applicable)
- Regional privacy laws (GDPR, CCPA)
- Content moderation policies
- User safety regulations
- Media content guidelines

This enhanced context document provides the comprehensive foundation for implementing the Vibe dating application with advanced media support, detailed DynamoDB schema, and extensive Agora.io integration for real-time communication, user safety, and community features.

