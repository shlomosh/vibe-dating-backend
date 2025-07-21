"""
Profile management utilities for the user service

This module contains all profile-related functions shared across services.
"""

import datetime
import os
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb")


def get_table():
    """Get DynamoDB table with lazy initialization"""
    dynamodb_table = os.environ.get("DYNAMODB_TABLE")
    if not dynamodb_table:
        raise ValueError("DYNAMODB_TABLE environment variable not set")
    
    return dynamodb.Table(dynamodb_table)


def validate_profile_ownership(user_id: str, profile_id: str) -> bool:
    """
    Validate that a profile belongs to the specified user
    
    Args:
        user_id: The user ID
        profile_id: The profile ID to validate
        
    Returns:
        bool: True if the profile belongs to the user, False otherwise
    """
    table = get_table()
    
    try:
        response = table.get_item(
            Key={"PK": f"USER#{user_id}", "SK": f"PROFILE#{profile_id}"}
        )
        return "Item" in response and response["Item"].get("isActive", False)
    except ClientError:
        return False


def get_user_profile_ids(user_id: str) -> List[str]:
    """
    Get all profile IDs for a user
    
    Args:
        user_id: The user ID
        
    Returns:
        List[str]: List of profile IDs for the user
    """
    table = get_table()
    
    try:
        response = table.query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
            ExpressionAttributeValues={
                ":pk": f"USER#{user_id}",
                ":sk_prefix": "PROFILE#"
            }
        )
        
        return [
            item["profileId"] for item in response.get("Items", [])
            if item.get("isActive", False)
        ]
    except ClientError:
        return []


def create_profile(user_id: str, profile_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new profile for a user
    
    Args:
        user_id: The user ID
        profile_id: The profile ID
        profile_data: Profile data dictionary
        
    Returns:
        Dict[str, Any]: Created profile data
        
    Raises:
        ValueError: If profile creation fails
    """
    table = get_table()
    now = datetime.datetime.utcnow().isoformat() + "Z"
    
    # Validate profile count limit
    current_profiles = get_user_profile_ids(user_id)
    if len(current_profiles) >= 3:  # Max 3 profiles per user
        raise ValueError("Maximum number of profiles (3) reached")
    
    # Prepare profile item (excluding location and last-seen)
    profile_item = {
        "PK": f"PROFILE#{profile_id}",
        "SK": "METADATA",
        "userId": user_id,
        "name": profile_data.get("name", ""),
        "age": profile_data.get("age"),
        "bio": profile_data.get("bio", ""),
        "interests": profile_data.get("interests", []),
        "lookingFor": profile_data.get("lookingFor", []),
        "position": profile_data.get("position"),
        "body": profile_data.get("body"),
        "eggplantSize": profile_data.get("eggplantSize"),
        "peachShape": profile_data.get("peachShape"),
        "sexuality": profile_data.get("sexuality"),
        "healthPractices": profile_data.get("healthPractices"),
        "hivStatus": profile_data.get("hivStatus"),
        "preventionPractices": profile_data.get("preventionPractices"),
        "hosting": profile_data.get("hosting"),
        "travelDistance": profile_data.get("travelDistance"),
        "meetingTime": profile_data.get("meetingTime"),
        "media": profile_data.get("media", {}),
        "isActive": True,
        "createdAt": now,
        "updatedAt": now,
        "TTL": 0
    }
    
    # User-profile lookup item
    lookup_item = {
        "PK": f"USER#{user_id}",
        "SK": f"PROFILE#{profile_id}",
        "profileId": profile_id,
        "isActive": True,
        "createdAt": now
    }
    
    try:
        # Use transact write to ensure both items are created atomically
        dynamodb_client = boto3.client("dynamodb")
        
        # Convert items to DynamoDB format
        from boto3.dynamodb.types import TypeSerializer
        serializer = TypeSerializer()
        
        dynamodb_client.transact_write_items(
            TransactItems=[
                {
                    "Put": {
                        "TableName": table.name,
                        "Item": {k: serializer.serialize(v) for k, v in profile_item.items()},
                        "ConditionExpression": "attribute_not_exists(PK)"
                    }
                },
                {
                    "Put": {
                        "TableName": table.name,
                        "Item": {k: serializer.serialize(v) for k, v in lookup_item.items()},
                        "ConditionExpression": "attribute_not_exists(PK)"
                    }
                }
            ]
        )
        
        return profile_item
        
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise ValueError("Profile already exists")
        else:
            raise ValueError(f"Failed to create profile: {str(e)}")


def update_profile(user_id: str, profile_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update an existing profile
    
    Args:
        user_id: The user ID
        profile_id: The profile ID
        profile_data: Updated profile data
        
    Returns:
        Dict[str, Any]: Updated profile data
        
    Raises:
        ValueError: If profile update fails
    """
    table = get_table()
    
    # Validate ownership
    if not validate_profile_ownership(user_id, profile_id):
        raise ValueError("Profile not found or access denied")
    
    now = datetime.datetime.utcnow().isoformat() + "Z"
    
    # Build update expression dynamically
    update_expression_parts = ["SET updatedAt = :updated_at"]
    expression_attribute_values = {":updated_at": now}
    expression_attribute_names = {}
    
    # Map of field names to update expression parts
    field_mappings = {
        "name": "name = :name",
        "age": "age = :age", 
        "bio": "bio = :bio",
        "interests": "interests = :interests",
        "lookingFor": "lookingFor = :looking_for",
        "position": "#position = :position",  # position is a reserved word
        "body": "body = :body",
        "eggplantSize": "eggplantSize = :eggplant_size",
        "peachShape": "peachShape = :peach_shape",
        "sexuality": "sexuality = :sexuality",
        "healthPractices": "healthPractices = :health_practices",
        "hivStatus": "hivStatus = :hiv_status",
        "preventionPractices": "preventionPractices = :prevention_practices",
        "hosting": "hosting = :hosting",
        "travelDistance": "travelDistance = :travel_distance",
        "meetingTime": "meetingTime = :meeting_time",
        "media": "media = :media"
    }
    
    for field, expression in field_mappings.items():
        if field in profile_data:
            if field == "position":
                expression_attribute_names["#position"] = "position"
                expression_attribute_values[":position"] = profile_data[field]
            else:
                attr_value_key = f":{field.lower().replace('_', '_')}"
                if field == "eggplantSize":
                    attr_value_key = ":eggplant_size"
                elif field == "peachShape":
                    attr_value_key = ":peach_shape"
                elif field == "lookingFor":
                    attr_value_key = ":looking_for"
                elif field == "healthPractices":
                    attr_value_key = ":health_practices"
                elif field == "hivStatus":
                    attr_value_key = ":hiv_status"
                elif field == "preventionPractices":
                    attr_value_key = ":prevention_practices"
                elif field == "travelDistance":
                    attr_value_key = ":travel_distance"
                elif field == "meetingTime":
                    attr_value_key = ":meeting_time"
                else:
                    attr_value_key = f":{field}"
                
                expression_attribute_values[attr_value_key] = profile_data[field]
            
            update_expression_parts.append(expression)
    
    update_expression = ", ".join(update_expression_parts)
    
    try:
        kwargs = {
            "Key": {"PK": f"PROFILE#{profile_id}", "SK": "METADATA"},
            "UpdateExpression": update_expression,
            "ExpressionAttributeValues": expression_attribute_values,
            "ReturnValues": "ALL_NEW"
        }
        
        if expression_attribute_names:
            kwargs["ExpressionAttributeNames"] = expression_attribute_names
        
        response = table.update_item(**kwargs)
        
        return response["Attributes"]
        
    except ClientError as e:
        raise ValueError(f"Failed to update profile: {str(e)}")


def delete_profile(user_id: str, profile_id: str) -> bool:
    """
    Delete a profile
    
    Args:
        user_id: The user ID
        profile_id: The profile ID
        
    Returns:
        bool: True if deletion was successful
        
    Raises:
        ValueError: If profile deletion fails
    """
    table = get_table()
    
    # Validate ownership
    if not validate_profile_ownership(user_id, profile_id):
        raise ValueError("Profile not found or access denied")
    
    try:
        # Use transact write to delete both profile and lookup items
        dynamodb_client = boto3.client("dynamodb")
        
        dynamodb_client.transact_write_items(
            TransactItems=[
                {
                    "Delete": {
                        "TableName": table.name,
                        "Key": {
                            "PK": {"S": f"PROFILE#{profile_id}"},
                            "SK": {"S": "METADATA"}
                        }
                    }
                },
                {
                    "Delete": {
                        "TableName": table.name,
                        "Key": {
                            "PK": {"S": f"USER#{user_id}"},
                            "SK": {"S": f"PROFILE#{profile_id}"}
                        }
                    }
                }
            ]
        )
        
        return True
        
    except ClientError as e:
        raise ValueError(f"Failed to delete profile: {str(e)}")


def get_profile(profile_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a profile by ID
    
    Args:
        profile_id: The profile ID
        
    Returns:
        Optional[Dict[str, Any]]: Profile data if found, None otherwise
    """
    table = get_table()
    
    try:
        response = table.get_item(
            Key={"PK": f"PROFILE#{profile_id}", "SK": "METADATA"}
        )
        
        if "Item" in response:
            return response["Item"]
        return None
        
    except ClientError:
        return None


def upsert_profile(user_id: str, profile_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create or update a profile (upsert operation)
    
    Args:
        user_id: The user ID
        profile_id: The profile ID
        profile_data: Profile data dictionary
        
    Returns:
        Dict[str, Any]: Result containing profile data and creation status
        
    Raises:
        ValueError: If profile operation fails
    """
    # Check if profile already exists
    existing_profile = get_profile(profile_id)
    
    if existing_profile:
        # Profile exists, update it
        updated_profile = update_profile(user_id, profile_id, profile_data)
        return {
            "profile": updated_profile,
            "created": False
        }
    else:
        # Profile doesn't exist, create it
        created_profile = create_profile(user_id, profile_id, profile_data)
        return {
            "profile": created_profile,
            "created": True
        }