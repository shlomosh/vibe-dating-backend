# Profile Image Backend Implementation Specification

## Overview

This document specifies the backend implementation for profile image upload, processing, and serving functionality within the User Service. The implementation handles image upload requests, generates thumbnails, stores metadata, and serves images through CloudFront CDN.

## Architecture Components

### Service Location
- **Module**: Media Service (`src/services/media/`)
- **Handler Files**: 
  - `media_upload.py` - Upload request handling
  - `media_processing.py` - Image processing pipeline
  - `media_management.py` - CRUD operations

### AWS Resources
- **S3 Bucket**: `vibe-dating-media-{environment}`
- **CloudFront Distribution**: Media delivery CDN
- **Lambda Functions**: Image processing and API handlers (prefixed with `media_`)
- **DynamoDB**: Metadata storage in main table

## API Endpoints

### 1. Request Upload URL

**Endpoint**: `POST /profiles/{profile_id}/media/request-upload`

**Purpose**: Allocate media ID and provide presigned S3 upload URL

**Request Headers**:
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body**:
```json
{
  "type": "image",
  "aspectRatio": "3:4",
  "metadata": {
    "width": 1440,
    "height": 1920,
    "size": 2048576,
    "format": "jpeg",
    "aspect": "3:4",
    "camera": "iPhone 12 Pro",
    "software": "iOS 17.0",
    "timestamp": "2024-01-01T12:00:00Z",
    "location": null,
    "flags": "",
  },
  "order": 1
}
```

**Response**:
```json
{
  "mediaId": "aB3cD4eF",
  "uploadUrl": "https://s3.amazonaws.com/vibe-dating-media-prod/uploads/profile-images/aB3cD4eF.jpg?X-Amz-Algorithm=...",
  "uploadMethod": "PUT",
  "uploadHeaders": {
    "Content-Type": "image/jpeg"
  },
  "expiresAt": "2024-01-01T13:00:00Z"
}
```

**Implementation**:
```python
def request_upload_url(profile_id: str, request_data: dict) -> dict:
    # 1. Validate user owns profile
    # 2. Check profile image limit (max 5)
    # 3. Generate unique media ID
    # 4. Create presigned S3 upload URL
    # 5. Store pending upload record in DynamoDB
    # 6. Return response
```

### 2. Complete Upload

**Endpoint**: `POST /profiles/{profile_id}/media/{media_id}/complete`

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

### 3. Get Processing Status

**Endpoint**: `GET /profiles/{profile_id}/media/{media_id}/status`

**Response**:
```json
{
  "mediaId": "aB3cD4eF",
  "status": "completed",
  "urls": {
    "original": "https://cdn.vibe-dating.io/original/aB3cD4eF.jpg",
    "thumbnail": "https://cdn.vibe-dating.io/thumb/aB3cD4eF.jpg"
  },
  "processedAt": "2024-01-01T12:05:00Z"
}
```

### 4. Delete Image

**Endpoint**: `DELETE /profiles/{profile_id}/media/{media_id}`

**Response**:
```json
{
  "mediaId": "aB3cD4eF",
  "deleted": true,
  "deletedAt": "2024-01-01T12:10:00Z"
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
  "type": "image",
  "status": "completed",
  "order": 1,
  "originalUrl": "https://cdn.vibe-dating.io/original/aB3cD4eF.jpg",
  "thumbnailUrl": "https://cdn.vibe-dating.io/thumb/aB3cD4eF.jpg",
  "metadata": {
    "width": 1440,
    "height": 1920,
    "size": 2048576,
    "format": "jpeg",
    "aspect": "3:4",
    "camera": "iPhone 12 Pro",
    "software": "iOS 17.0",
    "timestamp": "2024-01-01T12:00:00Z",
    "location": null,
    "flags": "",
  },
  "s3Key": "profile-images/aB3cD4eF.jpg",
  "s3Bucket": "vibe-dating-media-prod",
  "uploadedAt": "2024-01-01T12:00:00Z",
  "processedAt": "2024-01-01T12:05:00Z",
  "createdAt": "2024-01-01T12:00:00Z",
  "updatedAt": "2024-01-01T12:05:00Z",
  "TTL": 0
}
```

#### Pending Upload Record
```json
{
  "PK": "UPLOAD#{mediaId}",
  "SK": "PENDING",
  "mediaId": "aB3cD4eF",
  "profileId": "profile123",
  "userId": "user456",
  "status": "pending",
  "uploadUrl": "https://s3.amazonaws.com/...",
  "expiresAt": "2024-01-01T13:00:00Z",
  "createdAt": "2024-01-01T12:00:00Z",
  "TTL": 1704110400
}
```

### Python Data Classes

```python
from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum

class MediaStatus(Enum):
    PENDING = "pending"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ImageMetadata:
    # all strings size should be limited to maximum 32 chars.
    width: int
    height: int
    size: int
    format: str
    aspect: str
    camera: Optional[str] = None
    software: Optional[str] = None
    timestamp: Optional[str] = None
    location: Optional[Dict[str, float]] = None
    flags: Optional[str] = None

@dataclass
class ProfileImage:
    media_id: str
    profile_id: str
    user_id: str
    type: str
    status: MediaStatus
    order: int
    original_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    metadata: Optional[ImageMetadata] = None
    s3_key: Optional[str] = None
    s3_bucket: Optional[str] = None
    uploaded_at: Optional[str] = None
    processed_at: Optional[str] = None
    created_at: str
    updated_at: str
```

## Image Processing Pipeline

### Processing Workflow

1. **Upload Completion Detection**
   - S3 Event Notification triggers Lambda
   - Validate upload integrity (ETag, size)
   - Update status to "processing"

2. **Image Processing**
   - Download original image from S3
   - Validate image format and dimensions
   - Generate thumbnail (300x400px, maintaining aspect ratio)
   - Optimize images (compression, format conversion if needed)

3. **Storage & CDN**
   - Upload processed images to S3
   - Invalidate CloudFront cache if needed
   - Update DynamoDB with final URLs and metadata

4. **Cleanup**
   - Remove temporary files
   - Update status to "completed"
   - Send completion notification if needed

### Processing Function

```python
def process_profile_image(media_id: str, s3_bucket: str, s3_key: str):
    """
    Process uploaded profile image
    
    Args:
        media_id: Unique media identifier
        s3_bucket: S3 bucket name
        s3_key: S3 object key
    """
    try:
        # Update status to processing
        update_media_status(media_id, MediaStatus.PROCESSING)
        
        # Download original image
        original_image = download_from_s3(s3_bucket, s3_key)
        
        # Validate image
        validate_image(original_image)
        
        # Generate thumbnail
        thumbnail = generate_thumbnail(original_image, (300, 400))
        
        # Upload processed images
        original_url = upload_to_s3_and_cdn(original_image, f"original/{media_id}.jpg")
        thumbnail_url = upload_to_s3_and_cdn(thumbnail, f"thumb/{media_id}.jpg")
        
        # Update record with URLs
        update_media_record(media_id, {
            'status': MediaStatus.COMPLETED,
            'original_url': original_url,
            'thumbnail_url': thumbnail_url,
            'processed_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        update_media_status(media_id, MediaStatus.FAILED)
        raise e
```

## Validation & Security

### Input Validation

```python
def validate_upload_request(request_data: dict) -> bool:
    """Validate upload request data"""
    required_fields = ['type', 'aspectRatio', 'metadata']
    
    # Check required fields
    for field in required_fields:
        if field not in request_data:
            raise ValidationError(f"Missing required field: {field}")
    
    # Validate image type
    if request_data['type'] != 'image':
        raise ValidationError("Only image type supported")
    
    # Validate aspect ratio
    if request_data['aspectRatio'] != '3:4':
        raise ValidationError("Only 3:4 aspect ratio supported")
    
    # Validate metadata
    metadata = request_data['metadata']
    if metadata['size'] > MAX_FILE_SIZE:
        raise ValidationError(f"File size exceeds limit: {MAX_FILE_SIZE}")
    
    if metadata['format'] not in ALLOWED_FORMATS:
        raise ValidationError(f"Unsupported format: {metadata['format']}")
    
    return True
```

### Access Control

```python
def check_profile_ownership(user_id: str, profile_id: str) -> bool:
    """Verify user owns the profile"""
    profile = get_profile_by_id(profile_id)
    return profile and profile.user_id == user_id

def check_image_limit(profile_id: str) -> bool:
    """Check if profile has reached image limit"""
    current_count = count_profile_images(profile_id)
    return current_count < MAX_IMAGES_PER_PROFILE
```

### S3 Security

```python
def generate_presigned_upload_url(bucket: str, key: str, content_type: str) -> dict:
    """Generate secure presigned upload URL"""
    return s3_client.generate_presigned_post(
        Bucket=bucket,
        Key=key,
        Fields={
            'Content-Type': content_type
        },
        Conditions=[
            {'Content-Type': content_type},
            ['content-length-range', 1024, MAX_FILE_SIZE]
        ],
        ExpiresIn=3600  # 1 hour
    )
```

## Error Handling

### Error Types

```python
class ProfileImageError(Exception):
    """Base exception for profile image operations"""
    pass

class ValidationError(ProfileImageError):
    """Invalid input data"""
    pass

class PermissionError(ProfileImageError):
    """Access denied"""
    pass

class ProcessingError(ProfileImageError):
    """Image processing failed"""
    pass

class StorageError(ProfileImageError):
    """S3/storage operation failed"""
    pass
```

### Error Responses

```python
def handle_error(error: Exception) -> dict:
    """Convert exceptions to API error responses"""
    error_mapping = {
        ValidationError: (400, "VALIDATION_ERROR"),
        PermissionError: (403, "PERMISSION_DENIED"),
        ProcessingError: (422, "PROCESSING_FAILED"),
        StorageError: (500, "STORAGE_ERROR")
    }
    
    status_code, error_code = error_mapping.get(type(error), (500, "INTERNAL_ERROR"))
    
    return {
        "error": {
            "code": error_code,
            "message": str(error),
            "timestamp": datetime.utcnow().isoformat()
        }
    }, status_code
```

## Configuration

### Environment Variables

```python
# S3 Configuration
S3_BUCKET_NAME = os.environ.get("MEDIA_S3_BUCKET")
S3_REGION = os.environ.get("AWS_REGION", "us-east-1")

# CloudFront Configuration
CLOUDFRONT_DOMAIN = os.environ.get("CLOUDFRONT_DOMAIN")
CLOUDFRONT_DISTRIBUTION_ID = os.environ.get("CLOUDFRONT_DISTRIBUTION_ID")

# Image Processing Configuration
MAX_FILE_SIZE = int(os.environ.get("MAX_FILE_SIZE", "10485760"))  # 10MB
MAX_IMAGES_PER_PROFILE = int(os.environ.get("MAX_IMAGES_PER_PROFILE", "5"))
ALLOWED_FORMATS = ["jpeg", "jpg", "png", "webp"]

# Thumbnail Configuration
THUMBNAIL_WIDTH = 300
THUMBNAIL_HEIGHT = 400
THUMBNAIL_QUALITY = 85
```

## Implementation Checklist

- [ ] Create Lambda function handlers
- [ ] Implement S3 presigned URL generation
- [ ] Set up S3 event notifications for processing
- [ ] Implement image processing pipeline
- [ ] Create DynamoDB operations
- [ ] Add input validation and security checks
- [ ] Implement error handling and logging
- [ ] Create CloudFront invalidation logic
- [ ] Add monitoring and metrics
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Create deployment scripts

## Testing Strategy

### Unit Tests
- Upload request validation
- Media ID generation
- S3 operations
- Image processing functions
- Error handling

### Integration Tests
- End-to-end upload flow
- S3 event processing
- CloudFront integration
- DynamoDB operations

### Load Tests
- Concurrent upload handling
- Processing pipeline performance
- S3 throughput limits