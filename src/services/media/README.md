# Media Service

The Media Service handles profile image upload, processing, and management for the Vibe Dating App.

## Overview

This service provides:
- **Image Upload**: Secure presigned URL generation for direct S3 uploads
- **Image Processing**: Automatic thumbnail generation and optimization
- **Media Management**: Status checking, deletion, and reordering
- **CDN Delivery**: CloudFront-based media delivery

## Architecture

### Components

1. **Media Upload Lambda**: Handles upload requests and completion
2. **Media Processing Lambda**: Processes uploaded images (S3 event-triggered)
3. **Media Management Lambda**: Manages media CRUD operations
4. **S3 Bucket**: Media storage with versioning and encryption
5. **CloudFront Distribution**: CDN for media delivery

### Data Flow

1. **Upload Request**: Client requests upload URL with metadata
2. **Direct Upload**: Client uploads image directly to S3
3. **Processing Trigger**: S3 event triggers processing Lambda
4. **Image Processing**: Generate thumbnails and optimize images
5. **CDN Delivery**: Serve images through CloudFront

## API Endpoints

### 1. Request Upload URL

**POST** `/profiles/{profileId}/media`

Request a presigned upload URL for a new image.

**Request Body:**
```json
{
  "type": "image",
  "aspectRatio": "3:4",
  "metadata": {
    "width": 1440,
    "height": 1920,
    "size": 2048576,
    "format": "jpeg",
    "camera": "iPhone 12 Pro",
    "software": "iOS 17.0",
    "timestamp": "2024-01-01T12:00:00Z"
  },
  "order": 1
}
```

**Response:**
```json
{
  "mediaId": "aB3cD4eF",
  "uploadUrl": "https://s3.amazonaws.com/...",
  "uploadMethod": "POST",
  "uploadHeaders": {
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

### 2. Complete Upload

**POST** `/profiles/{profileId}/media/{mediaId}/complete`

Finalize upload and trigger processing.

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

### 3. Get Media Status

**GET** `/profiles/{profileId}/media/{mediaId}/status`

Check processing status and get URLs.

**Response:**
```json
{
  "mediaId": "aB3cD4eF",
  "status": "completed",
  "urls": {
    "original": "https://cdn.vibe-dating.io/original/aB3cD4eF.jpg",
    "thumbnail": "https://cdn.vibe-dating.io/thumb/aB3cD4eF.jpg"
  },
  "processedAt": "2024-01-01T12:05:00Z",
  "metadata": {
    "width": 1440,
    "height": 1920,
    "size": 2048576,
    "format": "jpeg"
  }
}
```

### 4. List Profile Media

**GET** `/profiles/{profileId}/media`

List all media for a profile.

**Response:**
```json
{
  "profileId": "profile123",
  "media": [
    {
      "mediaId": "aB3cD4eF",
      "status": "completed",
      "order": 1,
      "urls": {
        "original": "https://cdn.vibe-dating.io/original/aB3cD4eF.jpg",
        "thumbnail": "https://cdn.vibe-dating.io/thumb/aB3cD4eF.jpg"
      },
      "metadata": {
        "width": 1440,
        "height": 1920,
        "size": 2048576,
        "format": "jpeg"
      },
      "uploadedAt": "2024-01-01T12:00:00Z",
      "processedAt": "2024-01-01T12:05:00Z"
    }
  ]
}
```

### 5. Reorder Media

**PUT** `/profiles/{profileId}/media/order`

Reorder profile media.

**Request Body:**
```json
{
  "imageOrder": ["mediaId1", "mediaId2", "mediaId3"]
}
```

**Response:**
```json
{
  "profileId": "profile123",
  "imageOrder": ["mediaId1", "mediaId2", "mediaId3"],
  "updatedAt": "2024-01-01T12:10:00Z"
}
```

### 6. Delete Media

**DELETE** `/profiles/{profileId}/media/{mediaId}`

Delete media file and record.

**Response:**
```json
{
  "mediaId": "aB3cD4eF",
  "deleted": true,
  "deletedAt": "2024-01-01T12:10:00Z"
}
```

## Configuration

### Environment Variables

- `MEDIA_S3_BUCKET`: S3 bucket for media storage
- `CLOUDFRONT_DOMAIN`: CloudFront distribution domain
- `CLOUDFRONT_DISTRIBUTION_ID`: CloudFront distribution ID
- `DYNAMODB_TABLE`: DynamoDB table name
- `MAX_FILE_SIZE`: Maximum file size (default: 10485760 = 10MB)
- `MAX_IMAGES_PER_PROFILE`: Maximum images per profile (default: 5)

### Image Processing Settings

- **Thumbnail Size**: 300x400px (3:4 aspect ratio)
- **Thumbnail Quality**: 85%
- **Original Max Size**: 1920px (width or height)
- **Supported Formats**: JPEG, PNG, WebP
- **Cache Control**: 1 year for processed images

## Development

### Building

```bash
# Build media service Lambda packages
poetry run build-media

# Or use the generic service build
poetry run service-build media
```

### Testing

```bash
# Run all media service tests
poetry run service-test media

# Run individual test categories
python src/services/media/aws_lambdas/test/test_structure.py
python src/services/media/aws_lambdas/test/test_layer.py
python src/services/media/aws_lambdas/test/test_functional.py
```

### Deployment

```bash
# Deploy media service infrastructure
poetry run service-deploy media

# Update Lambda functions only
poetry run service-update media
```

## Security

### Access Control

- All endpoints require JWT authentication
- Profile ownership verification for all operations
- S3 bucket access restricted to CloudFront OAI
- Presigned URLs with expiration and size limits

### Data Protection

- S3 bucket encryption at rest
- CloudFront HTTPS-only delivery
- DynamoDB encryption at rest
- TTL-based cleanup for orphaned media

## Monitoring

### CloudWatch Logs

- `/aws/lambda/vibe-media-upload-{environment}`
- `/aws/lambda/vibe-media-processing-{environment}`
- `/aws/lambda/vibe-media-management-{environment}`

### Key Metrics

- Upload success/failure rates
- Processing time and success rates
- CDN cache hit rates
- Storage usage and costs

## Troubleshooting

### Common Issues

1. **Upload Failures**: Check file size limits and format support
2. **Processing Failures**: Verify S3 event notifications and Lambda permissions
3. **CDN Issues**: Check CloudFront distribution status and cache invalidation
4. **Permission Errors**: Verify IAM roles and DynamoDB access

### Debug Steps

1. Check CloudWatch logs for error details
2. Verify S3 bucket permissions and event notifications
3. Test Lambda functions with sample events
4. Validate DynamoDB table structure and access 