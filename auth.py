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


def validate_init_data(init_data: str, user_id_fallback: str = ""):
    """Parse Telegram initData, fallback to x-user-id header."""
    # Try initData first
    if init_data:
        try:
            parsed = dict(parse_qsl(init_data, keep_blank_values=True))
            user_raw = parsed.get("user", "")
            if user_raw:
                user_data = json.loads(unquote(user_raw))
                if user_data.get("id"):
                    print(f"[auth] initData ok, user_id={user_data['id']}")
                    return user_data
        except Exception as e:
            print(f"[auth] initData parse error: {e}")

    # Fallback: trust x-user-id from initDataUnsafe (client-side)
    if user_id_fallback:
        try:
            uid = int(user_id_fallback)
            if uid > 0:
                print(f"[auth] fallback user_id={uid}")
                return {"id": uid}
        except Exception:
            pass

    print(f"[auth] no valid user, init_data={bool(init_data)}, fallback={user_id_fallback!r}")
    return None


def get_role(user_id: int) -> str:
    admin_id = _get_admin_id()
    role = "admin" if user_id == admin_id else ("driver" if user_id in _get_driver_ids() else "client")
    print(f"[auth] get_role user_id={user_id} admin_id={admin_id} → {role}")
    return role
