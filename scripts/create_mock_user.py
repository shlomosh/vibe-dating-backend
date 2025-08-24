#!/usr/bin/env python3
"""
Mock User Creation Script for Vibe Dating Backend

This script creates a mock user with:
- Telegram authentication using valid signature
- Profile with randomized data
- Profile pictures from random image services
- All interactions through the backend REST API

Usage:
    python scripts/create_mock_user.py --env dev --api-url https://api.vibe-dating.io
"""

import argparse
import base64
import hashlib
import hmac
import json
import os
import random
import sys
import time
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Add src to path for imports
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from common.aws_lambdas.core_types.profile import (
    BodyType,
    EggplantSizeType,
    HealthPracticesType,
    HivStatusType,
    HostingType,
    PeachShapeType,
    PreventionPracticesType,
    SexualPosition,
    SexualityType,
    TravelDistanceType,
)


class TelegramSignatureGenerator:
    """Generates valid Telegram WebApp signatures for mock users"""

    @staticmethod
    def create_telegram_init_data(user_data: Dict[str, Any], bot_token: str) -> str:
        """
        Create valid Telegram WebApp init_data with proper signature
        
        Args:
            user_data: Telegram user data
            bot_token: Telegram bot token for signature
            
        Returns:
            str: Valid init_data string with hash
        """
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


class MockDataGenerator:
    """Generates realistic mock data for profiles"""
    
    FIRST_NAMES = [
        "Alex", "Jordan", "Sam", "Casey", "Riley", "Morgan", "Blake", "Avery",
        "Quinn", "Sage", "River", "Phoenix", "Skyler", "Cameron", "Devon",
        "Emery", "Finley", "Hayden", "Indigo", "Justice", "Kai", "Lane",
        "Max", "Nova", "Oakley", "Parker", "Reed", "Sage", "Taylor", "Vale"
    ]
    
    LAST_NAMES = [
        "Anderson", "Brooks", "Carter", "Davis", "Evans", "Fisher", "Garcia",
        "Harris", "Johnson", "Kelly", "Lewis", "Martinez", "Miller", "Nelson",
        "Parker", "Roberts", "Smith", "Taylor", "Thompson", "Wilson", "Young",
        "Brown", "Clark", "Hall", "King", "Lee", "Moore", "White", "Wright"
    ]
    
    USERNAMES = [
        "CoolGuy", "NiceVibes", "GoodTimes", "ChillDude", "FunTimes", "EasyGoing",
        "PositiveVibes", "GoodEnergy", "RadVibes", "AwesomeDude", "CoolVibes",
        "NiceGuy", "FriendlyFace", "HappyDude", "GoodMood", "CheerfulGuy"
    ]
    
    BIO_TEMPLATES = [
        "Love exploring new places and meeting interesting people. Always up for an adventure! 🌟",
        "Coffee enthusiast and weekend hiker. Looking for genuine connections. ☕️⛰️",
        "Passionate about music, art, and great conversations. Let's chat! 🎵🎨",
        "Fitness lover and foodie. Balance is key! 💪🍕",
        "Travel addict with a love for local culture. Where should we go next? ✈️🌍",
        "Bookworm by day, Netflix binger by night. Perfect balance! 📚📺",
        "Dog lover and outdoor enthusiast. Life is better with sunshine! 🐕☀️",
        "Creative soul with a technical mind. Best of both worlds! 🎭💻"
    ]
    
    @classmethod
    def generate_telegram_user(cls) -> Dict[str, Any]:
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
    
    @classmethod
    def generate_profile_data(cls) -> Dict[str, Any]:
        """Generate random profile data"""
        first_name = random.choice(cls.FIRST_NAMES)
        age = random.randint(18, 45)
        
        return {
            "nickName": first_name,
            "aboutMe": random.choice(cls.BIO_TEMPLATES),
            "age": str(age),
            "sexualPosition": random.choice(list(SexualPosition)).value,
            "bodyType": random.choice(list(BodyType)).value,
            "sexualityType": random.choice(list(SexualityType)).value,
            "eggplantSize": random.choice(list(EggplantSizeType)).value,
            "peachShape": random.choice(list(PeachShapeType)).value,
            "healthPractices": random.choice(list(HealthPracticesType)).value,
            "hivStatus": random.choice(list(HivStatusType)).value,
            "preventionPractices": random.choice(list(PreventionPracticesType)).value,
            "hosting": random.choice(list(HostingType)).value,
            "travelDistance": random.choice(list(TravelDistanceType)).value,
        }


class ImageService:
    """Handles downloading and processing images for profile pictures"""
    
    IMAGE_SERVICES = [
        "https://picsum.photos/800/600?random={}",
        "https://i.pravatar.cc/800?u={}",
        "https://via.placeholder.com/800x600/4A90E2/FFFFFF?text=Profile+{}",
    ]
    
    @classmethod
    def download_random_image(cls, user_id: int) -> bytes:
        """Download a random image for profile"""
        # Use user_id as seed for consistent but random images
        random.seed(user_id)
        
        # Try multiple services if one fails
        services = cls.IMAGE_SERVICES.copy()
        random.shuffle(services)
        
        for service_template in services:
            service_url = service_template.format(user_id)
            try:
                print(f"    Trying to download from: {service_url}")
                response = requests.get(service_url, timeout=15)
                response.raise_for_status()
                
                # Verify we got actual image content
                content = response.content
                if len(content) > 1024:  # At least 1KB
                    print(f"    Successfully downloaded {len(content)} bytes")
                    return content
                else:
                    print(f"    Downloaded content too small: {len(content)} bytes")
                    continue
                    
            except Exception as e:
                print(f"    Failed to download from {service_url}: {e}")
                continue
        
        # If all services fail, generate a fallback image
        print("    All image services failed, generating fallback image")
        return cls._generate_fallback_image(user_id)
    
    @classmethod
    def _generate_fallback_image(cls, user_id: int) -> bytes:
        """Generate a simple fallback image"""
        try:
            # Try to generate a simple colored image using placeholder service
            colors = ["FF6B6B", "4ECDC4", "45B7D1", "96CEB4", "FECA57", "FF9FF3", "54A0FF"]
            random.seed(user_id)
            color = random.choice(colors)
            fallback_url = f"https://via.placeholder.com/800x600/{color}/FFFFFF?text=User+{user_id}"
            
            response = requests.get(fallback_url, timeout=10)
            response.raise_for_status()
            return response.content
            
        except Exception as e:
            print(f"    Even fallback image generation failed: {e}")
            # Return minimal PNG header - this should fail gracefully in the backend
            return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x03 \x00\x00\x02X\x08\x02\x00\x00\x00\xd5\x94\x8e\xcf\x00\x00\x00\x19tEXtSoftware\x00Adobe ImageReadyq\xc9e<\x00\x00\x00\x0eIDATx\xdac\xf8\x0f\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
    
    @classmethod
    def create_media_metadata(cls, image_data: bytes) -> Dict[str, Any]:
        """Create metadata for uploaded image"""
        return {
            "size": len(image_data),
            "format": "jpeg",
            "width": 800,
            "height": 600
        }


class VibeAPIClient:
    """Client for interacting with the Vibe Dating Backend API"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.jwt_token: Optional[str] = None
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def authenticate_user(self, telegram_user: Dict[str, Any], bot_token: str) -> Dict[str, Any]:
        """Authenticate user with Telegram data"""
        # Generate valid Telegram signature
        init_data = TelegramSignatureGenerator.create_telegram_init_data(
            telegram_user, bot_token
        )
        
        auth_payload = {
            "platform": "telegram",
            "platformToken": init_data,
            "platformMetadata": telegram_user
        }
        
        response = self.session.post(
            f"{self.base_url}/auth/platform",
            json=auth_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"Authentication failed: {response.status_code} - {response.text}")
        
        auth_data = response.json()
        self.jwt_token = auth_data["token"]
        
        return auth_data
    
    def create_profile(self, profile_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new profile"""
        if not self.jwt_token:
            raise Exception("Not authenticated. Call authenticate_user first.")
        
        headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json"
        }
        
        payload = {"profile": profile_data}
        
        response = self.session.put(
            f"{self.base_url}/profile/{profile_id}",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"Profile creation failed: {response.status_code} - {response.text}")
        
        return response.json()
    
    def upload_profile_image(self, profile_id: str, image_data: bytes) -> Dict[str, Any]:
        """Upload profile image"""
        if not self.jwt_token:
            raise Exception("Not authenticated. Call authenticate_user first.")
        
        headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json"
        }
        
        # Create metadata
        metadata = ImageService.create_media_metadata(image_data)
        media_blob = base64.b64encode(json.dumps(metadata).encode()).decode()
        
        # Step 1: Request upload URL
        upload_request = {
            "mediaType": "image/jpeg",
            "mediaBlob": media_blob,
            "mediaSize": len(image_data)
        }
        
        print(f"  Requesting upload URL for profile {profile_id}...")
        response = self.session.post(
            f"{self.base_url}/profile/{profile_id}/media",
            json=upload_request,
            headers=headers,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"  Upload URL request details: {upload_request}")
            print(f"  Response headers: {dict(response.headers)}")
            raise Exception(f"Upload URL request failed: {response.status_code} - {response.text}")
        
        upload_data = response.json()
        media_id = upload_data["mediaId"]
        print(f"  Got media ID: {media_id}")
        
        # Step 2: Upload to S3 using presigned URL
        print(f"  Uploading {len(image_data)} bytes to S3...")
        upload_response = self.session.post(
            upload_data["uploadUrl"],
            data=upload_data["uploadHeaders"],
            files={"file": ("image.jpg", image_data, "image/jpeg")},
            timeout=60
        )
        
        if upload_response.status_code not in [200, 204]:
            print(f"  S3 upload response: {upload_response.status_code} - {upload_response.text}")
            raise Exception(f"S3 upload failed: {upload_response.status_code}")
        
        # Step 3: Complete upload
        completion_data = {
            "uploadSuccess": True,
            "s3ETag": upload_response.headers.get("ETag", "").strip('"'),
            "actualSize": len(image_data)
        }
        
        print(f"  Completing upload...")
        completion_response = self.session.post(
            f"{self.base_url}/profile/{profile_id}/media/{media_id}",
            json=completion_data,
            headers=headers,
            timeout=30
        )
        
        if completion_response.status_code != 200:
            print(f"  Completion response: {completion_response.status_code} - {completion_response.text}")
            raise Exception(f"Upload completion failed: {completion_response.status_code}")
        
        print(f"  Upload completed successfully!")
        return completion_response.json()


class MockUserCreator:
    """Main class for creating mock users"""
    
    def __init__(self, api_url: str, bot_token: str, num_images: int = 3):
        self.api_client = VibeAPIClient(api_url)
        self.bot_token = bot_token
        self.num_images = num_images
    
    def create_mock_user(self) -> Dict[str, Any]:
        """Create a complete mock user with profile and images"""
        print("Creating mock user...")
        
        # Step 1: Generate Telegram user data
        telegram_user = MockDataGenerator.generate_telegram_user()
        print(f"Generated Telegram user: {telegram_user['username']}")
        
        # Step 2: Authenticate with backend
        print("Authenticating with backend...")
        auth_data = self.api_client.authenticate_user(telegram_user, self.bot_token)
        user_id = auth_data["userId"]
        profile_ids = auth_data["profileIds"]
        
        if not profile_ids:
            raise Exception("No profile IDs allocated for user")
        
        profile_id = profile_ids[0]  # Use first allocated profile ID
        print(f"Authenticated user: {user_id}, using profile: {profile_id}")
        
        # Step 3: Create profile
        print("Creating profile...")
        profile_data = MockDataGenerator.generate_profile_data()
        profile_response = self.api_client.create_profile(profile_id, profile_data)
        print(f"Created profile: {profile_data['nickName']}")
        
        # Brief delay for DynamoDB consistency
        import time
        time.sleep(2)
        
        # Step 3.5: Test profile access first
        print("Testing profile access...")
        try:
            test_response = self.api_client.session.get(
                f"{self.api_client.base_url}/profile/{profile_id}",
                headers={
                    "Authorization": f"Bearer {self.api_client.jwt_token}",
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            if test_response.status_code == 200:
                print("✓ Profile access confirmed")
            else:
                print(f"⚠ Profile access issue: {test_response.status_code} - {test_response.text}")
                print("  This may cause media upload failures")
        except Exception as e:
            print(f"⚠ Profile access test failed: {e}")

        # Step 4: Upload profile images
        uploaded_images = []
        for i in range(self.num_images):
            try:
                print(f"Uploading image {i+1}/{self.num_images}...")
                image_data = ImageService.download_random_image(
                    telegram_user["id"] + i
                )
                
                if image_data:  # Only upload if we have image data
                    upload_response = self.api_client.upload_profile_image(
                        profile_id, image_data
                    )
                    uploaded_images.append(upload_response)
                    print(f"Uploaded image {i+1}: {upload_response['mediaId']}")
                else:
                    print(f"Skipping image {i+1} (no data)")
                    
            except Exception as e:
                print(f"Failed to upload image {i+1}: {e}")
                continue
        
        return {
            "telegram_user": telegram_user,
            "auth_data": auth_data,
            "profile_data": profile_data,
            "profile_response": profile_response,
            "uploaded_images": uploaded_images,
            "user_id": user_id,
            "profile_id": profile_id
        }


def get_bot_token_from_aws(environment: str) -> str:
    """Get bot token from AWS Secrets Manager"""
    import boto3
    from botocore.exceptions import ClientError
    
    try:
        session = boto3.Session(profile_name=f"vibe-{environment}")
        secrets_client = session.client("secretsmanager")
        
        secret_name = f"vibe-dating/telegram-bot-token/{environment}"
        response = secrets_client.get_secret_value(SecretId=secret_name)
        return response["SecretString"]
        
    except ClientError as e:
        raise Exception(f"Failed to get bot token from AWS: {e}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Create mock user for Vibe Dating")
    parser.add_argument("--env", default="dev", help="Environment (dev, staging, prod)")
    parser.add_argument("--api-url", help="API base URL (optional, will use config)")
    parser.add_argument("--bot-token", help="Telegram bot token (optional, will use AWS)")
    parser.add_argument("--num-images", type=int, default=3, help="Number of profile images")
    parser.add_argument("--output", help="Output file for created user data")
    
    args = parser.parse_args()
    
    try:
        # Determine API URL
        if args.api_url:
            api_url = args.api_url
        else:
            # Load from config
            config_file = project_root / "src" / "config" / "parameters.yaml"
            if config_file.exists():
                import yaml
                with open(config_file) as f:
                    config = yaml.safe_load(f)
                api_domain = config.get("ApiDomainName", "api.vibe-dating.io")
                api_url = f"https://{api_domain}"
            else:
                api_url = f"https://api-{args.env}.vibe-dating.io"
        
        print(f"Using API URL: {api_url}")
        
        # Get bot token
        if args.bot_token:
            bot_token = args.bot_token
        else:
            print("Getting bot token from AWS Secrets Manager...")
            bot_token = get_bot_token_from_aws(args.env)
        
        # Create mock user
        creator = MockUserCreator(api_url, bot_token, args.num_images)
        result = creator.create_mock_user()
        
        # Output results
        print("\n" + "="*50)
        print("MOCK USER CREATED SUCCESSFULLY!")
        print("="*50)
        print(f"User ID: {result['user_id']}")
        print(f"Profile ID: {result['profile_id']}")
        print(f"Username: @{result['telegram_user']['username']}")
        print(f"Profile Name: {result['profile_data']['nickName']}")
        print(f"Images Uploaded: {len(result['uploaded_images'])}")
        
        # Save to file if requested
        if args.output:
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2, default=str)
            print(f"Full data saved to: {args.output}")
        
        return 0
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())