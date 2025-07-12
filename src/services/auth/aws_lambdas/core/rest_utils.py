import json
from typing import Any, Dict


def generate_response(status_code: int, body: Any) -> Dict[str, Any]:
    security_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,Authorization",
        "Access-Control-Allow-Methods": "POST,OPTIONS",
    }

    response_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,Authorization",
        "Access-Control-Allow-Methods": "POST,OPTIONS",
    }

    return {
        "statusCode": status_code,
        "headers": {**response_headers, **security_headers},
        "body": json.dumps(body),
    }


class ResponseError(Exception):
    def __init__(self, status_code: int, body: Any):
        self.status_code = status_code
        self.body = body

    def __str__(self):
        return f"ResponseError: {self.status_code} {self.body}"

    def to_dict(self) -> Dict[str, Any]:
        return generate_response(self.status_code, self.body)
