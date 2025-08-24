#!/usr/bin/env python3
"""
Example usage of the mock user creation script

This demonstrates how to use the script programmatically.
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.create_mock_user import MockUserCreator, MockDataGenerator


def example_create_multiple_users():
    """Example: Create multiple mock users"""
    print("Example: Creating multiple mock users")
    print("=" * 50)
    
    # Configuration
    api_url = "https://api-dev.vibe-dating.io"
    bot_token = "your_bot_token_here"  # Replace with actual token
    num_users = 3
    
    try:
        creator = MockUserCreator(api_url, bot_token, num_images=2)
        
        users = []
        for i in range(num_users):
            print(f"\nCreating user {i+1}/{num_users}...")
            
            # This would make actual API calls - commented out for safety
            # user_result = creator.create_mock_user()
            # users.append(user_result)
            
            # Instead, just demonstrate data generation
            telegram_user = MockDataGenerator.generate_telegram_user()
            profile_data = MockDataGenerator.generate_profile_data()
            
            print(f"Generated: @{telegram_user['username']}")
            print(f"Profile: {profile_data['nickName']}, {profile_data['age']} years old")
            
        print(f"\nWould create {num_users} users successfully!")
        
    except Exception as e:
        print(f"Error: {e}")


def example_custom_user_data():
    """Example: Create user with custom data"""
    print("\nExample: Custom user data")
    print("=" * 30)
    
    # Generate data
    telegram_user = MockDataGenerator.generate_telegram_user()
    profile_data = MockDataGenerator.generate_profile_data()
    
    # Customize the data
    telegram_user["first_name"] = "Custom"
    telegram_user["last_name"] = "User"
    profile_data["nickName"] = "CustomNick"
    profile_data["aboutMe"] = "This is a custom bio for testing!"
    
    print(f"Custom user: {telegram_user['first_name']} {telegram_user['last_name']}")
    print(f"Username: @{telegram_user['username']}")
    print(f"Profile: {profile_data['nickName']}")
    print(f"Bio: {profile_data['aboutMe']}")


def example_signature_generation():
    """Example: Generate Telegram signatures"""
    print("\nExample: Telegram signature generation")
    print("=" * 40)
    
    from scripts.create_mock_user import TelegramSignatureGenerator
    
    # Sample data
    user_data = {
        "id": 123456789,
        "first_name": "Example",
        "last_name": "User",
        "username": "exampleuser",
        "language_code": "en"
    }
    
    bot_token = "example_bot_token"
    
    # Generate signature
    init_data = TelegramSignatureGenerator.create_telegram_init_data(
        user_data, bot_token
    )
    
    print(f"Generated init_data: {init_data[:100]}...")
    print("This would be used for authentication with your backend")


def main():
    """Run all examples"""
    print("Mock User Creation Script - Usage Examples")
    print("=" * 60)
    
    example_create_multiple_users()
    example_custom_user_data() 
    example_signature_generation()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("\nTo use the actual script:")
    print("  python scripts/create_mock_user.py --env dev")
    print("  poetry run create-mock-user --env dev --num-images 5")


if __name__ == "__main__":
    main()