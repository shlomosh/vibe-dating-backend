import os
from typing import Any, Dict, Optional

from botocore.exceptions import ClientError


class DynamoDBService:
    dynamodb = None

    @classmethod
    def get_table(cls, table_name: Optional[str] = None):
        """Get DynamoDB table with lazy initialization"""

        if cls.dynamodb is None:
            import boto3

            cls.dynamodb = boto3.resource("dynamodb")

        if table_name is None:
            table_name = os.environ.get("DYNAMODB_TABLE")
            if not table_name:
                raise ValueError("DYNAMODB_TABLE environment variable not set")

        try:
            return cls.dynamodb.Table(table_name)
        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize DynamoDB table {table_name}: {str(e)}"
            )

    @classmethod
    def serialize_dynamodb_item(cls, item: Dict[str, Any]) -> Dict[str, Any]:
        """Efficiently serialize items for DynamoDB"""
        serialized = {}
        for key, value in item.items():
            if isinstance(value, str):
                serialized[key] = {"S": value}
            elif isinstance(value, (int, float)):
                serialized[key] = {"N": str(value)}
            elif isinstance(value, bool):
                serialized[key] = {"BOOL": value}
            elif isinstance(value, list):
                serialized[key] = {
                    "L": [
                        cls.serialize_dynamodb_item([v])[0]
                        if isinstance(v, dict)
                        else {"S": str(v)}
                        for v in value
                    ]
                }
            elif isinstance(value, dict):
                serialized[key] = {"M": cls.serialize_dynamodb_item(value)}
            else:
                serialized[key] = {"S": str(value)}

        return serialized


class SecretsManagerService:
    secretsmanager = None

    @classmethod
    def get_secret(cls, secret_arn: str) -> Optional[str]:
        """Get a secret from AWS Secrets Manager"""

        if cls.secretsmanager is None:
            import boto3

            cls.secretsmanager = boto3.client("secretsmanager")

        try:
            print("secret_arn", secret_arn)
            response = cls.secretsmanager.get_secret_value(SecretId=secret_arn)

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
