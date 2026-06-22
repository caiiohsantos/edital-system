# client/updater.py
import json, urllib.request

APP_VERSION = "1.0.0"


def _version_tuple(v):
    try: return tuple(int(x) for x in v.split("."))
    except Exception: return (0,0,0)


def check_for_updates(update_url, timeout=8):
    if not update_url or not update_url.startswith("http"):
        return None
    try:
        req = urllib.request.Request(update_url, headers={"User-Agent":"EditalSystem/"+APP_VERSION})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode())
        remote = data.get("version","0.0.0")
        if _version_tuple(remote) > _version_tuple(APP_VERSION):
            return data
        return None
    except Exception:
        return None


def get_current_version():
    return APP_VERSION
