# core/license_core.py
"""
License system using HMAC-signed JSON files.
Admin generates .lic files → distributes to users → client validates.
"""
import hmac
import hashlib
import json
import base64
import os
from datetime import datetime
from pathlib import Path

# ⚠️ In production: obfuscate this key or load from a secure source
_SECRET = b"EditalSystem_2026_SecureKey_F3l1p3_v1"


def _sign(data: dict) -> str:
    """Create HMAC-SHA256 signature for a dict."""
    payload = json.dumps(data, sort_keys=True).encode()
    return hmac.new(_SECRET, payload, hashlib.sha256).hexdigest()


def generate_license_file(serial: str, user_name: str, valid_until: str,
                           mac_hash: str = "") -> bytes:
    """
    Generate an encrypted license file content (bytes).
    Admin uses this to create .lic files for users.
    """
    data = {
        "serial": serial,
        "user_name": user_name,
        "valid_until": valid_until,
        "mac_hash": mac_hash,
        "issued_at": datetime.now().strftime("%Y-%m-%d"),
    }
    data["signature"] = _sign({k: v for k, v in data.items()})
    json_bytes = json.dumps(data).encode()
    return base64.b64encode(json_bytes)


def parse_license_file(content: bytes) -> dict:
    """
    Parse and validate a license file.
    Returns dict with license data, or raises ValueError.
    """
    try:
        json_bytes = base64.b64decode(content)
        data = json.loads(json_bytes)
    except Exception:
        raise ValueError("Arquivo de licença inválido ou corrompido.")

    # Verify signature
    sig = data.pop("signature", "")
    expected = _sign(data)
    if not hmac.compare_digest(sig, expected):
        raise ValueError("Assinatura da licença inválida. Arquivo pode ter sido alterado.")
    data["signature"] = sig
    return data


def validate_license_data(data: dict, mac_hash: str) -> tuple[bool, str]:
    """
    Validate license data against current machine.
    Returns (is_valid, message).
    """
    # Check expiry
    try:
        exp = datetime.strptime(data["valid_until"], "%Y-%m-%d")
        if exp < datetime.now():
            return False, f"Licença expirada em {data['valid_until']}."
    except Exception:
        return False, "Data de validade inválida."

    # Check MAC binding (only if MAC was set)
    stored_mac = data.get("mac_hash", "")
    if stored_mac and stored_mac != mac_hash:
        return False, (
            "Esta licença está vinculada a outro dispositivo.\n"
            "Entre em contato com o administrador para reativação."
        )

    days_left = (exp - datetime.now()).days
    return True, f"Licença válida por mais {days_left} dias."


def find_license_file() -> Path | None:
    """Search common locations for a .lic file."""
    search_dirs = [
        Path.cwd(),
        Path.home() / "AppData" / "Local" / "EditalSystem",
        Path.home() / ".edital_system",
        Path(__file__).parent.parent / "client",
    ]
    for d in search_dirs:
        if d.exists():
            for f in d.glob("*.lic"):
                return f
    return None


def load_license_from_file(path: str | Path) -> dict:
    """Load and parse a .lic file."""
    with open(path, "rb") as f:
        content = f.read()
    return parse_license_file(content)


def save_license_file(content: bytes, directory: str | Path, filename: str = "license.lic"):
    """Save license file bytes to directory."""
    path = Path(directory) / filename
    with open(path, "wb") as f:
        f.write(content)
    return str(path)
