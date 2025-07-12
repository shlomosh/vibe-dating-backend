import os
import boto3
import datetime
from typing import Dict, Any

dynamodb = boto3.resource("dynamodb", region_name=os.environ["AWS_REGION"])
table = dynamodb.Table(os.environ["DYNAMODB_TABLE"])

def db_create_or_update_user_record(user_id: str, platform_user_id: str, platform_user_data: Dict[str, Any]) -> None:
    """
    Create or update user in DynamoDB

    Args:
        user_id: The Vibe user ID
        platform_user_id: The platform user ID
        platform_user_data: The platform user data dictionary
    """
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
