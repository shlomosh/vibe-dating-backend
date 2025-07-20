"""
Authentication utilities for user service
"""

import os
from typing import Any, Dict, Optional

import boto3
import jwt
from botocore.exceptions import ClientError


def get_secret_from_aws_secrets_manager(secret_arn: str) -> Optional[str]:
    """
    Retrieve a secret value from AWS Secrets Manager
    
    Args:
        secret_arn: ARN of the secret in AWS Secrets Manager
        
    Returns:
        Optional[str]: Secret value if found, None otherwise
        
    Raises:
        Exception: If there's an error retrieving the secret
    """
    try:
        secrets_client = boto3.client("secretsmanager")
        response = secrets_client.get_secret_value(SecretId=secret_arn)
        
        if "SecretString" in response:
            return response["SecretString"]
        else:
            # Handle binary secrets
            import base64
            return base64.b64decode(response["SecretBinary"]).decode("utf-8")
            
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "ResourceNotFoundException":
            raise Exception(f"Secret not found: {secret_arn}")
        elif error_code == "InvalidRequestException":
            raise Exception(f"Invalid request for secret: {secret_arn}")
        elif error_code == "InvalidParameterException":
            raise Exception(f"Invalid parameter for secret: {secret_arn}")
        else:
            raise Exception(f"Error retrieving secret {secret_arn}: {str(e)}")


def verify_jwt_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode JWT token using secret from AWS Secrets Manager
    
    Args:
        token: JWT token string
        
    Returns:
        Dict[str, Any]: Decoded token payload
        
    Raises:
        Exception: If token is invalid or expired
    """
    try:
        jwt_secret_arn = os.environ.get("JWT_SECRET_ARN")
        if not jwt_secret_arn:
            raise Exception("JWT_SECRET_ARN environment variable not set")
        
        secret = get_secret_from_aws_secrets_manager(jwt_secret_arn)
        if not secret:
            raise Exception("Failed to retrieve JWT secret from Secrets Manager")
        
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload
        
    except jwt.ExpiredSignatureError:
        raise Exception("Token has expired")
        
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")


def extract_user_id_from_context(event: Dict[str, Any]) -> str:
    """
    Extract user ID from API Gateway request context
    
    Args:
        event: Lambda event object
        
    Returns:
        str: User ID from the JWT token context
        
    Raises:
        Exception: If user ID cannot be extracted
    """
    request_context = event.get("requestContext", {})
    authorizer = request_context.get("authorizer", {})
    
    user_id = authorizer.get("uid")
    if not user_id:
        raise Exception("User ID not found in request context")
    
    return user_id


def hash_string_to_id(platform_id_string: str, length: int = 8) -> str:
    """
    Convert platform ID string to Vibe user ID using UUID v5
    
    Args:
        platform_id_string: String in format "userId:profileIndex"
        length: Length of the final ID (default: 8)
        
    Returns:
        str: Base64 encoded ID
    """
    import base64
    import uuid
    
    # Get UUID namespace from AWS Secrets Manager
    uuid_namespace_arn = os.environ.get("UUID_NAMESPACE_SECRET_ARN")
    if not uuid_namespace_arn:
        raise Exception("UUID_NAMESPACE_SECRET_ARN environment variable not set")
    
    uuid_namespace = get_secret_from_aws_secrets_manager(uuid_namespace_arn)
    if not uuid_namespace:
        raise Exception("Failed to retrieve UUID namespace from Secrets Manager")
    
    # Create UUID v5 with namespace from Secrets Manager
    namespace_uuid = uuid.UUID(uuid_namespace)
    id_uuid = uuid.uuid5(namespace_uuid, platform_id_string)
    
    # Convert UUID to base64
    uuid_bytes = id_uuid.bytes
    base64_string = base64.b64encode(uuid_bytes).decode("utf-8")
    
    # Remove padding and return first N characters
    return base64_string.rstrip("=")[:length]


def get_allocated_profile_ids(user_id: str) -> list:
    """
    Get allocated profile IDs for a user (same logic as auth service)
    
    Args:
        user_id: The user ID
        
    Returns:
        list: List of allocated profile IDs for the user
    """
    from core.settings import CoreSettings
    core_settings = CoreSettings()
    
    return [
        hash_string_to_id(f"{user_id}:{profile_idx}") 
        for profile_idx in range(0, core_settings.max_profile_count)
    ]