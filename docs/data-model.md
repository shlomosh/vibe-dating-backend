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

**9. Profile Media Record (for media processing pipeline)**
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
  nickName?: string;        // max 32 chars
  aboutMe?: string;         // max 512 chars
  age?: string;             // max 8 chars
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
  allocatedMediaIds: string[];  // max 5 media IDs
  activeMediaIds: string[];     // currently active media
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