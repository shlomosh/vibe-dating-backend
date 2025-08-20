"""
Shared authentication utilities for Vibe Lambda Functions

This module contains common authentication functions used by both auth and user services.
"""

import base64
import datetime
import os
import uuid
from typing import Any, Dict

import jwt

from core.aws import SecretsManagerService


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


def generate_jwt_token(signed_data: Dict[str, Any], expires_in: int = 7) -> str:
    """
    Generate JWT token for authenticated user

    Args:
        signed_data: Data to include in the JWT token
        expires_in: Number of days until token expires (default: 7)

    Returns:
        str: JWT token string
    """
    payload = {
        **signed_data,
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=expires_in),
        "iss": "vibe-app",
    }

    # Get JWT secret from AWS Secrets Manager
    jwt_secret_arn = os.environ.get("JWT_SECRET_ARN")
    if not jwt_secret_arn:
        raise Exception("JWT_SECRET_ARN environment variable not set")

    secret = SecretsManagerService.get_secret(jwt_secret_arn)
    if not secret:
        raise Exception("Failed to retrieve JWT secret from Secrets Manager")

    return jwt.encode(payload, secret, algorithm="HS256")


def verify_jwt_token_with_secret_manager(token: str) -> Dict[str, Any]:
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

        secret = SecretsManagerService.get_secret(jwt_secret_arn)
        if not secret:
            raise Exception("Failed to retrieve JWT secret from Secrets Manager")

        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload

    except jwt.ExpiredSignatureError:
        raise Exception("Token has expired")

    except jwt.InvalidTokenError:
        raise Exception("Invalid token")


def generate_policy(
    principal_id: str, effect: str, resource: str, context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate IAM policy for API Gateway

    Args:
        principal_id: User ID for the principal
        effect: 'Allow' or 'Deny'
        resource: API Gateway resource ARN
        context: Additional context to pass to Lambda functions

    Returns:
        Dict[str, Any]: IAM policy document
    """
    return {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {"Action": "execute-api:Invoke", "Effect": effect, "Resource": resource}
            ],
        },
        "context": context,
    }


def get_secret_from_aws_secrets_manager(secret_arn: str) -> str:
    """
    Get secret from AWS Secrets Manager

    Args:
        secret_arn: ARN of the secret

    Returns:
        str: Secret value
    """
    return SecretsManagerService.get_secret(secret_arn)
