#!/usr/bin/env python3
"""
Debug JWT token to understand the 403 authorization issue
"""

import base64
import json

# Token from the last successful authentication (from user.json)
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOiJZQ1FNNUktciIsImlhdCI6MTc1NjA1NjA4NywiZXhwIjoxNzU2NjYwODg3LCJpc3MiOiJ2aWJlLWFwcCJ9.EfpXMjC3bOPoXNVsc8zs83pdz1FygL-p5dskyoTf-lM"

# Decode without verification to see the payload
try:
    # Split token parts
    header, payload, signature = token.split('.')
    
    # Add padding if needed
    payload += '=' * (4 - len(payload) % 4)
    
    # Decode payload
    decoded_payload = json.loads(base64.urlsafe_b64decode(payload))
    
    print("JWT Token Payload:")
    print(json.dumps(decoded_payload, indent=2))
    
    # Check if token is expired
    import time
    current_time = int(time.time())
    exp_time = decoded_payload.get('exp', 0)
    
    print(f"\nCurrent time: {current_time}")
    print(f"Token expires: {exp_time}")
    print(f"Token valid: {current_time < exp_time}")
    print(f"Time until expiry: {exp_time - current_time} seconds")
    
except Exception as e:
    print(f"Error decoding token: {e}")