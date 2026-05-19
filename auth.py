import os
import hmac
import hashlib
import json
from urllib.parse import parse_qsl, unquote

ADMIN_ID = int(os.getenv("ADMIN_ID", "7555325054"))
DRIVER_IDS = set(
    int(x.strip())
    for x in os.getenv("DRIVER_IDS", "").split(",")
    if x.strip().isdigit()
)


def validate_init_data(init_data: str) -> dict | None:
    """Validate Telegram WebApp initData via HMAC-SHA256. Returns user dict or None."""
    try:
        bot_token = os.getenv("BOT_TOKEN", "")
        parsed = dict(parse_qsl(init_data, keep_blank_values=True))
        hash_value = parsed.pop("hash", "")

        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(parsed.items())
        )

        secret_key = hmac.new(
            key=b"WebAppData",
            msg=bot_token.encode(),
            digestmod=hashlib.sha256,
        ).digest()

        computed = hmac.new(
            key=secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(computed, hash_value):
            return None

        user_data = json.loads(unquote(parsed.get("user", "{}")))
        return user_data
    except Exception as e:
        print(f"validate_init_data error: {e}")
        return None


def get_role(user_id: int) -> str:
    if user_id == ADMIN_ID:
        return "admin"
    if user_id in DRIVER_IDS:
        return "driver"
    return "client"
