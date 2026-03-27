# core/utils.py
import hashlib
import random
import string
import socket
import uuid
import re
import os
import platform
from datetime import datetime


# ─────────────────────────────────────────────
#  NETWORK / DEVICE IDENTIFICATION
# ─────────────────────────────────────────────

def get_mac_address() -> str:
    """Get MAC address of the primary network interface."""
    try:
        mac = uuid.getnode()
        mac_str = ':'.join(('%012X' % mac)[i:i+2] for i in range(0, 12, 2))
        return mac_str
    except Exception:
        return "00:00:00:00:00:00"


def get_mac_hash() -> str:
    """Return SHA-256 hash of MAC address."""
    mac = get_mac_address()
    return hashlib.sha256(mac.encode()).hexdigest()


def get_local_ip() -> str:
    """Get local IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def get_public_ip() -> str:
    """Get public IP address (requires internet)."""
    try:
        import urllib.request
        with urllib.request.urlopen("https://api.ipify.org", timeout=5) as r:
            return r.read().decode().strip()
    except Exception:
        return get_local_ip()


# ─────────────────────────────────────────────
#  SERIAL KEY GENERATION
# ─────────────────────────────────────────────

def generate_serial_key(prefix: str = "EDIT") -> str:
    """Generate a serial key in format: PREFIX-XXXX-XXXX-XXXX"""
    chars = string.ascii_uppercase + string.digits
    # Remove ambiguous chars
    chars = chars.replace("0", "").replace("O", "").replace("1", "").replace("I", "")
    groups = ["".join(random.choices(chars, k=4)) for _ in range(3)]
    return f"{prefix}-{'-'.join(groups)}"


def format_serial_key(raw: str) -> str:
    """Format a raw key string into XXXX-XXXX-XXXX-XXXX groups."""
    clean = re.sub(r"[^A-Z0-9a-z]", "", raw.upper())
    if len(clean) < 4:
        return raw.upper()
    groups = [clean[i:i+4] for i in range(0, min(len(clean), 16), 4)]
    return "-".join(groups)


def validate_serial_format(serial: str) -> bool:
    """Check if serial matches expected format."""
    pattern = r"^[A-Z]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$"
    return bool(re.match(pattern, serial.upper()))


# ─────────────────────────────────────────────
#  DATE UTILITIES
# ─────────────────────────────────────────────

def format_date_br(date_str: str) -> str:
    """Convert YYYY-MM-DD to DD/MM/YYYY."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return date_str


def format_datetime_br(dt_str: str) -> str:
    """Format a datetime string to Brazilian format."""
    if not dt_str:
        return "—"
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        try:
            dt = datetime.strptime(dt_str[:10], "%Y-%m-%d")
            return dt.strftime("%d/%m/%Y")
        except Exception:
            return dt_str


def days_remaining(valid_until: str) -> int:
    """Return number of days until expiry (negative if expired)."""
    try:
        exp = datetime.strptime(valid_until, "%Y-%m-%d")
        delta = (exp - datetime.now()).days
        return delta
    except Exception:
        return -999


def is_expired(valid_until: str) -> bool:
    return days_remaining(valid_until) < 0


# ─────────────────────────────────────────────
#  URL / YouTube UTILITIES
# ─────────────────────────────────────────────

def extract_youtube_id(url: str) -> str:
    """Extract YouTube video ID from various URL formats."""
    patterns = [
        r"(?:v=|/v/|youtu\.be/|/embed/|/watch\?v=)([A-Za-z0-9_-]{11})",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return ""


def make_youtube_embed_url(url: str) -> str:
    """Convert any YouTube URL to embed URL."""
    vid_id = extract_youtube_id(url)
    if vid_id:
        return f"https://www.youtube.com/embed/{vid_id}?autoplay=0&rel=0"
    return url


def is_youtube_url(url: str) -> bool:
    return "youtube.com" in url or "youtu.be" in url


def make_youtube_html(url: str) -> str:
    """Generate HTML page with embedded YouTube player."""
    embed_url = make_youtube_embed_url(url)
    return f"""<!DOCTYPE html>
<html>
<head>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: #0d1117; display: flex; justify-content: center;
          align-items: center; height: 100vh; }}
  iframe {{ width: 100%; max-width: 900px; height: 506px;
            border: none; border-radius: 8px; }}
</style>
</head>
<body>
  <iframe src="{embed_url}"
          allow="accelerometer; autoplay; clipboard-write;
                 encrypted-media; gyroscope; picture-in-picture"
          allowfullscreen>
  </iframe>
</body>
</html>"""


# ─────────────────────────────────────────────
#  SYSTEM INFO
# ─────────────────────────────────────────────

def get_system_info() -> dict:
    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "mac": get_mac_address(),
        "ip": get_local_ip(),
    }
