# core/custom_editals.py
import json, os
from pathlib import Path

CATEGORIES = ["Prioridade 1","Prioridade 2","Prioridade 3","Prioridade 4","Prefeituras"]


def _path() -> Path:
    candidates = [
        Path(os.path.dirname(os.path.abspath(__file__))).parent / "custom_editals.json",
        Path(__file__).parent.parent / "custom_editals.json",
    ]
    for p in candidates:
        if p.exists(): return p
    return candidates[0]


def load_custom_editals() -> dict:
    try:
        p = _path()
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception: pass
    return {}


def save_custom_editals(data: dict) -> bool:
    try:
        p = _path(); p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except Exception as e:
        print(f"[custom_editals] {e}"); return False


def get_all_editals_merged() -> dict:
    from core.editals_data import EDITALS_DATA
    import copy
    merged = copy.deepcopy(EDITALS_DATA)
    custom = load_custom_editals()
    for cat, editals in custom.items():
        merged.setdefault(cat, []).extend(editals)
    return merged


def add_edital(category, edital) -> bool:
    data = load_custom_editals()
    data.setdefault(category, [])
    data[category] = [e for e in data[category] if e.get("id") != edital.get("id")]
    data[category].append(edital)
    return save_custom_editals(data)


def update_edital(category, edital_id, edital) -> bool:
    data = load_custom_editals()
    if category not in data: return False
    for i,e in enumerate(data[category]):
        if e.get("id") == edital_id:
            data[category][i] = edital
            return save_custom_editals(data)
    return False


def delete_edital(category, edital_id) -> bool:
    data = load_custom_editals()
    if category not in data: return False
    n0 = len(data[category])
    data[category] = [e for e in data[category] if e.get("id") != edital_id]
    return save_custom_editals(data) if len(data[category]) < n0 else False


def make_edital_id(nome: str) -> str:
    import re, unicodedata
    name = unicodedata.normalize("NFD", nome.lower())
    name = "".join(c for c in name if unicodedata.category(c) != "Mn")
    name = re.sub(r"[^a-z0-9]+","_", name).strip("_")
    return f"custom_{name}"
