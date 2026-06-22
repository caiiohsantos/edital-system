# core/tutorials_sync.py
import json, os, urllib.request
from pathlib import Path
from datetime import datetime

GITHUB_TUTORIALS_URL = "https://raw.githubusercontent.com/caiiohsantos/edital-system/master/tutorials.json"
GITHUB_VERSION_URL   = "https://raw.githubusercontent.com/caiiohsantos/edital-system/master/version.json"


def _local_path() -> Path:
    candidates = [
        Path(os.path.dirname(os.path.abspath(__file__))).parent / "tutorials.json",
        Path(__file__).parent.parent / "tutorials.json",
    ]
    for p in candidates:
        if p.exists(): return p
    return candidates[0]


def _cache_path() -> Path:
    d = Path.home() / ("AppData/Local/EditalSystem" if os.name=="nt" else ".edital_system")
    d.mkdir(parents=True, exist_ok=True)
    return d / "tutorials_cache.json"


def load_tutorials() -> dict:
    if GITHUB_TUTORIALS_URL:
        remote = _fetch_github()
        if remote is not None:
            _save_cache(remote); return remote
    cache = _load_cache()
    if cache: return cache
    return _load_local()


def _fetch_github():
    try:
        req = urllib.request.Request(GITHUB_TUTORIALS_URL,
            headers={"Cache-Control":"no-cache","User-Agent":"EditalSystem/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.loads(r.read().decode()).get("tutorials", {})
    except Exception:
        return None


def _load_cache() -> dict:
    try:
        p = _cache_path()
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8")).get("tutorials", {})
    except Exception: pass
    return {}


def _save_cache(tutorials: dict):
    try:
        _cache_path().write_text(json.dumps(
            {"tutorials":tutorials,"cached_at":datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
            ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception: pass


def _load_local() -> dict:
    try:
        p = _local_path()
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8")).get("tutorials", {})
    except Exception: pass
    return {}


def save_tutorials(tutorials: dict) -> bool:
    p = _local_path()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"tutorials":tutorials,
            "updated_at":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"version":1},
            ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except Exception as e:
        print(f"[tutorials_sync] {e}"); return False
