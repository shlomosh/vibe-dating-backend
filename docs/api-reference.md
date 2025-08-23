# API Reference - Vibe Dating Backend

## Overview

The Vibe Backend API is a RESTful API built with FastAPI and deployed on AWS Lambda via API Gateway. It provides endpoints for user authentication, profile management, location-based matching, and real-time communication.

## Base URL

- **Development**: `https://api-dev.vibe-dating.io`
- **Staging**: `https://api-staging.vibe-dating.io`
- **Production**: `https://api.vibe-dating.io`

## Authentication

All API endpoints (except authentication endpoints) require a valid JWT token in the Authorization header:

```
Authorization: Bearer <jwt_token>
```

### JWT Token Format

JWT tokens are issued after successful Telegram authentication and contain the following claims:

- `user_id`: Vibe user ID
- `telegram_id`: Telegram user ID
- `iat`: Issued at timestamp
- `exp`: Expiration timestamp
- `iss`: Issuer (vibe-app)

## API Endpoints

### Authentication

#### POST /auth/telegram
Authenticate user with Telegram WebApp data.

**Request Body:**
```json
{
  "init_data": "telegram_init_data_string",
  "telegram_user": {
    "id": 123456789,
    "username": "username",
    "first_name": "First",
    "last_name": "Last",
    "language_code": "en",
    "is_premium": false,
    "photo_url": "https://example.com/photo.jpg"
  }
}
```

**Response:**
```json
{
  "token": "jwt_token_string",
  "user_id": "user_id",
  "user": {
    "user_id": "user_id",
    "telegram_username": "username",
    "is_banned": false,
    "preferences": {},
    "createdAt": "2024-01-01T00:00:00Z"
  },
  "expires_at": "2024-01-08T00:00:00Z"
}
```

#### GET /auth/me
Get current user information.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "user_id": "user_id",
  "platform": "tg",
  "platform_id": "123456789",
  "platform_metadata": {
    "username": "username",
    "first_name": "John",
    "last_name": "Doe",
    "language_code": "en",
    "is_premium": false,
    "added_to_attachment_menu": false
  },
  "is_banned": false,
  "ban_reason": null,
  "ban_expires_at": null,
  "preferences": {
    "notifications": true,
    "privacy": "public",
    "language": "en",
    "theme": "auto"
  },
  "last_active_at": "2024-01-01T12:00:00Z",
  "createdAt": "2024-01-01T00:00:00Z"
}
```

#### POST /auth/refresh
Refresh JWT token.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "token": "new_jwt_token_string",
  "expires_at": "2024-01-08T00:00:00Z"
}
```

### User Management

#### PUT /users/me
Update current user information.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Request Body:**
```json
{
  "preferences": {
    "notifications": true,
    "privacy": "public",
    "language": "en",
    "theme": "auto"
  },
  "agora_chat_id": "agora_chat_id"
}
```

### Profile Management

#### GET /profile/{profileId}
Get a specific profile by ID.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "profileId": "profile_id",
  "userId": "user_id",
  "nickName": "Display Name",
  "aboutMe": "Profile description",
  "age": "25",
  "sexualPosition": "vers",
  "bodyType": "fit",
  "eggplantSize": "average",
  "peachShape": "average",
  "healthPractices": "regular_exercise",
  "hivStatus": "negative",
  "preventionPractices": "prep",
  "hosting": "hostAndTravel",
  "travelDistance": "city",
  "profileImages": [
    {
      "imageId": "image_id",
      "imageUrl": "https://media.vibe-dating.io/original/image_id.jpg",
      "imageThumbnailUrl": "https://media.vibe-dating.io/thumb/image_id.jpg",
      "imageAttributes": {
        "width": "1920",
        "height": "1080",
        "format": "jpeg"
      }
    }
  ],
  "createdAt": "2024-01-01T00:00:00Z",
  "updatedAt": "2024-01-01T12:00:00Z"
}
```

#### PUT /profile/{profileId}
Create or update a profile (upsert operation).

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Request Body:**
```json
{
  "nickName": "Display Name",
  "aboutMe": "Profile description",
  "age": "25",
  "sexualPosition": "vers",
  "bodyType": "fit",
  "eggplantSize": "average",
  "peachShape": "average",
  "healthPractices": "regular_exercise",
  "hivStatus": "negative",
  "preventionPractices": "prep",
  "hosting": "hostAndTravel",
  "travelDistance": "city",
  "profileImages": [
    {
      "imageId": "image_id",
      "imageUrl": "https://media.vibe-dating.io/original/image_id.jpg",
      "imageThumbnailUrl": "https://media.vibe-dating.io/thumb/image_id.jpg",
      "imageAttributes": {
        "width": "1920",
        "height": "1080",
        "format": "jpeg"
      }
    }
  ]
}
```

**Response:**
```json
{
  "profileId": "profile_id",
  "success": true,
  "message": "Profile updated successfully"
}
```

#### DELETE /profile/{profileId}
Delete a profile and associated media.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "profileId": "profile_id",
  "success": true,
  "message": "Profile deleted successfully"
}
```

### Location Services

#### PUT /profile/{profileId}/location
Update profile location.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Request Body:**
```json
{
  "latitude": 40.7128,
  "longitude": -74.0060,
  "precision": 5
}
```

#### GET /discover
Discover nearby profiles.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `latitude` (required): Current latitude
- `longitude` (required): Current longitude
- `radiusKm` (optional): Search radius in kilometers (default: 50)
- `limit` (optional): Maximum number of results (default: 20)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "items": [
    {
      "profile": {
        "profileId": "profile_id",
        "userId": "user_id",
        "name": "Profile Name",
        "age": 25,
        "bio": "Profile description",
        "interests": ["music", "travel"],
        "lookingFor": ["friendship", "relationship"],
        "location": {
          "latitude": 40.7128,
          "longitude": -74.0060,
          "geohash": "dr5ru",
          "precision": 5,
          "lastUpdated": "2024-01-01T12:00:00Z"
        },
        "media": [],
        "isActive": true,
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T12:00:00Z"
      },
      "distance_km": 2.5,
      "geohash_match": "dr5ru"
    }
  ],
  "total": 150,
  "limit": 20,
  "offset": 0,
  "has_more": true
}
```

### Media Management

Media management endpoints for profile image upload, processing, and management.

#### POST /profiles/{profile_id}/media
Request upload URL for media.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Request Body:**
```json
{
  "mediaType": "image",
  "mediaMeta": "base64_encoded_metadata",
  "mediaOrder": 1
}
```

**Metadata Format** (base64 encoded):
```json
{
  "size": 2048576,
  "format": "jpeg",
  "width": 1440,
  "height": 1920
}
```

**Response:**
```json
{
  "mediaId": "aB3cD4eF",
  "uploadUrl": "https://s3.amazonaws.com/vibe-dating-media-prod/uploads/profile-images/aB3cD4eF.jpg?X-Amz-Algorithm=...",
  "uploadMethod": "POST",
  "uploadHeaders": {
    "Content-Type": "image/jpeg",
    "key": "uploads/profile-images/aB3cD4eF.jpg",
    "policy": "...",
    "x-amz-algorithm": "AWS4-HMAC-SHA256",
    "x-amz-credential": "...",
    "x-amz-date": "...",
    "x-amz-signature": "..."
  },
  "expiresAt": "2024-01-01T13:00:00Z"
}

#### POST /profiles/{profile_id}/media/{media_id}
Complete media upload and trigger processing.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Request Body:**
```json
{
  "uploadSuccess": true,
  "s3ETag": "\"d41d8cd98f00b204e9800998ecf8427e\"",
  "actualSize": 2048576
}
```

**Response:**
```json
{
  "mediaId": "aB3cD4eF",
  "status": "processing",
  "estimatedProcessingTime": 30
}
```



#### PUT /profiles/{profile_id}/media
Reorder profile media.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Request Body:**
```json
{
  "imageOrder": ["media_id_1", "media_id_2", "media_id_3"]
}
```

**Response:**
```json
{
  "profileId": "profile123",
  "imageOrder": ["media_id_1", "media_id_2", "media_id_3"],
  "updatedAt": "2024-01-01T12:15:00Z"
}
```

#### DELETE /profiles/{profile_id}/media/{media_id}
Delete media file.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "mediaId": "aB3cD4eF",
  "deleted": true,
  "deletedAt": "2024-01-01T12:10:00Z"
}
```

### Agora Integration

#### GET /agora/token
Get Agora token for real-time communication.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `channel_name` (required): Channel name for RTC
- `uid` (required): User ID for RTC

**Response:**
```json
{
  "rtc_token": "agora_rtc_token",
  "rtm_token": "agora_rtm_token",
  "app_id": "agora_app_id",
  "expires_at": "2024-01-01T13:00:00Z"
}
```

#### GET /agora/active-users
Get active users in a channel.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `channel_name` (required): Channel name

**Response:**
```json
{
  "channel_name": "channel_name",
  "user_count": 25,
  "active_users": [
    {
      "user_id": "user_id",
      "profile_id": "profile_id",
      "online": true,
      "last_seen": "2024-01-01T12:00:00Z"
    }
  ]
}
```

### User Blocking

#### POST /users/{user_id}/block
Block a user.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Request Body:**
```json
{
  "reason": "harassment"
}
```

#### DELETE /users/{user_id}/block
Unblock a user.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

#### GET /users/blocks
Get list of blocked users.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
[
  {
    "blocked_user_id": "user_id",
    "blocked_profile_id": "profile_id",
    "reason": "harassment",
    "blocked_at": "2024-01-01T12:00:00Z"
  }
]
```

## Error Responses

All endpoints return consistent error responses:

```json
{
  "error": "Error message",
  "error_code": "ERROR_CODE",
  "details": {
    "field": "Additional error details"
  }
}
```

### Common HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required or invalid
- `403 Forbidden`: Access denied
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Rate Limiting

API requests are rate limited to prevent abuse:

- **Authentication endpoints**: 10 requests per minute
- **Other endpoints**: 100 requests per hour per user

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Pagination

List endpoints support pagination with the following query parameters:

- `limit`: Number of items per page (default: 20, max: 100)
- `offset`: Number of items to skip (default: 0)
- `sort_by`: Field to sort by
- `sort_order`: Sort order ("asc" or "desc", default: "desc")

Pagination metadata is included in responses:

```json
{
  "items": [...],
  "total": 150,
  "limit": 20,
  "offset": 0,
  "has_more": true
}
```

## Domain Configuration

The API is configured with custom domains for each environment:

### Development Environment
- **Domain**: `api-dev.vibe-dating.io`
- **SSL**: AWS Certificate Manager certificate
- **DNS**: Route53 hosted zone

### Staging Environment
- **Domain**: `api-staging.vibe-dating.io`
- **SSL**: AWS Certificate Manager certificate
- **DNS**: Route53 hosted zone

### Production Environment
- **Domain**: `api.vibe-dating.io`
- **SSL**: AWS Certificate Manager certificate
- **DNS**: Route53 hosted zone

### Media Domain
- **Domain**: `media.vibe-dating.io` (production only)
- **CDN**: CloudFront distribution
- **Storage**: S3 bucket with CloudFront origin

## SSL/TLS Configuration

All custom domains use SSL certificates managed by AWS Certificate Manager:

- **Certificate Type**: Regional certificate for API Gateway
- **Validation Method**: DNS validation
- **Security Policy**: TLS 1.2
- **Auto-renewal**: Enabled

## DNS Configuration

The infrastructure uses Route53 for DNS management:

- **Hosted Zone**: `vibe-dating.io`
- **A Records**: Point to API Gateway custom domain
- **CNAME Records**: For SSL certificate validation
- **Nameservers**: Route53 nameservers for the domain 