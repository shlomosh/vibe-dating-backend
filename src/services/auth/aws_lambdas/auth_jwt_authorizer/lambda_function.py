"""
Vibe JWT Authorizer Lambda Function

This function validates JWT tokens for API Gateway authorization.
"""

from typing import Any, Dict

from core.auth_utils import generate_policy, verify_jwt_token_with_secret_manager


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
        # Extract token from Authorization header
        auth_header = event.get("authorizationToken", "")

        if not auth_header:
            raise Exception("Missing authorization token")

        if not auth_header.startswith("Bearer "):
            raise Exception("Invalid authorization header format")

        token = auth_header.replace("Bearer ", "")

        # Verify JWT token using secret from AWS Secrets Manager
        payload = verify_jwt_token_with_secret_manager(token)
        user_id = payload["uid"]

        # Generate allow policy
        policy = generate_policy(
            principal_id=user_id,
            effect="Allow",
            resource=event["methodArn"],
            context={
                "uid": user_id,
                "iss": payload.get("iss"),
                "iat": str(payload.get("iat")),
                "exp": str(payload.get("exp")),
            },
        )

    except Exception as ex:
        # Generate deny policy
        policy = generate_policy(
            principal_id="unauthorized",
            effect="Deny",
            resource=event["methodArn"],
            context={"error": str(ex)},
        )

    print(f"Authorization policy: {policy}")
    return policy
