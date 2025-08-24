#!/usr/bin/env python3
"""
Test profile access to debug media upload authorization
"""

import json
import requests

# Data from the last successful authentication
api_url = "https://api.vibe-dating.io"
jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOiJZQ1FNNUktciIsImlhdCI6MTc1NjA1NjA4NywiZXhwIjoxNzU2NjYwODg3LCJpc3MiOiJ2aWJlLWFwcCJ9.EfpXMjC3bOPoXNVsc8zs83pdz1FygL-p5dskyoTf-lM"
user_id = "YCQM5I-r"
profile_id = "4PSYTrD3"

headers = {
    "Authorization": f"Bearer {jwt_token}",
    "Content-Type": "application/json"
}

print(f"Testing access for user {user_id} to profile {profile_id}")
print("=" * 60)

# Test 1: Try to get the profile
print("1. Testing profile access...")
try:
    response = requests.get(f"{api_url}/profile/{profile_id}", headers=headers, timeout=30)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        profile_data = response.json()
        print("   ✓ Profile access successful")
        print(f"   Profile owner check: {profile_data.get('profile', {}).get('userId', 'N/A')}")
    else:
        print(f"   ✗ Profile access failed: {response.text}")
except Exception as e:
    print(f"   ✗ Profile access error: {e}")

print()

# Test 2: Try a simple media request
print("2. Testing media endpoint access...")
try:
    # Try to get media for this profile (this should fail gracefully if no media exists)
    response = requests.options(f"{api_url}/profile/{profile_id}/media", headers=headers, timeout=30)
    print(f"   OPTIONS Status: {response.status_code}")
    print(f"   Headers: {dict(response.headers)}")
except Exception as e:
    print(f"   ✗ Media OPTIONS error: {e}")

print()

# Test 3: Check what profiles this user actually owns
print("3. Checking auth data for allocated profiles...")
print(f"   User ID from JWT: {user_id}")
print(f"   Profile ID being used: {profile_id}")

# From user.json, the allocated profile IDs were:
allocated_profiles = [
    "4PSYTrD3",
    "4W3-O_QU", 
    "sMEKmbj0",
    "cWk1mVXM",
    "24-vBWEs"
]

print(f"   Allocated profiles: {allocated_profiles}")
print(f"   Profile ownership: {profile_id in allocated_profiles}")

print()
print("Summary:")
print(f"- User ID: {user_id}")  
print(f"- Profile ID: {profile_id}")
print(f"- Profile in allocated list: {profile_id in allocated_profiles}")
print()
print("If profile access works but media doesn't, it's likely a backend authorization issue.")