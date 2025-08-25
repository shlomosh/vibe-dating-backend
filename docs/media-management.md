# Profile Image Backend Implementation Specification

## Overview

This document specifies the backend implementation for profile image upload, processing, and serving functionality within the User Service. The implementation handles image upload requests, generates thumbnails, stores metadata, and serves images through CloudFront CDN.

## Architecture Components

### Service Location
- **Module**: User Service (`src/services/user/aws_lambdas/user_media_mgmt/`)
- **Handler File**: `lambda_function.py` - Main media management handler

### AWS Resources
- **S3 Bucket**: `vibe-dating-media-{environment}` (configured via `MEDIA_S3_BUCKET` env var)
- **CloudFront Distribution**: Media delivery CDN
- **Lambda Function**: `user_media_mgmt` - Media management API handler
- **DynamoDB**: Metadata storage in main table

## API Endpoints

### 1. Request Upload URL

**Endpoint**: `POST /profiles/{profile_id}/media`

**Purpose**: Allocate media ID and provide presigned S3 upload URL

**Request Headers**:
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body**:
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

**Response**:
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
```

**Implementation**:
```python
def request_upload(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
    # 1. Validate request and decode metadata
    # 2. Get available pre-allocated media ID
    # 3. Generate presigned S3 upload URL
    # 4. Create media record and store pending upload
    # 5. Return response with expiration
```

### 2. Complete Upload

**Endpoint**: `POST /profiles/{profile_id}/media/{media_id}`

**Purpose**: Finalize upload and trigger processing pipeline

**Request Body**:
```json
{
  "uploadSuccess": true,
  "s3ETag": "\"d41d8cd98f00b204e9800998ecf8427e\"",
  "actualSize": 2048576
}
```

**Response**:
```json
{
  "mediaId": "aB3cD4eF",
  "status": "processing",
  "estimatedProcessingTime": 30
}
```

### 3. Delete Media

**Endpoint**: `DELETE /profiles/{profile_id}/media/{media_id}`

**Purpose**: Delete media file and record

**Response**:
```json
{
  "mediaId": "aB3cD4eF",
  "deleted": true,
  "deletedAt": "2024-01-01T12:10:00Z"
}
```

### 4. Reorder Media

**Endpoint**: `PUT /profiles/{profile_id}/media`

**Purpose**: Reorder profile media

**Request Body**:
```json
{
  "imageOrder": ["media_id_1", "media_id_2", "media_id_3"]
}
```

**Response**:
```json
{
  "profileId": "profile123",
  "imageOrder": ["media_id_1", "media_id_2", "media_id_3"],
  "updatedAt": "2024-01-01T12:15:00Z"
}
```

## Data Models

### DynamoDB Schema

#### Profile Media Record
```json
{
  "PK": "PROFILE#{profileId}",
  "SK": "MEDIA#{mediaId}",
  "mediaId": "aB3cD4eF",
  "profileId": "profile123",
  "userId": "user456",
  "s3Key": "uploads/profile-images/aB3cD4eF.jpg",
  "status": "pending",
  "order": 1,
  "metadata": {
    "size": 2048576,
    "format": "jpeg",
    "width": 1440,
    "height": 1920
  },
  "mediaType": "image",
  "fileSize": 2048576,
  "mimeType": "image/jpeg",
  "dimensions": {
    "width": 1440,
    "height": 1920
  },
  "createdAt": "2024-01-01T12:00:00Z",
  "updatedAt": "2024-01-01T12:00:00Z"
}
```

### Python Data Classes

```python
from enum import Enum
from typing import Any, Dict, Optional
import msgspec

class MediaStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"

class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"

class MediaRecord(msgspec.Struct):
    """Media record validation using msgspec"""
    mediaId: str
    profileId: str
    userId: str
    s3Key: str
    status: MediaStatus = MediaStatus.PENDING
    order: int = 1
    metadata: Dict[str, Any] = msgspec.field(default_factory=dict)
    mediaType: Optional[MediaType] = None
    fileSize: Optional[int] = None
    mimeType: Optional[str] = None
    dimensions: Optional[Dict[str, int]] = None
    duration: Optional[float] = None
    error_msg: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
```

## Media Management Flow

### Upload Process

1. **Request Upload URL**
   - Client sends upload request with metadata
   - Server validates request and decodes base64 metadata
   - Server allocates pre-existing media ID from profile
   - Server generates presigned S3 upload URL
   - Server creates pending media record in DynamoDB

2. **Client Upload**
   - Client uploads file directly to S3 using presigned URL
   - S3 stores file in `uploads/profile-images/` directory

3. **Complete Upload**
   - Client confirms successful upload with ETag and actual size
   - Server validates media ID ownership
   - Server updates media status to "processing"
   - Server activates media ID in profile

4. **Image Processing** (External Pipeline)
   - S3 event triggers image processing Lambda
   - Processing generates thumbnail and optimizes image
   - Final images stored in `original/` and `thumb/` directories
   - Media status updated to "ready"

### Media ID Management

The system uses a pre-allocation strategy where:
- Each profile has 5 pre-allocated media IDs (`allocatedMediaIds`)
- Media IDs are moved from allocated to active (`activeMediaIds`) upon successful upload
- This ensures consistent media ID references and prevents conflicts

## Validation & Security

### Input Validation

```python
def validate_upload_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate upload request data and decode metadata"""
    required_fields = ["mediaType", "mediaMeta"]
    
    # Check required fields
    for field in required_fields:
        if field not in request_data:
            raise ResponseError(400, {"error": f"Missing required field: {field}"})
    
    # Validate media type
    if request_data["mediaType"] != "image":
        raise ResponseError(400, {"error": "Only image type supported"})
    
    # Decode and validate metadata
    metadata = self._decode_media_metadata(request_data["mediaMeta"])
    
    # Validate file size and format
    self._validate_file_size(metadata.get("size", 0))
    self._validate_file_format(metadata.get("format", ""))
    
    return metadata
```

### File Validation

```python
def _validate_file_size(self, size: int) -> None:
    """Validate file size against limits"""
    if size > self.core_settings.media_max_file_size:
        raise ResponseError(
            400, 
            {"error": f"File size exceeds limit: {self.core_settings.media_max_file_size}"}
        )

def _validate_file_format(self, format_str: str) -> None:
    """Validate file format against allowed formats"""
    file_format = format_str.lower()
    if file_format not in self.core_settings.media_allowed_formats:
        raise ResponseError(
            400, 
            {"error": f"Unsupported format: {file_format}"}
        )
```

### Access Control

```python
def check_profile_ownership(user_id: str, profile_id: str) -> bool:
    """Verify user owns the profile"""
    profile_mgmt = ProfileManager(user_id)
    return profile_mgmt.validate_profile_id(profile_id, is_existing=True)
```

### S3 Security

```python
def generate_presigned_upload_url(self, media_id: str, content_type: str) -> Dict[str, Any]:
    """Generate secure presigned upload URL"""
    s3_key = f"uploads/profile-images/{media_id}.{content_type.split('/')[-1]}"
    
    presigned_url = self.s3_client.generate_presigned_post(
        Bucket=self.media_bucket,
        Key=s3_key,
        Fields={"Content-Type": content_type},
        Conditions=[
            {"Content-Type": content_type},
            ["content-length-range", 1024, self.core_settings.media_max_file_size],
        ],
        ExpiresIn=self.core_settings.media_upload_expiry_hours * 3600,
    )
    
    return {
        "uploadUrl": presigned_url["url"],
        "uploadMethod": "POST",
        "uploadHeaders": presigned_url["fields"],
        "s3Key": s3_key,
    }
```

## Configuration

### Environment Variables

```python
# S3 Configuration
MEDIA_S3_BUCKET = os.environ.get("MEDIA_S3_BUCKET")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

# Media Configuration
MEDIA_MAX_FILE_SIZE = 10485760  # 10MB
MEDIA_ALLOWED_FORMATS = ["jpeg", "jpg", "png", "webp"]
MEDIA_UPLOAD_EXPIRY_HOURS = 1
MAX_MEDIAS_PER_PROFILE = 5
```

### Core Settings

```python
@dataclass
class CoreSettings:
    record_id_length: int = 8
    max_profiles_count: int = 5
    max_medias_per_profile: int = 5
    media_max_file_size: int = 10485760
    media_allowed_formats: list[str] = ["jpeg", "jpg", "png", "webp"]
    media_upload_expiry_hours: int = 1
```

## Error Handling

### Error Types

```python
class ResponseError(Exception):
    """Custom response error with status code and message"""
    def __init__(self, status_code: int, body: Dict[str, Any]):
        self.status_code = status_code
        self.body = body
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "statusCode": self.status_code,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(self.body)
        }
```

### Common Error Responses

```json
{
  "statusCode": 400,
  "headers": {"Content-Type": "application/json"},
  "body": "{\"error\": \"Invalid mediaMeta format: Invalid base64\"}"
}
```

## Implementation Status

- [x] Create Lambda function handler (`user_media_mgmt`)
- [x] Implement S3 presigned URL generation
- [x] Implement upload request validation
- [x] Implement upload completion handling
- [x] Implement media deletion
- [x] Implement media reordering
- [x] Create DynamoDB operations
- [x] Add input validation and security checks
- [x] Implement error handling and logging
- [ ] Set up S3 event notifications for processing
- [ ] Implement image processing pipeline
- [ ] Create CloudFront invalidation logic
- [ ] Add monitoring and metrics
- [ ] Write unit tests
- [ ] Write integration tests

## Testing Strategy

### Unit Tests
- Upload request validation
- Media ID allocation and activation
- S3 presigned URL generation
- Error handling scenarios

### Integration Tests
- End-to-end upload flow
- S3 operations
- DynamoDB operations
- Profile ownership validation

### Load Tests
- Concurrent upload handling
- Media ID allocation performance
- S3 throughput limits