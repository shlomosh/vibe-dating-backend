# Profile Management Backend

## Overview

The Profile Management Backend provides comprehensive CRUD operations for user profiles in the Vibe Dating application. It handles profile creation, updates, retrieval, and deletion with strong validation and security controls.

## Implementation Status

✅ **Fully Implemented**:
- Profile CRUD operations
- Comprehensive data validation  
- Authentication and authorization
- DynamoDB storage with transactions
- Profile ownership verification

🚧 **In Development**:
- Media upload and processing pipeline
- Location-based services
- Advanced search capabilities

## Architecture

### Service Location
- **Module**: User Service (`src/services/user/`)
- **Handler**: `aws_lambdas/user_profile_mgmt/lambda_function.py`
- **API Gateway**: `/profile/{profileId}` endpoints
- **Data Layer**: `src/common/aws_lambdas/core/profile_utils.py`

### Data Models

#### ProfileRecord Structure

```python
class ProfileRecord(msgspec.Struct):
    nickName: Optional[str] = msgspec.field(max_length=32, default=None)
    aboutMe: Optional[str] = msgspec.field(max_length=512, default=None)
    age: Optional[str] = msgspec.field(max_length=8, default=None)
    sexualPosition: Optional[SexualPosition] = None
    bodyType: Optional[BodyType] = None
    eggplantSize: Optional[EggplantSizeType] = None
    peachShape: Optional[PeachShapeType] = None
    healthPractices: Optional[HealthPracticesType] = None
    hivStatus: Optional[HivStatusType] = None
    preventionPractices: Optional[PreventionPracticesType] = None
    hosting: Optional[HostingType] = None
    travelDistance: Optional[TravelDistanceType] = None
    profileImages: List[ProfileImage] = msgspec.field(default_factory=list, max_length=10)
```

#### ProfileImage Structure

```python
class ProfileImage(msgspec.Struct):
    imageId: str
    imageUrl: str
    imageThumbnailUrl: str
    imageAttributes: Dict[str, str] = msgspec.field(default_factory=dict)
```

### Available Enums

#### Sexual Preferences
```python
class SexualPosition(Enum):
    bottom = "bottom"
    vers = "vers" 
    top = "top"
    side = "side"
    oral = "oral"
```

#### Physical Attributes
```python
class BodyType(Enum):
    petite = "petite"
    slim = "slim"
    average = "average"
    fit = "fit"
    muscular = "muscular"
    stocky = "stocky"
    chubby = "chubby"
    bear = "bear"
```

#### Health & Safety
```python
class HivStatusType(Enum):
    negative = "negative"
    positive = "positive"
    positive_undetectable = "positive_undetectable"
    unknown = "unknown"
    prefer_not_to_say = "prefer_not_to_say"

class PreventionPracticesType(Enum):
    prep = "prep"
    condoms = "condoms"
    both = "both"
    other = "other"
    none = "none"
```

#### Logistics
```python
class HostingType(Enum):
    hostAndTravel = "hostAndTravel"
    hostOnly = "hostOnly"
    travelOnly = "travelOnly"

class TravelDistanceType(Enum):
    none = "none"
    block = "block"
    neighbourhood = "neighbourhood"
    city = "city"
    metropolitan = "metropolitan"
    state = "state"
```

## API Endpoints

### GET /profile/{profileId}

**Purpose**: Retrieve a specific profile by ID

**Authentication**: JWT Bearer token required

**Response**:
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
        "format": "jpeg",
        "flags": "",
      }
    }
  ],
  "createdAt": "2024-01-01T00:00:00Z",
  "updatedAt": "2024-01-01T12:00:00Z"
}
```

### PUT /profile/{profileId}

**Purpose**: Create or update a profile (upsert operation)

**Authentication**: JWT Bearer token required

**Request Body**: Any subset of ProfileRecord fields

**Response**:
```json
{
  "profileId": "profile_id",
  "success": true,
  "message": "Profile updated successfully"
}
```

### DELETE /profile/{profileId}

**Purpose**: Delete a profile and associated media

**Authentication**: JWT Bearer token required

**Response**:
```json
{
  "profileId": "profile_id",
  "success": true,
  "message": "Profile deleted successfully"
}
```

## Implementation Details

### ProfileManager Class

```python
class ProfileManager(CommonManager):
    def create(self, profile_id: str, profile_record: Dict[str, Any]) -> bool
    def update(self, profile_id: str, profile_record: Dict[str, Any]) -> bool
    def upsert(self, profile_id: str, profile_record: Dict[str, Any]) -> bool
    def delete(self, profile_id: str) -> bool
    def get(self, profile_id: str) -> Dict[str, Any]
    def validate_profile_record(self, profile_record: Dict[str, Any]) -> ProfileRecord
    def validate_profile_id(self, profile_id: str, is_existing: bool = False) -> bool
```

### Data Storage

**DynamoDB Table**: `vibe-dating-{environment}`

**Primary Record Pattern**:
```
PK: "PROFILE#{profileId}"
SK: "METADATA"
```

**User-Profile Lookup Pattern**:
```
PK: "USER#{userId}"
SK: "PROFILE#{profileId}"
```

### Validation & Security

#### Input Validation
- **msgspec**: Strongly typed validation for all profile fields
- **Length Limits**: nickName (32 chars), aboutMe (512 chars)
- **Enum Validation**: All categorical fields validated against predefined enums
- **Image Limits**: Maximum 10 profile images

#### Access Control
- **JWT Authentication**: All endpoints require valid JWT token
- **Profile Ownership**: Users can only modify their own profiles
- **User-Profile Validation**: Ensures profile belongs to authenticated user

#### Data Integrity
- **DynamoDB Transactions**: Atomic operations for create/delete
- **Optimistic Locking**: Prevents concurrent modification conflicts
- **Relationship Consistency**: User-profile relationships maintained automatically

## Error Handling

### Standard Error Response
```json
{
  "error": "Error message",
  "error_code": "ERROR_CODE",
  "details": {
    "field": "Additional error details"
  }
}
```

### Common Error Codes
- `400 Bad Request`: Invalid request data or validation failure
- `401 Unauthorized`: Missing or invalid JWT token
- `403 Forbidden`: User doesn't own the profile
- `404 Not Found`: Profile doesn't exist
- `422 Unprocessable Entity`: Data validation error
- `500 Internal Server Error`: Server error

## Media Integration (Planned)

The profile system is designed to integrate with the media service for image handling:

### Planned Features
- **S3 Presigned URLs**: Direct client-to-S3 upload
- **Automatic Processing**: Thumbnail generation and optimization
- **CDN Delivery**: CloudFront distribution for fast image delivery
- **Image Validation**: Format, size, and content validation
- **Processing Pipeline**: Async image processing with status tracking

### Storage Architecture
```
Profile Images (planned):
PK: "PROFILE#{profileId}"     SK: "MEDIA#{mediaId}"
PK: "UPLOAD#{mediaId}"        SK: "PENDING"
```

## Performance Considerations

- **Single-Item Operations**: O(1) profile retrieval by ID
- **Batch Operations**: Support for querying multiple profiles efficiently
- **Caching**: DynamoDB DAX for sub-millisecond response times
- **Pagination**: Built-in support for large result sets
- **Indexes**: GSI for user-to-profile lookups

## Testing Strategy

### Unit Tests
- Profile validation logic
- CRUD operations
- Error handling
- Security controls

### Integration Tests
- End-to-end API workflows
- DynamoDB operations
- JWT authentication
- Cross-service communication

## Configuration

### Environment Variables
```python
# DynamoDB Configuration
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

# JWT Configuration  
JWT_SECRET_ARN = os.environ.get("JWT_SECRET_ARN")

# Profile Limits
MAX_PROFILE_IMAGES = int(os.environ.get("MAX_PROFILE_IMAGES", "10"))
MAX_NICKNAME_LENGTH = int(os.environ.get("MAX_NICKNAME_LENGTH", "32"))
MAX_ABOUTME_LENGTH = int(os.environ.get("MAX_ABOUTME_LENGTH", "512"))
```

## Monitoring & Observability

### CloudWatch Metrics
- Request volume and latency
- Error rates by endpoint
- DynamoDB performance metrics
- Lambda function duration and memory usage

### Logging
- Structured JSON logging
- Request/response correlation IDs
- User action audit trails
- Error context and stack traces

### Alerts
- High error rate alerts
- Performance degradation alerts
- DynamoDB throttling alerts
- Lambda timeout alerts