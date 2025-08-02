# Vibe Dating App - System Architecture

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
- **Subject Rooms**: Themed discussion rooms for community interaction
- **User Blocking**: Users can block other users from contacting them
- **User Banning**: Community moderation with temporary/permanent bans

### 4. Media Management
- **Frontend Processing**: User uploads image and sets zoom/cropping to 3:4 ratio; frontend crops original image and extracts EXIF metadata (selective fields); EXIF removed from cropped image
- **Upload Flow**: Frontend requests backend to upload image with EXIF metadata -> Backend allocates image-id and provides upload path -> Image uploaded to S3 -> CloudFront
- **Backend Processing**: Thumbnail generation, video transcoding, metadata extraction/storage
- **Delivery**: CloudFront CDN URLs for originals, thumbnails, and video previews
- **Cleanup**: TTL-based removal of orphaned media

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

### Platform Compliance
- Telegram Mini-App guidelines
- App store requirements (if applicable)
- Regional privacy laws (GDPR, CCPA)
- Content moderation policies
- User safety regulations
- Media content guidelines