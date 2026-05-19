import os
import json
from urllib.parse import parse_qsl, unquote

# runtime set — populated at startup + when drivers activate
_active_drivers: set = set()


def _load_drivers_from_env():
    return set(
        int(x.strip())
        for x in os.getenv("DRIVER_IDS", "").split(",")
        if x.strip().isdigit()
    )


def init_drivers():
    global _active_drivers
    _active_drivers = _load_drivers_from_env()


def add_driver_runtime(user_id: int):
    _active_drivers.add(user_id)


def _get_admin_id():
    return int(os.getenv("ADMIN_ID", "7555325054"))


def validate_init_data(init_data: str, user_id_fallback: str = ""):
    if init_data:
        try:
            parsed = dict(parse_qsl(init_data, keep_blank_values=True))
            user_raw = parsed.get("user", "")
            if user_raw:
                user_data = json.loads(unquote(user_raw))
                if user_data.get("id"):
                    return user_data
        except Exception as e:
            print(f"[auth] initData parse error: {e}")

    if user_id_fallback:
        try:
            uid = int(user_id_fallback)
            if uid > 0:
                return {"id": uid}
        except Exception:
            pass

    return None


def get_role(user_id: int) -> str:
    if user_id == _get_admin_id():
        return "admin"
    if user_id in _active_drivers:
        return "driver"
    return "client"


# initialize on import
init_drivers()
