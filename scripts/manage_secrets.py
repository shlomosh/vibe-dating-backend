#!/usr/bin/env python3
"""
AWS Secrets Manager Management Script for Vibe Dating App

This script provides a command-line interface for managing secrets in AWS Secrets Manager
for the Vibe Dating App backend services.
"""

import os
import sys
import argparse
import boto3
import base64
import secrets
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List
from botocore.exceptions import ClientError, NoCredentialsError

# Set AWS profile
os.environ["AWS_PROFILE"] = "vibe-dating"
os.environ["AWS_REGION"] = "il-central-1"

class SecretsManager:
    """Manages AWS Secrets Manager for Vibe Dating App"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.region = os.getenv("AWS_REGION", "il-central-1")
        self.environment = os.getenv("ENVIRONMENT", "dev")
        self.secrets_client = boto3.client('secretsmanager', region_name=self.region)
        
        # Secret names
        self.secret_names = {
            "telegram_bot_token": f"vibe-dating/telegram-bot-token/{self.environment}",
            "jwt_secret": f"vibe-dating/jwt-secret/{self.environment}",
            "uuid_namespace": f"vibe-dating/uuid-namespace/{self.environment}"
        }
        
    def check_prerequisites(self):
        """Check that all prerequisites are met"""
        print("• Checking prerequisites...")
        
        # Check if AWS CLI is installed
        try:
            import boto3
            print("• boto3 is available")
        except ImportError:
            print("❌ boto3 is not installed. Please install it first.")
            sys.exit(1)
            
        # Check AWS credentials
        try:
            self.secrets_client.list_secrets(MaxResults=1)
            print("• AWS credentials are configured")
        except NoCredentialsError:
            print("❌ AWS credentials not configured. Please run 'aws configure' first.")
            sys.exit(1)
        except Exception as e:
            print(f"❌ AWS credentials error: {e}")
            sys.exit(1)
            
        print("✅ All prerequisites met")
        
    def generate_secure_secret(self, length: int = 32) -> str:
        """Generate a secure random secret"""
        return secrets.token_urlsafe(length)
        
    def create_secret(self, secret_name: str, secret_value: str, description: str = "") -> bool:
        """Create a new secret in AWS Secrets Manager"""
        try:
            response = self.secrets_client.create_secret(
                Name=secret_name,
                SecretString=secret_value,
                Description=description,
                Tags=[
                    {'Key': 'Environment', 'Value': self.environment},
                    {'Key': 'Service', 'Value': 'vibe-dating'},
                    {'Key': 'ManagedBy', 'Value': 'secrets-manager-script'}
                ]
            )
            print(f"• Created secret: {secret_name}")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceExistsException':
                print(f"⚠️  Secret already exists: {secret_name}")
                return False
            else:
                print(f"❌ Failed to create secret {secret_name}: {e}")
                return False
                
    def update_secret(self, secret_name: str, secret_value: str) -> bool:
        """Update an existing secret"""
        try:
            response = self.secrets_client.update_secret(
                SecretId=secret_name,
                SecretString=secret_value
            )
            print(f"• Updated secret: {secret_name}")
            return True
        except ClientError as e:
            print(f"❌ Failed to update secret {secret_name}: {e}")
            return False
            
    def get_secret(self, secret_name: str) -> Optional[str]:
        """Retrieve a secret value"""
        try:
            response = self.secrets_client.get_secret_value(SecretId=secret_name)
            if 'SecretString' in response:
                return response['SecretString']
            else:
                # Handle binary secrets
                return base64.b64decode(response['SecretBinary']).decode('utf-8')
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print(f"⚠️  Secret not found: {secret_name}")
                return None
            else:
                print(f"❌ Failed to retrieve secret {secret_name}: {e}")
                return None
                
    def delete_secret(self, secret_name: str, force: bool = False) -> bool:
        """Delete a secret"""
        try:
            if force:
                # Force delete immediately
                response = self.secrets_client.delete_secret(
                    SecretId=secret_name,
                    ForceDeleteWithoutRecovery=True
                )
            else:
                # Schedule for deletion (7 days recovery window)
                response = self.secrets_client.delete_secret(SecretId=secret_name)
            print(f"• Deleted secret: {secret_name}")
            return True
        except ClientError as e:
            print(f"❌ Failed to delete secret {secret_name}: {e}")
            return False
            
    def list_secrets(self, filter_prefix: str = "vibe-dating/") -> List[Dict[str, Any]]:
        """List all secrets with a specific prefix"""
        try:
            secrets_list = []
            paginator = self.secrets_client.get_paginator('list_secrets')
            
            for page in paginator.paginate():
                for secret in page['SecretList']:
                    if secret['Name'].startswith(filter_prefix):
                        secrets_list.append({
                            'name': secret['Name'],
                            'description': secret.get('Description', ''),
                            'created': secret['CreatedDate'],
                            'last_modified': secret.get('LastModifiedDate', ''),
                            'tags': {tag['Key']: tag['Value'] for tag in secret.get('Tags', [])}
                        })
            return secrets_list
        except ClientError as e:
            print(f"❌ Failed to list secrets: {e}")
            return []
            
    def setup_core_secrets(self, interactive: bool = True) -> Dict[str, bool]:
        """Setup core secrets for the application"""
        print("🔧 Setting up core secrets...")
        
        results = {}
        
        # Core secrets that are required
        core_secrets = {
            "telegram_bot_token": {
                "description": "Telegram Bot Token for WebApp authentication",
                "required": True,
                "generate": False
            },
            "jwt_secret": {
                "description": "Secret key for JWT token signing",
                "required": True,
                "generate": True
            },
            "uuid_namespace": {
                "description": "UUID namespace for generating consistent UUIDs",
                "required": True,
                "generate": True
            }
        }
        
        for secret_key, config in core_secrets.items():
            secret_name = self.secret_names[secret_key]
            
            # Check if secret already exists
            existing_value = self.get_secret(secret_name)
            if existing_value:
                print(f"⚠️  Secret already exists: {secret_name}")
                if interactive:
                    update = input("Do you want to update it? (y/N): ").lower().strip()
                    if update != 'y':
                        results[secret_key] = True
                        continue
                else:
                    results[secret_key] = True
                    continue
            
            # Get or generate secret value
            if config["generate"]:
                if secret_key == "uuid_namespace":
                    secret_value = str(uuid.uuid4())
                    print(f"• Generated UUID namespace: {secret_value}")
                else:
                    secret_value = self.generate_secure_secret(64)
                    print(f"• Generated secure {secret_key}: {secret_value[:20]}...")
            else:
                if interactive:
                    secret_value = input(f"Enter {secret_key}: ").strip()
                    if not secret_value:
                        if config["required"]:
                            print(f"❌ {secret_key} is required")
                            results[secret_key] = False
                            continue
                        else:
                            print(f"•  Skipping {secret_key}")
                            results[secret_key] = True
                            continue
                else:
                    print(f"❌ {secret_key} requires manual input in interactive mode")
                    results[secret_key] = False
                    continue
            
            # Create or update secret
            if existing_value:
                success = self.update_secret(secret_name, secret_value)
            else:
                success = self.create_secret(secret_name, secret_value, config["description"])
            
            results[secret_key] = success
            
        return results
        
    def export_secrets_to_env(self, output_file: str = None) -> bool:
        """Export secrets to environment variables or file"""
        print("• Exporting secrets...")
        
        env_vars = {}
        
        for secret_key, secret_name in self.secret_names.items():
            secret_value = self.get_secret(secret_name)
            if secret_value:
                # Convert to environment variable format
                env_key = secret_key.upper().replace('-', '_')
                env_vars[env_key] = secret_value
        
        if output_file:
            # Write to file
            try:
                with open(output_file, 'w') as f:
                    for key, value in env_vars.items():
                        f.write(f"{key}={value}\n")
                print(f"• Exported secrets to {output_file}")
                return True
            except Exception as e:
                print(f"❌ Failed to write to {output_file}: {e}")
                return False
        else:
            # Print to console
            print("Environment variables:")
            for key, value in env_vars.items():
                print(f"export {key}='{value}'")
            return True
            
    def validate_secrets(self) -> Dict[str, bool]:
        """Validate that all required secrets exist and are accessible"""
        print("• Validating secrets...")
        
        results = {}
        
        for secret_key, secret_name in self.secret_names.items():
            secret_value = self.get_secret(secret_name)
            if secret_value:
                print(f"• {secret_key}: Found")
                results[secret_key] = True
            else:
                print(f"❌ {secret_key}: Missing")
                results[secret_key] = False
                
        return results
        
    def rotate_secret(self, secret_name: str) -> bool:
        """Rotate a secret by generating a new value"""
        print(f"• Rotating secret: {secret_name}")
        
        # Generate new secret value
        new_value = self.generate_secure_secret(64)
        
        # Update the secret
        success = self.update_secret(secret_name, new_value)
        
        if success:
            print(f"• Successfully rotated {secret_name}")
            print(f"New value: {new_value[:20]}...")
        else:
            print(f"❌ Failed to rotate {secret_name}")
            
        return success


def main():
    """Main function for command-line interface"""
    parser = argparse.ArgumentParser(
        description="Manage AWS Secrets Manager for Vibe Dating App",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Setup core secrets interactively
  python scripts/manage_secrets.py setup

  # Setup core secrets
  python scripts/manage_secrets.py setup

  # List all secrets
  python scripts/manage_secrets.py list

  # Export secrets to environment file
  python scripts/manage_secrets.py export --output .env

  # Validate all secrets
  python scripts/manage_secrets.py validate

  # Rotate JWT secret
  python scripts/manage_secrets.py rotate --secret jwt_secret

  # Delete a secret
  python scripts/manage_secrets.py delete --secret telegram_bot_token
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Setup secrets')
    setup_parser.add_argument('--non-interactive', action='store_true', help='Non-interactive mode')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all secrets')
    list_parser.add_argument('--filter', default='vibe-dating/', help='Filter secrets by prefix')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export secrets')
    export_parser.add_argument('--output', help='Output file path (default: print to console)')
    
    # Validate command
    subparsers.add_parser('validate', help='Validate all secrets')
    
    # Rotate command
    rotate_parser = subparsers.add_parser('rotate', help='Rotate a secret')
    rotate_parser.add_argument('--secret', required=True, help='Secret key to rotate')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a secret')
    delete_parser.add_argument('--secret', required=True, help='Secret key to delete')
    delete_parser.add_argument('--force', action='store_true', help='Force delete without recovery')
    
    # Get command
    get_parser = subparsers.add_parser('get', help='Get a secret value')
    get_parser.add_argument('--secret', required=True, help='Secret key to retrieve')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize secrets manager
    secrets_manager = SecretsManager()
    secrets_manager.check_prerequisites()
    
    # Execute command
    if args.command == 'setup':
        interactive = not args.non_interactive
        
        # Setup core secrets
        all_results = secrets_manager.setup_core_secrets(interactive)
        
        # Summary
        print("\n• Setup Summary:")
        for secret_key, success in all_results.items():
            status = "✅ Success" if success else "❌ Failed"
            print(f"  {secret_key}: {status}")
            
    elif args.command == 'list':
        secrets = secrets_manager.list_secrets(args.filter)
        if secrets:
            print(f"\n• Found {len(secrets)} secrets:")
            for secret in secrets:
                print(f"  {secret['name']}")
                print(f"    Description: {secret['description']}")
                print(f"    Created: {secret['created']}")
                print(f"    Environment: {secret['tags'].get('Environment', 'N/A')}")
                print()
        else:
            print("No secrets found")
            
    elif args.command == 'export':
        success = secrets_manager.export_secrets_to_env(args.output)
        if not success:
            sys.exit(1)
            
    elif args.command == 'validate':
        results = secrets_manager.validate_secrets()
        print(f"\n• Validation Summary:")
        for secret_key, success in results.items():
            status = "✅ Valid" if success else "❌ Missing"
            print(f"  {secret_key}: {status}")
            
    elif args.command == 'rotate':
        if args.secret not in secrets_manager.secret_names:
            print(f"❌ Unknown secret: {args.secret}")
            print(f"Available secrets: {', '.join(secrets_manager.secret_names.keys())}")
            sys.exit(1)
        
        secret_name = secrets_manager.secret_names[args.secret]
        success = secrets_manager.rotate_secret(secret_name)
        if not success:
            sys.exit(1)
            
    elif args.command == 'delete':
        if args.secret not in secrets_manager.secret_names:
            print(f"❌ Unknown secret: {args.secret}")
            print(f"Available secrets: {', '.join(secrets_manager.secret_names.keys())}")
            sys.exit(1)
        
        secret_name = secrets_manager.secret_names[args.secret]
        success = secrets_manager.delete_secret(secret_name, args.force)
        if not success:
            sys.exit(1)
            
    elif args.command == 'get':
        if args.secret not in secrets_manager.secret_names:
            print(f"❌ Unknown secret: {args.secret}")
            print(f"Available secrets: {', '.join(secrets_manager.secret_names.keys())}")
            sys.exit(1)
        
        secret_name = secrets_manager.secret_names[args.secret]
        secret_value = secrets_manager.get_secret(secret_name)
        if secret_value:
            print(f"Secret value for {args.secret}:")
            print(secret_value)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
