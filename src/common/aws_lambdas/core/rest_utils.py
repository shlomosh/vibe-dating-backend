"""
Shared REST utilities for Vibe Lambda Functions

This module contains common REST response functions used by both auth and user services.
"""

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


class ResponseError(Exception):
    """Custom exception for API responses"""

    def __init__(self, status_code: int, body: Any):
        self.status_code = status_code
        self.body = body
        super().__init__(f"{status_code}: {body}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API Gateway response format"""
        return generate_response(self.status_code, self.body)
