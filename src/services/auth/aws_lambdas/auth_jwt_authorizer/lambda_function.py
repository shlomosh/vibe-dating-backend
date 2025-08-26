"""
Vibe JWT Authorizer Lambda Function

This function validates JWT tokens for API Gateway authorization.
"""

import os
from typing import Any, Dict

import jwt

from core.aws import SecretsManagerService


def api_verify_jwt_token(token: str) -> Dict[str, Any]:
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


def api_generate_policy(
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


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda authorizer for API Gateway

    Args:
        event: Lambda event object containing authorization details
        context: Lambda context object

    Returns:
        Dict[str, Any]: IAM policy document
    """
    try:
        import json

        print(f"JWT Authorizer Event: {json.dumps(event)}")

        # Extract token from Authorization header
        auth_header = event.get("authorizationToken", "")

        if not auth_header:
            raise Exception("Missing authorization token")

        if not auth_header.startswith("Bearer "):
            raise Exception("Invalid authorization header format")

        token = auth_header.replace("Bearer ", "")

        # Verify JWT token using secret from AWS Secrets Manager
        payload = api_verify_jwt_token(token)
        user_id = payload["uid"]

        # Generate allow policy with proper resource pattern
        # The methodArn format is: arn:aws:execute-api:region:account:api-id/stage/HTTP-VERB/resource-path
        method_arn = event["methodArn"]
        arn_parts = method_arn.split('/')
        
        if len(arn_parts) >= 3:
            # Extract the base API ARN and allow access to all methods/resources under this API
            # For paths like /profile/{profileId}/media, we want to allow access to all sub-resources
            method_arn = f"{'/'.join(arn_parts[:-1])}/*"

        print(f"Resource ARN: {method_arn}")
        
        policy = {
            "principalId": user_id,
            "policyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": "execute-api:Invoke",
                        "Effect": "Allow",
                        "Resource": method_arn
                    }
                ],
            },
            "context": {
                "uid": user_id,
                "iss": payload.get("iss"),
                "iat": str(payload.get("iat")),
                "exp": str(payload.get("exp")),
            },
        }

    except Exception as ex:
        # Generate deny policy
        policy = api_generate_policy(
            principal_id="unauthorized",
            effect="Deny",
            resource=event["methodArn"],
            context={"error": str(ex)},
        )

    print(f"Authorization policy: {policy}")
    return policy
