import datetime
import os
from typing import Any, Dict

import boto3

dynamodb = boto3.resource("dynamodb")


def get_table():
    """Get DynamoDB table with lazy initialization"""
    dynamodb_table = os.environ.get("DYNAMODB_TABLE")
    if not dynamodb_table:
        raise ValueError("DYNAMODB_TABLE environment variable not set")

    return dynamodb.Table(dynamodb_table)


def db_create_or_update_user_record(
    user_id: str, platform_user_id: str, platform_user_data: Dict[str, Any]
) -> None:
    """
    Create or update user in DynamoDB

    Args:
        user_id: The Vibe user ID
        platform_user_id: The platform user ID
        platform_user_data: The platform user data dictionary
    """
    table = get_table()
    now = datetime.datetime.utcnow().isoformat() + "Z"

    # Use UpdateItem to handle both create and update
    table.update_item(
        Key={"PK": f"USER#{user_id}", "SK": "METADATA"},
        UpdateExpression="SET platform = :platform, platformId = :pid, platformMetadata = :pmd, lastActiveAt = :laa, #prefs = :prefs, GSI1PK = :gsi1pk, GSI1SK = :gsi1sk",
        ExpressionAttributeNames={"#prefs": "preferences"},
        ExpressionAttributeValues={
            ":platform": "tg",
            ":pid": platform_user_id,
            ":pmd": platform_user_data,
            ":laa": now,
            ":prefs": {"notifications": True, "privacy": "public"},
            ":gsi1pk": f"USER#{user_id}",
            ":gsi1sk": "METADATA",
        },
    )
