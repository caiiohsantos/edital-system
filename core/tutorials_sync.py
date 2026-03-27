# core/tutorials_sync.py
"""
Sincronizacao de tutoriais entre admin e clientes.

Fluxo:
  Admin edita tutorial -> salva no banco + escreve tutorials.json
  -> faz commit/push no GitHub
  -> Cliente baixa tutorials.json do GitHub ao abrir ou ao clicar Atualizar
"""
import json
import os
import urllib.request
from pathlib import Path
from datetime import datetime

# --- CONFIGURE AQUI ---------------------------------------------------
# URL raw do tutorials.json no seu repositorio GitHub
# Formato: https://raw.githubusercontent.com/caiiohsantos/edital-system/main/tutorials.json
GITHUB_TUTORIALS_URL = "https://raw.githubusercontent.com/caiiohsantos/edital-system/master/tutorials.json"

# URL raw do version.json (para auto-update)
GITHUB_VERSION_URL = "https://raw.githubusercontent.com/caiiohsantos/edital-system/master/version.json"
# ----------------------------------------------------------------------


def _get_local_path() -> Path:
    candidates = [
        Path(os.path.dirname(os.path.abspath(__file__))).parent / "tutorials.json",
        Path.home() / "AppData" / "Local" / "EditalSystem" / "tutorials.json",
        Path.home() / ".edital_system" / "tutorials.json",
    ]
    for p in candidates:
        if p.exists():
            return p
    return candidates[0]


def _get_cache_path() -> Path:
    if os.name == "nt":
        d = Path.home() / "AppData" / "Local" / "EditalSystem"
    else:
        d = Path.home() / ".edital_system"
    d.mkdir(parents=True, exist_ok=True)
    return d / "tutorials_cache.json"


def load_tutorials() -> dict:
    """
    Carrega tutoriais em ordem de prioridade:
    1. GitHub (online)
    2. Cache local (offline fallback)
    3. Arquivo local (desenvolvimento)
    """
    if GITHUB_TUTORIALS_URL:
        remote = _fetch_from_github()
        if remote is not None:
            _save_cache(remote)
            return remote
    cache = _load_cache()
    if cache:
        return cache
    return _load_local()


def _fetch_from_github():
    try:
        req = urllib.request.Request(
            GITHUB_TUTORIALS_URL,
            headers={"Cache-Control": "no-cache", "User-Agent": "EditalSystem/1.0"}
        )
        with urllib.request.urlopen(req, timeout=6) as r:
            data = json.loads(r.read().decode())
        return data.get("tutorials", {})
    except Exception:
        return None


def _load_cache() -> dict:
    try:
        p = _get_cache_path()
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("tutorials", {})
    except Exception:
        pass
    return {}


def _save_cache(tutorials: dict):
    try:
        p = _get_cache_path()
        with open(p, "w", encoding="utf-8") as f:
            json.dump({"tutorials": tutorials,
                       "cached_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
                      f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _load_local() -> dict:
    try:
        p = _get_local_path()
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("tutorials", {})
    except Exception:
        pass
    return {}


def save_tutorials(tutorials: dict) -> bool:
    p = _get_local_path()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "tutorials": tutorials,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": 1,
        }
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[tutorials_sync] Erro: {e}")
        return False


def get_tutorial_url(edital_id: str) -> str:
    return load_tutorials().get(edital_id, "")


def check_remote_version():
    if not GITHUB_VERSION_URL:
        return None
    try:
        from client.updater import APP_VERSION, _version_tuple
        req = urllib.request.Request(
            GITHUB_VERSION_URL,
            headers={"Cache-Control": "no-cache", "User-Agent": "EditalSystem/1.0"}
        )
        with urllib.request.urlopen(req, timeout=6) as r:
            data = json.loads(r.read().decode())
        remote = data.get("version", "0.0.0")
        if _version_tuple(remote) > _version_tuple(APP_VERSION):
            return data
    except Exception:
        pass
    return None
