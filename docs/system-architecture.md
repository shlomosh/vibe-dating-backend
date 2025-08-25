# Vibe Dating App - System Architecture & Data Design

## Application Overview

Vibe is a location-based dating application designed as a Telegram Mini-App for the gay community. The app focuses on profile-based interactions, location-aware features, and real-time communication.

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
- **Framework**: Python 3.11+
- **Media Processing**: Thumbnail generation, video transcoding, and metadata extraction

### External Services
- **Chat & Communication**: Agora.io for real-time messaging, voice/video calls, presence management
- **Maps/Location**: Browser geolocation + geohash encoding
- **Media Processing**: Frontend handles initial processing, backend generates thumbnails and video previews

## Service Architecture

### Authentication Service
- **Telegram WebApp Authentication**: Validates Telegram user data
- **JWT Token Management**: Issues and validates JWT tokens
- **API Gateway Integration**: Lambda authorizer for protected endpoints

### User Service
- **Profile Management**: Create, read, update, delete user profiles
- **Media Management**: Image and video handling
- **Location Services**: Real-time location tracking per profile

### Hosting Service
- **Frontend Deployment**: AWS CloudFront + S3
- **Custom Domain**: `tma.vibe-dating.io`
- **SSL/TLS**: AWS Certificate Manager

## Core Infrastructure

### AWS CloudFormation Stacks

The core service provides foundational AWS infrastructure deployed in order:

1. **S3 Stack** (`01-s3.yaml`) - Creates the Lambda code bucket
2. **DynamoDB Stack** (`02-dynamodb.yaml`) - Creates the main database table and KMS key
3. **IAM Stack** (`03-iam.yaml`) - Creates execution roles (depends on S3 and DynamoDB)

#### Stack Details

**S3 Stack**
- **Bucket Name**: `vibe-dating-code-{environment}-{deployment-uuid}`
- **Features**: Versioning, encryption, public access blocking

**DynamoDB Stack**
- **Table Name**: `vibe-dating-{environment}`
- **Features**: Single-table design with 4 GSIs, KMS encryption, point-in-time recovery, pay-per-request billing

**IAM Stack**
- **LambdaExecutionRole**: For Lambda functions with DynamoDB, KMS, S3, and Secrets Manager access
- **ApiGatewayAuthorizerRole**: For API Gateway to invoke Lambda authorizers

## Data Model & Database Schema

### ID System
- All application IDs are **16-character base64 strings**
- User ID: Generated from hash of Telegram user ID (1:1 mapping)
- Profile ID: Unique per profile (max 3 per user)
- Media ID: Unique per media item (max 5 per profile, supporting images and short videos)

### Entity Relationships
```
User (1) -> Profiles (1-3) -> Media (0-5) [images/short-videos]
User (1) -> Profiles (1-3) -> Location History (many)
User (1) -> Agora Chat ID (1)
```

### DynamoDB Schema

#### Single Table Design: `vibe-dating`

**Partition Key (PK) and Sort Key (SK) Structure**
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
  "nickName": "Display Name",
  "aboutMe": "Profile description or bio text",
  "age": "25",
  "sexualPosition": "top",
  "bodyType": "athletic",
  "sexualityType": "gay",
  "eggplantSize": "medium",
  "peachShape": "round",
  "healthPractices": ["regular_testing", "safe_practices"],
  "hivStatus": "negative",
  "preventionPractices": ["prep", "condoms"],
  "hostingType": "can_host",
  "travelDistance": "within_10km",
  "allocatedMediaIds": ["mediaId1", "mediaId2", "mediaId3", "mediaId4", "mediaId5"],
  "activeMediaIds": ["mediaId1", "mediaId2"],
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
  "TTL": 604800
}
```

**5. Profile Media Record (for media processing pipeline)**
```json
{
  "PK": "PROFILE#{profileId}",
  "SK": "MEDIA#{mediaId}",
  "mediaId": "mediaId",
  "profileId": "profileId",
  "userId": "userId",
  "s3Key": "uploads/profile-images/mediaId.jpg",
  "status": "pending",
  "order": 1,
  "metadata": {
    "width": 1920,
    "height": 1080,
    "size": 2048576,
    "format": "jpeg"
  },
  "mediaType": "image",
  "fileSize": 2048576,
  "mimeType": "image/jpeg",
  "dimensions": {
    "width": 1920,
    "height": 1080
  },
  "createdAt": "2024-01-01T00:00:00Z",
  "updatedAt": "2024-01-01T12:00:00Z"
}
```

### Global Secondary Indexes (GSIs)

**GSI1 - Profile Lookup**
- PK: `USER#{userId}`
- SK: `PROFILE#{profileId}`
- Use Case: Query all profiles for a specific user

**GSI2 - Time Lookup**
- PK: `TIME#{datePrefix}`
- SK: `{timestamp}#{entityType}#{entityId}`
- Use Case: Time-based queries for activity, creation times, updates

**GSI3 - Location Lookup**
- PK: `LOCATION#{geohashPrefix}`
- SK: `PROFILE#{profileId}`
- Use Case: Geographic proximity queries for profile matching

## Core Features

### 1. Profile Management
- **Multi-Profile Support**: Up to 3 profiles per user
- **Comprehensive Attributes**: Dating-specific profile fields
- **Media Gallery**: Images and short videos (max 5 per profile)
- **Location Integration**: Profile-based location tracking

### 2. Location Services
- Real-time location tracking per profile
- Geohash-based proximity calculations
- Location privacy (precision-controlled)
- Historical location data with TTL

### 3. Communication & Social Features
- **Chat**: Agora.io integration with user-level chat IDs
- **Profile Context**: Frontend passes profile IDs in chat messages
- **Local Storage**: Chat history stored on device

### 4. Media Management
- **Pre-Allocation Strategy**: Each profile has 5 pre-allocated media IDs for consistent references
- **Upload Flow**: Frontend requests upload URL with base64-encoded metadata -> Backend validates and provides presigned S3 URL -> Client uploads directly to S3 -> Backend confirms upload and triggers processing
- **Backend Processing**: Media status management, S3 operations, and integration with external processing pipeline
- **Storage**: S3 with organized directory structure (`uploads/`, `original/`, `thumb/`)
- **Security**: Presigned URLs with expiration, content validation, and profile ownership verification

## Security & Privacy

### Data Protection
- Profile data isolation
- Location precision control
- Media access validation
- GDPR compliance with TTL

### API Security
- Input validation and sanitization
- Rate limiting
- CORS configuration
- SQL injection prevention (NoSQL)
- User authentication and authorization

### Platform Compliance
- Telegram Mini-App guidelines
- App store requirements (if applicable)
- Regional privacy laws (GDPR, CCPA)
- Content moderation policies
- User safety regulations
- Media content guidelines

### Infrastructure Security
- All resources are tagged with Environment and Service
- DynamoDB uses KMS encryption
- S3 bucket blocks public access
- IAM roles follow least privilege principle
- KMS key policies restrict access appropriately

## Design Principles

### 1. Single Table Design
- All related data stored in one table
- Reduces complexity and improves performance
- Enables efficient joins and queries

### 2. Access Pattern Optimization
- Primary keys designed for most common queries
- GSIs support additional query patterns
- Minimizes data duplication

### 3. Consistent Naming Convention
- **PK Format**: `{ENTITY_TYPE}#{ID}`
- **SK Format**: `{SUBTYPE}` or `{ENTITY_TYPE}#{ID}`
- **GSI Format**: `{QUERY_PATTERN}#{VALUE}`

### 4. Efficient Data Distribution
- Hash keys ensure even distribution across partitions
- Sort keys provide ordering and filtering within partitions
- GSIs enable alternative access patterns

## Frontend Data Models

### Profile System
```typescript
interface ProfileMedia {
  mediaId: string;
  status: 'pending' | 'processing' | 'ready' | 'error';
  order: number;
  s3Key: string;
  metadata: {
    width: number;
    height: number;
    size: number;
    format: string;
  };
  mediaType: 'image' | 'video' | 'audio';
  fileSize?: number;
  mimeType?: string;
  dimensions?: {
    width: number;
    height: number;
  };
  createdAt: string;
  updatedAt: string;
}

interface ProfileRecord {
  nickName?: string;
  aboutMe?: string;
  age?: string;
  sexualPosition?: SexualPositionType;
  bodyType?: BodyType;
  sexualityType?: SexualityType;
  eggplantSize?: EggplantSizeType;
  peachShape?: PeachShapeType;
  healthPractices?: HealthPracticesType[];
  hivStatus?: HivStatusType;
  preventionPractices?: PreventionPracticesType[];
  hostingType?: HostingType;
  travelDistance?: TravelDistanceType;
  allocatedMediaIds: string[];
  activeMediaIds: string[];
}

interface ProfileDB {
  id: ProfileId;
  db: Record<ProfileId, ProfileRecord>;
}
```

### Chat System
```typescript
interface Message {
  id: number;
  text: string;
  isMe: boolean;
  timestamp: Date;
}

interface Conversation {
  profile: ProfileRecord;
  lastMessage: string;
  lastTime: number;
  unreadCount: number;
}
```

## Deployment

### Prerequisites
- AWS CLI installed and configured
- Appropriate AWS credentials/permissions
- Python 3.11+ with boto3

### Deployment Process
```bash
# Deploy to dev environment (default)
python deploy.py

# Deploy to specific environment
python deploy.py --environment staging

# Deploy with specific parameters
python deploy.py --region us-east-1 --profile vibe-dating
```

### Stack Outputs
After successful deployment:
- **LambdaCodeBucketName**: S3 bucket for Lambda code
- **DynamoDBTableName**: Main database table name
- **DynamoDBKMSKeyArn**: KMS key ARN for encryption
- **LambdaExecutionRoleArn**: Lambda execution role ARN
- **ApiGatewayAuthorizerRoleArn**: API Gateway authorizer role ARN

---

*This document provides a comprehensive overview of the Vibe Dating application's system architecture and data design. For specific implementation details, refer to the service-specific documentation.*