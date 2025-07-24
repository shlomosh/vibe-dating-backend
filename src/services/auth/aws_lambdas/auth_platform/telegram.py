import hashlib
import hmac
import json
import os
import urllib.parse
from typing import Any, Dict, Optional

from core.auth_utils import get_secret_from_aws_secrets_manager
from core.rest_utils import ResponseError


def telegram_verify_data(init_data: str, bot_token: str) -> Optional[Dict[str, Any]]:
    """
    Verify Telegram WebApp init data integrity

    Args:
        init_data: The init data string from Telegram WebApp
        bot_token: The Telegram bot token

    Returns:
        Optional[Dict[str, Any]]: User data if data is valid, None otherwise
    """
    try:
        # Parse and decode query string
        params = {
            k: urllib.parse.unquote(v)
            for k, v in [s.split("=", 1) for s in init_data.split("&")]
        }
        telegram_hash = params.pop("hash", None)
        if not telegram_hash:
            raise ValueError("Hash not found in telegram authentication data")

        # Create data check string
        data_params_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))

        # Generate secret key
        secret_key = hmac.new(
            "WebAppData".encode(), bot_token.encode(), hashlib.sha256
        ).digest()

        # Calculate hash
        calculated_hash = hmac.new(
            secret_key, data_params_string.encode(), hashlib.sha256
        ).hexdigest()

        if calculated_hash == telegram_hash:
            user_data_string = params.get("user")
            if not user_data_string:
                raise ValueError("User data not found in telegram authentication data")

            return json.loads(user_data_string)
        else:
            return None

    except Exception as e:
        raise ResponseError(500, {"error": f"Failed to verify Telegram data: {str(e)}"})


def authenticate_user(platform_token: str) -> Dict[str, Any]:
    telegram_bot_token_arn = os.environ.get("TELEGRAM_BOT_TOKEN_SECRET_ARN")
    if not telegram_bot_token_arn:
        raise ResponseError(500, {"error": "Telegram bot token not configured"})

    bot_token = get_secret_from_aws_secrets_manager(telegram_bot_token_arn)
    if not bot_token:
        raise ResponseError(500, {"error": "Failed to retrieve Telegram bot token"})

    user_data = telegram_verify_data(platform_token, bot_token)
    if not user_data:
        raise ResponseError(401, {"error": "Invalid Telegram data"})

    return user_data
