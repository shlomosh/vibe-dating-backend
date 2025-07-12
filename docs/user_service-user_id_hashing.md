# Telegram User ID to Vibe User ID Hashing

This document explains how Telegram user IDs are converted into Vibe user IDs using a deterministic hashing process.

## Overview

The system uses a two-step process to convert Telegram user IDs into Vibe user IDs:
1. Create a platform-specific identifier string
2. Hash the string using UUID v5 and convert to Base64

## Implementation

### Step 1: Platform Identifier Creation

```typescript
const platform = 'tg'; // Platform identifier for Telegram
const platformId = telegramUser.id; // The Telegram user ID
const platformIdString = `${platform}:${String(platformId)}`;
```

This creates a string in the format: `tg:123456789` where:
- `tg` is the platform identifier for Telegram
- `123456789` is the actual Telegram user ID

### Step 2: Hashing Process

The platform identifier string is then hashed using the following process:

```typescript
export const hashStringToId = (str: string, len: number = 8): string => {
  return uuidToBase64(uuidv5(str, '<uuid-namespace-secret>')).slice(0, len);
};
```

#### UUID v5 Generation
- Uses UUID v5 algorithm with a fixed namespace UUID: `<uuid-namespace-secret>`
- Input: The platform identifier string (e.g., `tg:123456789`)
- Output: A deterministic UUID

#### Base64 Conversion
```typescript
export const uuidToBase64 = (uuid: string): string => {
  // Remove hyphens and convert to a byte array
  const hex = uuid.replace(/-/g, '');
  const bytes = new Uint8Array(hex.match(/.{1,2}/g)?.map(byte => parseInt(byte, 16)) || []);

  // Convert to Base64
  const base64 = btoa(String.fromCharCode(...bytes));
  return base64;
}
```

This converts the UUID to Base64 by:
1. Removing hyphens from the UUID
2. Converting hex string to byte array
3. Converting bytes to Base64 using `btoa()`

### Step 3: Final User ID

The final Vibe user ID is created by taking the first 8 characters of the Base64 string:

```typescript
const userId = hashStringToId(platformIdString);
// Result: e.g., "aB3cD4eF"
```

## Example

```typescript
// Input
const telegramUser = { id: 123456789 };

// Process
const platform = 'tg';
const platformId = telegramUser.id;
const platformIdString = `${platform}:${String(platformId)}`; // "tg:123456789"
const userId = hashStringToId(platformIdString); // e.g., "aB3cD4eF"

// Output
console.log(userId); // 8-character Base64 string
```

## Key Properties

1. **Deterministic**: The same Telegram user ID will always produce the same Vibe user ID
2. **Collision Resistant**: Uses UUID v5 with a fixed namespace to minimize collisions
3. **Compact**: Final user ID is only 8 characters long
4. **Platform Agnostic**: The same process can be used for other platforms by changing the platform identifier

## Dependencies

- `uuidv5`: For generating deterministic UUIDs
- Built-in `btoa()`: For Base64 encoding
- Built-in `Uint8Array`: For byte array manipulation

## Security Considerations

- The namespace UUID is hardcoded and should remain consistent across deployments
- The process is deterministic, so the same input will always produce the same output
- The 8-character limit provides 48 bits of entropy (6 bits per character)
- Consider increasing the length parameter if higher collision resistance is needed 