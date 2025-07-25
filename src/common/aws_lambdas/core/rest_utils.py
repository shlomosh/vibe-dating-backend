"""
Shared REST utilities for Vibe Lambda Functions

This module contains common REST response functions used by both auth and user services.
"""

import base64
import json
from typing import Any, Dict


def generate_response(status_code: int, body: Any) -> Dict[str, Any]:
    """
    Generate standardized API Gateway response

    Args:
        status_code: HTTP status code
        body: Response body (will be JSON serialized)

    Returns:
        Dict[str, Any]: API Gateway response format
    """
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
        },
        "body": json.dumps(body, default=str),
    }


def parse_request_body(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse request body from Lambda event

    Handles base64 decoding and JSON parsing with proper error handling.

    Args:
        event: Lambda event object

    Returns:
        Dict[str, Any]: Parsed JSON body

    Raises:
        ResponseError: If body is missing, base64 decoding fails, or JSON is invalid
    """
    # Parse request body
    request_body = event.get("body")
    if not request_body:
        raise ResponseError(400, {"error": "Missing request body"})

    # Handle base64 encoded body
    if event.get("isBase64Encoded", False):
        try:
            request_body = base64.b64decode(request_body).decode("utf-8")
        except Exception as e:
            raise ResponseError(
                400, {"error": f"Failed to decode base64 body: {str(e)}"}
            )

    try:
        body = json.loads(request_body)
    except json.JSONDecodeError as e:
        raise ResponseError(400, {"error": f"Invalid JSON in request body: {str(e)}"})

    return body


class ResponseError(Exception):
    """Custom exception for API responses"""

    def __init__(self, status_code: int, body: Any):
        self.status_code = status_code
        self.body = body
        super().__init__(f"{status_code}: {body}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API Gateway response format"""
        return generate_response(self.status_code, self.body)
