# core/utils.py
import hashlib, random, string, socket, uuid, re, platform
from datetime import datetime


def get_mac_address() -> str:
    try:
        mac = uuid.getnode()
        return ':'.join(('%012X' % mac)[i:i+2] for i in range(0,12,2))
    except Exception:
        return "00:00:00:00:00:00"


def get_mac_hash() -> str:
    return hashlib.sha256(get_mac_address().encode()).hexdigest()


def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]; s.close(); return ip
    except Exception:
        return "127.0.0.1"


def get_public_ip() -> str:
    try:
        import urllib.request
        with urllib.request.urlopen("https://api.ipify.org", timeout=5) as r:
            return r.read().decode().strip()
    except Exception:
        return get_local_ip()


def generate_serial_key(prefix="EDIT") -> str:
    chars = string.ascii_uppercase + string.digits
    chars = chars.replace("0","").replace("O","").replace("1","").replace("I","")
    groups = ["".join(random.choices(chars,k=4)) for _ in range(3)]
    return f"{prefix}-{'-'.join(groups)}"


def format_date_br(date_str: str) -> str:
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return date_str or "—"


def format_datetime_br(dt_str: str) -> str:
    if not dt_str: return "—"
    try:
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")
    except Exception:
        try:
            return datetime.strptime(dt_str[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
        except Exception:
            return dt_str


def days_remaining(valid_until: str) -> int:
    try:
        return (datetime.strptime(valid_until,"%Y-%m-%d") - datetime.now()).days
    except Exception:
        return -999


def is_expired(valid_until: str) -> bool:
    return days_remaining(valid_until) < 0


def extract_youtube_id(url: str) -> str:
    m = re.search(r"(?:v=|/v/|youtu\.be/|/embed/|/watch\?v=)([A-Za-z0-9_-]{11})", url)
    return m.group(1) if m else ""


def get_system_info() -> dict:
    return {
        "os": platform.system(), "os_version": platform.version(),
        "machine": platform.machine(), "python": platform.python_version(),
        "mac": get_mac_address(), "ip": get_local_ip(),
    }
