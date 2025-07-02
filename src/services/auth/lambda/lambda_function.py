"""
Vibe Authentication Lambda Functions

This file contains both the Telegram authentication and JWT authorization functions.
The function type is determined by the LAMBDA_FUNCTION_TYPE environment variable.
"""

import json
import os
import hmac
import hashlib
import uuid
import base64
import datetime
import jwt
import boto3
from urllib.parse import unquote, parse_qs
from typing import Dict, Any, Optional

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])


def verify_telegram_data(init_data: str, bot_token: str) -> bool:
    """
    Verify Telegram WebApp init data integrity
    
    Args:
        init_data: The init data string from Telegram WebApp
        bot_token: The Telegram bot token
        
    Returns:
        bool: True if data is valid, False otherwise
    """
    try:
        # Parse the init data
        data_pairs = []
        hash_value = None
        
        for item in init_data.split('&'):
            if item.startswith('hash='):
                hash_value = item[5:]
            else:
                data_pairs.append(item)
        
        # Sort and join data
        data_pairs.sort()
        data_check_string = '\n'.join(data_pairs)
        
        # Create secret key
        secret_key = hmac.new(
            b"WebAppData", 
            bot_token.encode(), 
            hashlib.sha256
        ).digest()
        
        # Calculate expected hash
        expected_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hash_value == expected_hash
    except Exception as e:
        print(f"Error verifying Telegram data: {str(e)}")
        return False


def hash_string_to_id(platform_id_string: str, length: int = 8) -> str:
    """
    Convert platform ID string to Vibe user ID using UUID v5
    
    Args:
        platform_id_string: String in format "tg:123456789"
        length: Length of the final user ID (default: 8)
        
    Returns:
        str: Base64 encoded user ID
    """
    # Create UUID v5 with fixed namespace
    namespace_uuid = uuid.UUID('f205b16e-4eac-11f0-a692-00155dcd3c6a')
    user_uuid = uuid.uuid5(namespace_uuid, platform_id_string)
    
    # Convert UUID to base64
    uuid_bytes = user_uuid.bytes
    base64_string = base64.b64encode(uuid_bytes).decode('utf-8')
    
    # Remove padding and return first N characters
    return base64_string.rstrip('=')[:length]


def generate_jwt_token(user_id: str) -> str:
    """
    Generate JWT token for authenticated user
    
    Args:
        user_id: The Vibe user ID
        
    Returns:
        str: JWT token string
    """
    payload = {
        'user_id': user_id,
        'iat': datetime.datetime.utcnow(),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7),
        'iss': 'vibe-app'
    }
    
    secret = os.environ['JWT_SECRET']
    return jwt.encode(payload, secret, algorithm='HS256')


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
        secret = os.environ['JWT_SECRET']
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception('Token has expired')
    except jwt.InvalidTokenError:
        raise Exception('Invalid token')


def create_or_update_user(user_id: str, telegram_user: Dict[str, Any]) -> None:
    """
    Create or update user in DynamoDB
    
    Args:
        user_id: The Vibe user ID
        telegram_user: Telegram user data dictionary
    """
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    
    # Use UpdateItem to handle both create and update
    table.update_item(
        Key={'PK': f'USER#{user_id}', 'SK': 'METADATA'},
        UpdateExpression='SET telegramId = :tid, telegramUsername = :tun, telegramFirstName = :tfn, telegramLastName = :tln, lastActiveAt = :laa, #prefs = :prefs, GSI1PK = :gsi1pk, GSI1SK = :gsi1sk',
        ExpressionAttributeNames={
            '#prefs': 'preferences'
        },
        ExpressionAttributeValues={
            ':tid': str(telegram_user['id']),
            ':tun': telegram_user.get('username'),
            ':tfn': telegram_user.get('first_name'),
            ':tln': telegram_user.get('last_name'),
            ':laa': now,
            ':prefs': {
                'notifications': True,
                'privacy': 'public'
            },
            ':gsi1pk': f'USER#{user_id}',
            ':gsi1sk': 'METADATA'
        }
    )


def add_security_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """
    Add security headers to response
    
    Args:
        headers: Existing headers dictionary
        
    Returns:
        Dict[str, str]: Headers with security headers added
    """
    security_headers = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'"
    }
    
    return {**headers, **security_headers}


def generate_policy(principal_id: str, effect: str, resource: str, context: Dict[str, Any]) -> Dict[str, Any]:
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
        'principalId': principal_id,
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Action': 'execute-api:Invoke',
                    'Effect': effect,
                    'Resource': resource
                }
            ]
        },
        'context': context
    }


def telegram_auth_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for Telegram authentication
    
    Args:
        event: Lambda event object
        context: Lambda context object
        
    Returns:
        Dict[str, Any]: API Gateway response
    """
    try:
        # Parse request body
        body = json.loads(event['body'])
        init_data = body.get('initData')
        telegram_user = body.get('telegramUser')
        
        if not init_data or not telegram_user:
            return {
                'statusCode': 400,
                'headers': add_security_headers({
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'POST,OPTIONS'
                }),
                'body': json.dumps({'error': 'Missing required fields'})
            }
        
        # Verify Telegram data
        bot_token = os.environ['TELEGRAM_BOT_TOKEN']
        if not verify_telegram_data(init_data, bot_token):
            return {
                'statusCode': 401,
                'headers': add_security_headers({
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'POST,OPTIONS'
                }),
                'body': json.dumps({'error': 'Invalid Telegram data'})
            }
        
        # Generate user ID
        platform_id_string = f"tg:{telegram_user['id']}"
        user_id = hash_string_to_id(platform_id_string)
        
        # Create or update user in DynamoDB
        create_or_update_user(user_id, telegram_user)
        
        # Generate JWT token
        token = generate_jwt_token(user_id)
        
        return {
            'statusCode': 200,
            'headers': add_security_headers({
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'POST,OPTIONS'
            }),
            'body': json.dumps({
                'token': token,
                'userId': user_id,
                'telegramUser': {
                    'id': telegram_user['id'],
                    'username': telegram_user.get('username'),
                    'firstName': telegram_user.get('first_name'),
                    'lastName': telegram_user.get('last_name')
                }
            })
        }
        
    except Exception as e:
        print(f"Error in telegram_auth_handler: {str(e)}")
        return {
            'statusCode': 500,
            'headers': add_security_headers({
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'POST,OPTIONS'
            }),
            'body': json.dumps({'error': 'Internal server error'})
        }


def jwt_authorizer_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
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
        auth_header = event.get('authorizationToken', '')
        
        if not auth_header:
            raise Exception('Missing authorization token')
        
        if not auth_header.startswith('Bearer '):
            raise Exception('Invalid authorization header format')
        
        token = auth_header.replace('Bearer ', '')
        
        # Verify JWT token
        payload = verify_jwt_token(token)
        user_id = payload['user_id']
        
        # Generate policy allowing access
        policy = generate_policy(
            principal_id=user_id,
            effect='Allow',
            resource=event['methodArn'],
            context={
                'userId': user_id,
                'telegramId': payload.get('telegram_id'),
                'iss': payload.get('iss'),
                'iat': str(payload.get('iat')),
                'exp': str(payload.get('exp'))
            }
        )
        
        return policy
        
    except Exception as e:
        print(f"Authorization error: {str(e)}")
        # Return deny policy
        return generate_policy(
            principal_id='unauthorized',
            effect='Deny',
            resource=event['methodArn'],
            context={'error': str(e)}
        )


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler that routes to appropriate function based on environment variable
    
    Args:
        event: Lambda event object
        context: Lambda context object
        
    Returns:
        Dict[str, Any]: Function response
    """
    function_type = os.environ.get('LAMBDA_FUNCTION_TYPE', 'telegram_auth')
    
    if function_type == 'jwt_authorizer':
        return jwt_authorizer_handler(event, context)
    else:
        return telegram_auth_handler(event, context) 