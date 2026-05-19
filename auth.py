import os
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
    """Parse Telegram WebApp initData and return user dict."""
    if not init_data:
        return None
    try:
        parsed = dict(parse_qsl(init_data, keep_blank_values=True))
        user_raw = parsed.get("user", "")
        if not user_raw:
            return None
        user_data = json.loads(unquote(user_raw))
        uid = user_data.get("id")
        print(f"[auth] user_id={uid} admin_id={_get_admin_id()}")
        return user_data if uid else None
    except Exception as e:
        print(f"[auth] error: {e}")
        return None


def get_role(user_id: int) -> str:
    admin_id = _get_admin_id()
    print(f"[auth] get_role: user_id={user_id} ({type(user_id)}) admin_id={admin_id} ({type(admin_id)}) match={user_id == admin_id}")
    if user_id == admin_id:
        return "admin"
    if user_id in _get_driver_ids():
        return "driver"
    return "client"
