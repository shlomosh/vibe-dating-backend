# Data Model & Database Schema

## ID System
- All application IDs are **16-character base64 strings**
- User ID: Generated from hash of Telegram user ID (1:1 mapping)
- Profile ID: Unique per profile (max 3 per user)
- Media ID: Unique per media item (max 5 per profile, supporting images and short videos)
- Room ID: Unique per subject-based room
- Message ID: Unique per room message
- Block ID: Unique per user block relationship

## Entity Relationships
```
User (1) -> Profiles (1-3) -> Media (0-5) [images/short-videos]
User (1) -> Agora Chat ID (1)
User (1) -> Blocked Users (many)
User (1) -> Banned Users (many)
Profile (1) -> Location History (many)
Profile (1) -> Room Messages (many)
Room (1) -> Messages (many) -> Media Attachments (0-many)
```

## DynamoDB Schema

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

## Global Secondary Indexes (GSIs)

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

## Frontend Data Models

### Profile System
```typescript
interface ProfileInfo {
  nickName: string;
  aboutMe: string;
  age: AgeType;
  position: PositionType;
  body: BodyType;
  eggplantSize: EggplantSizeType;
  peachShape: PeachShapeType;
  healthPractices: HealthPracticesType;
  hivStatus: HivStatusType;
  preventionPractices: PreventionPracticesType;
  hosting: HostingType;
  travelDistance: TravelDistanceType;
}

interface ProfileDB {
  id: ProfileId;
  db: Record<ProfileId, MyProfileInfo>;
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