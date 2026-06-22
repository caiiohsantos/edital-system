# core/license_core.py
import hmac, hashlib, json, base64
from datetime import datetime
from pathlib import Path

_SECRET = b"EditalSystem_2026_SecureKey_F3l1p3_v1"


def _sign(data: dict) -> str:
    payload = json.dumps(data, sort_keys=True).encode()
    return hmac.new(_SECRET, payload, hashlib.sha256).hexdigest()


def generate_license_file(serial, user_name, valid_until, mac_hash=""):
    data = {"serial":serial,"user_name":user_name,"valid_until":valid_until,
            "mac_hash":mac_hash,"issued_at":datetime.now().strftime("%Y-%m-%d")}
    data["signature"] = _sign(dict(data))
    return base64.b64encode(json.dumps(data).encode())


def parse_license_file(content: bytes) -> dict:
    try:
        data = json.loads(base64.b64decode(content))
    except Exception:
        raise ValueError("Arquivo de licença inválido ou corrompido.")
    sig = data.pop("signature","")
    if not hmac.compare_digest(sig, _sign(data)):
        raise ValueError("Assinatura inválida. Arquivo pode ter sido alterado.")
    data["signature"] = sig
    return data


def validate_license_data(data: dict, mac_hash: str):
    try:
        exp = datetime.strptime(data["valid_until"], "%Y-%m-%d")
        if exp < datetime.now():
            return False, f"Licença expirada em {data['valid_until']}."
    except Exception:
        return False, "Data de validade inválida."
    stored_mac = data.get("mac_hash","")
    if stored_mac and stored_mac != mac_hash:
        return False, "Licença vinculada a outro dispositivo.\nContate o administrador."
    days_left = (exp - datetime.now()).days
    return True, f"Válida por mais {days_left} dias."


def find_license_file():
    dirs = [Path.cwd(), Path.home()/"AppData/Local/EditalSystem",
            Path.home()/".edital_system", Path(__file__).parent.parent/"client"]
    for d in dirs:
        if d.exists():
            for f in d.glob("*.lic"):
                return f
    return None


def load_license_from_file(path):
    with open(path,"rb") as f:
        return parse_license_file(f.read())
