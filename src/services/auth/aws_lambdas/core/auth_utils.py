"""
Shared utilities for Vibe Authentication Lambda Functions

This module contains common functions used by both the Telegram authentication
and JWT authorization Lambda functions.
"""

import os
import jwt
import boto3
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError


def verify_jwt_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode JWT token

    Args:
        token: JWT token string

    Returns:
        Dict[str, Any]: Decoded token payload

    Raises:
        Exception: If token is invalid or expired
    """
    try:
        secret = os.environ["JWT_SECRET"]
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

        secret = get_secret_from_aws_secrets_manager(jwt_secret_arn)
        if not secret:
            raise Exception("Failed to retrieve JWT secret from Secrets Manager")

        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token has expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")
