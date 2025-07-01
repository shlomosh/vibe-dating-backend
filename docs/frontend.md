# Vibe Dating - Telegram Mini App AI Context

## Project Overview

**Vibe Dating** is a Telegram mini-app frontend application built for dating purposes, specifically targeting the LGBTQ+ community. The app is designed as a single-page application that runs within Telegram's ecosystem, providing a modern dating experience with features like profile management, location-based matching, chat functionality, and TON blockchain integration.

## Technology Stack

### Core Technologies
- **React 18.2.0** - Main UI framework
- **TypeScript 5.8.2** - Type-safe JavaScript
- **Vite 6.2.4** - Build tool and dev server
- **Tailwind CSS 4.1.7** - Utility-first CSS framework
- **React Router DOM 6.23.0** - Client-side routing

### Telegram Integration
- **@telegram-apps/sdk 3.10.0** - Telegram Mini Apps SDK
- **@telegram-apps/sdk-react 3.1.7** - React hooks for Telegram SDK
- **@telegram-apps/telegram-ui 2.1.8** - Telegram UI components

### UI Components & Styling
- **Radix UI** - Headless UI components (Dialog, Popover, Select, etc.)
- **Lucide React** - Icon library
- **Shadcn/ui** - Component library (custom components in `src/components/ui/`)
- **Tailwind CSS** with RTL support and direction utilities

### Blockchain Integration
- **@tonconnect/ui-react 2.1.0** - TON Connect integration for blockchain features

### Additional Libraries
- **Mapbox GL 3.12.0** - Location and mapping functionality
- **Swiper 11.2.7** - Touch slider component
- **React Dropzone** - File upload functionality
- **React Easy Crop** - Image cropping
- **UUID** - Unique identifier generation
- **Seedrandom** - Deterministic random number generation

## Project Structure

```
vibe-frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── ui/             # Shadcn/ui components
│   │   ├── App.tsx         # Main app component
│   │   ├── Background.tsx  # Background component
│   │   ├── Content.tsx     # Content wrapper
│   │   └── ...
│   ├── contexts/           # React context providers
│   │   ├── ProfileContext.tsx
│   │   ├── LocationContext.tsx
│   │   ├── UserContext.tsx
│   │   ├── ThemeContext.tsx
│   │   └── LanguageContext.tsx
│   ├── pages/              # Route components
│   │   ├── SplashPage.tsx
│   │   ├── ProfileSetupPage.tsx
│   │   ├── RadarPage.tsx
│   │   ├── InboxPage.tsx
│   │   ├── ChatPage.tsx
│   │   └── ...
│   ├── navigation/         # Routing configuration
│   │   ├── routes.tsx
│   │   └── *NavigationBar.tsx
│   ├── types/              # TypeScript type definitions
│   │   ├── profile.ts
│   │   ├── chat.ts
│   │   └── location.ts
│   ├── utils/              # Utility functions
│   │   ├── local-storage.ts
│   │   ├── cloud-storage.ts
│   │   ├── generator.ts
│   │   └── location.ts
│   ├── locale/             # Internationalization
│   │   ├── en-US.tsx
│   │   └── he-IL.tsx
│   ├── mock/               # Mock data for development
│   └── config.tsx          # App configuration
```

## Key Features & Functionality

### 1. Profile Management
- **Profile Types**: Comprehensive profile system with detailed user information
- **Profile Categories**:
  - Position types (bottom, vers, top, etc.)
  - Body types (petite, slim, average, fit, etc.)
  - Sexuality types (gay, bisexual, curious, trans, fluid)
  - Health practices and HIV status
  - Hosting preferences and travel distance
  - Physical attributes (eggplant size, peach shape)

### 2. Location-Based Features
- **Mapbox Integration**: Location services and mapping
- **Distance Calculation**: Proximity-based matching
- **Travel Preferences**: User-defined travel distance preferences

### 3. Chat & Messaging
- **Conversation Management**: Chat history and message tracking
- **Unread Counts**: Message notification system
- **Profile Integration**: Chat linked to user profiles

### 4. Radar/Matching System
- **Discovery Interface**: Location-based profile discovery
- **Filtering System**: Advanced filtering options for matches
- **Profile Cards**: Swipeable profile interface

### 5. Multi-language Support
- **Internationalization**: English and Hebrew support
- **RTL Support**: Right-to-left text direction for Hebrew

### 6. Theme System
- **Dark/Light Mode**: Automatic theme detection from Telegram
- **Theme Persistence**: User preference storage
- **Telegram Integration**: Seamless theme synchronization

### 7. Blockchain Integration
- **TON Connect**: TON blockchain wallet integration
- **Web3 Features**: Cryptocurrency and blockchain functionality

## Data Models

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

## State Management

The app uses React Context for state management with the following providers:

1. **ProfileProvider**: Manages user profiles and profile database
2. **LocationProvider**: Handles location data and preferences
3. **UserProvider**: Manages user authentication and data
4. **ThemeProvider**: Handles theme switching and persistence
5. **LanguageProvider**: Manages internationalization
6. **FiltersDrawerContext**: Manages filter UI state

## Storage Strategy

- **Local Storage**: Primary storage for user data and preferences
- **Cloud Storage**: Alternative storage option (commented out)
- **Storage Keys**: Namespaced keys for data organization
  - `vibe/config/v1/profiles`
  - `vibe/config/v1/location`
  - `vibe/config/v1/radar-filters`

## Development & Deployment

### Development Commands
- `npm run dev` - Development server
- `npm run dev:https` - HTTPS development server
- `npm run build` - Production build
- `npm run lint` - Code linting
- `npm run deploy` - Deploy to GitHub Pages

### Build Configuration
- **Base Path**: `/vibe-dating/` for GitHub Pages deployment
- **Target**: ESNext for modern browser support
- **Asset Optimization**: Hashed filenames for caching
- **SSL Support**: Self-signed certificates for local HTTPS

### Deployment
- **GitHub Pages**: Primary deployment platform
- **CDN**: Fast content delivery via GitHub Pages CDN
- **Automatic Deployment**: GitHub Actions workflow for master branch

## Security & Privacy Considerations

1. **Telegram Integration**: Leverages Telegram's security model
2. **Local Storage**: Sensitive data stored locally
3. **HTTPS Required**: Secure communication for production
4. **User Privacy**: Profile data management with user consent

## Performance Optimizations

1. **Code Splitting**: Route-based code splitting with React Router
2. **Asset Optimization**: Vite build optimization
3. **Lazy Loading**: Component lazy loading for better performance
4. **Image Optimization**: Efficient image handling and cropping
5. **Caching Strategy**: Asset hashing for optimal caching

## Browser Support

- **Modern Browsers**: ES2020+ support
- **Mobile Optimization**: Responsive design for mobile devices
- **Telegram Integration**: Optimized for Telegram Web App environment

## Future Considerations

1. **Real-time Features**: WebSocket integration for live chat
2. **Push Notifications**: Telegram notification integration
3. **Advanced Matching**: AI-powered matching algorithms
4. **Video Chat**: WebRTC integration for video calls
5. **Payment Integration**: TON blockchain payments

## Development Guidelines

1. **TypeScript First**: All new code should be TypeScript
2. **Component Architecture**: Use functional components with hooks
3. **Context Usage**: Prefer context over prop drilling
4. **Responsive Design**: Mobile-first approach with Tailwind
5. **Accessibility**: Follow WCAG guidelines
6. **Performance**: Monitor bundle size and loading times
7. **Testing**: Unit tests for critical components (to be implemented)

This context file provides a comprehensive overview of the Vibe Dating Telegram mini-app project, enabling AI assistants to understand the codebase structure, architecture decisions, and development patterns used throughout the application.
