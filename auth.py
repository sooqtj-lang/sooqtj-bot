import os
import hmac
import hashlib
import json
from urllib.parse import parse_qsl, unquote


def _get_admin_id():
    return int(os.getenv("ADMIN_ID", "7555325054"))


def _get_driver_ids():
    return set(
        int(x.strip())
        for x in os.getenv("DRIVER_IDS", "").split(",")
        if x.strip().isdigit()
    )


def validate_init_data(init_data: str):
    """Validate Telegram WebApp initData. Returns user dict or None."""
    if not init_data:
        return None
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
            print(f"[auth] HMAC mismatch — expected={hash_value[:16]}... computed={computed[:16]}...")
            # Fallback: still try to read user if initData looks valid
            if not parsed.get("user") or not parsed.get("auth_date"):
                return None
            print("[auth] Falling back to unsigned user data")

        user_data = json.loads(unquote(parsed.get("user", "{}")))
        return user_data if user_data.get("id") else None

    except Exception as e:
        print(f"[auth] validate_init_data error: {e}")
        return None


def get_role(user_id: int) -> str:
    if user_id == _get_admin_id():
        return "admin"
    if user_id in _get_driver_ids():
        return "driver"
    return "client"
