#!/usr/bin/env python3
"""
Simple test script for mock user creation functionality (no project dependencies)
"""

import hashlib
import hmac
import json
import random
import time
import urllib.parse

class SimpleTelegramSignatureGenerator:
    """Simplified version for testing"""
    
    @staticmethod
    def create_telegram_init_data(user_data, bot_token):
        """Create valid Telegram WebApp init_data with proper signature"""
        # Create base parameters
        auth_date = int(time.time())
        params = {
            "user": json.dumps(user_data, separators=(",", ":")),
            "chat_instance": str(random.randint(1000000000000000000, 9999999999999999999)),
            "chat_type": "sender",
            "auth_date": str(auth_date)
        }
        
        # Create data check string
        data_params_string = "\n".join(
            f"{k}={v}" for k, v in sorted(params.items())
        )
        
        # Generate secret key
        secret_key = hmac.new(
            "WebAppData".encode(), bot_token.encode(), hashlib.sha256
        ).digest()
        
        # Calculate hash
        calculated_hash = hmac.new(
            secret_key, data_params_string.encode(), hashlib.sha256
        ).hexdigest()
        
        # Add hash to params
        params["hash"] = calculated_hash
        
        # URL encode the params
        init_data_parts = []
        for key, value in params.items():
            encoded_value = urllib.parse.quote(value, safe="")
            init_data_parts.append(f"{key}={encoded_value}")
            
        return "&".join(init_data_parts)


class SimpleMockDataGenerator:
    """Simplified version for testing"""
    
    FIRST_NAMES = ["Alex", "Jordan", "Sam", "Casey", "Riley"]
    LAST_NAMES = ["Anderson", "Brooks", "Carter", "Davis", "Evans"]
    USERNAMES = ["CoolGuy", "NiceVibes", "GoodTimes", "ChillDude", "FunTimes"]
    
    @classmethod
    def generate_telegram_user(cls):
        """Generate random Telegram user data"""
        user_id = random.randint(100000000, 999999999)
        first_name = random.choice(cls.FIRST_NAMES)
        last_name = random.choice(cls.LAST_NAMES)
        username = f"{random.choice(cls.USERNAMES)}{random.randint(1, 999)}"
        
        return {
            "id": user_id,
            "first_name": first_name,
            "last_name": last_name,
            "username": username,
            "language_code": "en",
            "allows_write_to_pm": True,
            "photo_url": f"https://i.pravatar.cc/150?u={user_id}"
        }


def test_telegram_signature():
    """Test Telegram signature generation"""
    print("Testing Telegram signature generation...")
    
    user_data = {
        "id": 123456789,
        "first_name": "Test",
        "last_name": "User", 
        "username": "testuser",
        "language_code": "en"
    }
    bot_token = "test_bot_token"
    
    try:
        init_data = SimpleTelegramSignatureGenerator.create_telegram_init_data(user_data, bot_token)
        
        # Verify structure
        assert "user=" in init_data
        assert "hash=" in init_data
        assert "auth_date=" in init_data
        
        print("✓ Telegram signature generation works")
        return True
        
    except Exception as e:
        print(f"✗ Telegram signature test failed: {e}")
        return False


def test_mock_data():
    """Test mock data generation"""
    print("Testing mock data generation...")
    
    try:
        telegram_user = SimpleMockDataGenerator.generate_telegram_user()
        
        # Check required fields
        required = ["id", "first_name", "last_name", "username", "language_code"]
        for field in required:
            assert field in telegram_user
        
        # Check data types
        assert isinstance(telegram_user["id"], int)
        assert 100000000 <= telegram_user["id"] <= 999999999
        
        print("✓ Mock data generation works")
        return True
        
    except Exception as e:
        print(f"✗ Mock data test failed: {e}")
        return False


def test_signature_validation():
    """Test signature can be validated"""
    print("Testing signature validation...")
    
    try:
        user_data = SimpleMockDataGenerator.generate_telegram_user()
        bot_token = "test_validation_token"
        
        # Generate signature
        init_data = SimpleTelegramSignatureGenerator.create_telegram_init_data(user_data, bot_token)
        
        # Parse and validate
        params = dict(param.split("=", 1) for param in init_data.split("&"))
        hash_value = params.pop("hash")
        
        # Recreate data string
        data_params_string = "\n".join(
            f"{k}={urllib.parse.unquote(v)}" for k, v in sorted(params.items())
        )
        
        # Generate secret key and hash
        secret_key = hmac.new("WebAppData".encode(), bot_token.encode(), hashlib.sha256).digest()
        expected_hash = hmac.new(secret_key, data_params_string.encode(), hashlib.sha256).hexdigest()
        
        assert hash_value == expected_hash, "Hash validation failed"
        
        # Extract and verify user data
        user_json = urllib.parse.unquote(params["user"])
        extracted_user = json.loads(user_json)
        assert extracted_user["id"] == user_data["id"]
        
        print("✓ Signature validation works")
        print(f"  User: {user_data['username']} (ID: {user_data['id']})")
        return True
        
    except Exception as e:
        print(f"✗ Signature validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("Mock User Creation Script - Simple Tests")
    print("=" * 50)
    
    tests = [
        test_telegram_signature,
        test_mock_data,
        test_signature_validation
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__} failed: {e}")
            failed += 1
        print()
    
    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("All tests passed! ✅")
        return 0
    else:
        print("Some tests failed! ❌")
        return 1


if __name__ == "__main__":
    exit(main())