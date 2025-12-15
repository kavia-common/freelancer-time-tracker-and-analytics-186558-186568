import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from pydantic import TypeAdapter

from src.api.models import (
    Project,
    Task,
    Session,
    compute_session_fields,
)

DATA_DIR = Path("data")
PROJECTS_FILE = DATA_DIR / "projects.json"
TASKS_FILE = DATA_DIR / "tasks.json"
SESSIONS_FILE = DATA_DIR / "sessions.json"


def _ensure_files():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for f in (PROJECTS_FILE, TASKS_FILE, SESSIONS_FILE):
        if not f.exists():
            f.write_text("[]", encoding="utf-8")


def _read_json(path: Path):
    _ensure_files()
    raw = path.read_text(encoding="utf-8").strip() or "[]"
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # fallback to empty array on corruption
        return []


def _write_json(path: Path, obj):
    _ensure_files()
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, default=str, indent=2), encoding="utf-8")
    tmp.replace(path)


def list_projects() -> List[Project]:
    adapter = TypeAdapter(List[Project])
    return adapter.validate_python(_read_json(PROJECTS_FILE))


def save_projects(items: List[Project]):
    adapter = TypeAdapter(List[Project])
    payload = adapter.dump_python(items, by_alias=True)
    _write_json(PROJECTS_FILE, payload)


def list_tasks() -> List[Task]:
    adapter = TypeAdapter(List[Task])
    return adapter.validate_python(_read_json(TASKS_FILE))


def save_tasks(items: List[Task]):
    adapter = TypeAdapter(List[Task])
    payload = adapter.dump_python(items, by_alias=True)
    _write_json(TASKS_FILE, payload)


def list_sessions() -> List[Session]:
    adapter = TypeAdapter(List[Session])
    data = _read_json(SESSIONS_FILE)
    sessions = adapter.validate_python(_parse_dates_in_sessions(data))
    # compute derived fields using project rate fallback
    projects = {p.id: p for p in list_projects()}
    sessions_dicts = [s.model_dump() for s in sessions]
    enriched = [compute_session_fields(_coerce_dt(s), projects) for s in sessions_dicts]
    adapter_out = TypeAdapter(List[Session])
    return adapter_out.validate_python(enriched)


def save_sessions(items: List[Session]):
    adapter = TypeAdapter(List[Session])
    payload = adapter.dump_python(items, by_alias=True)
    _write_json(SESSIONS_FILE, payload)


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None


def _parse_dates_in_sessions(raw_list: List[dict]) -> List[dict]:
    out = []
    for s in raw_list:
        s = dict(s)
        s["start_time"] = _parse_dt(s.get("start_time")) or s.get("start_time")
        s["end_time"] = _parse_dt(s.get("end_time")) if s.get("end_time") else None
        s["created_at"] = _parse_dt(s.get("created_at")) or s.get("created_at")
        s["updated_at"] = _parse_dt(s.get("updated_at")) or s.get("updated_at")
        out.append(s)
    return out


def _coerce_dt(s: dict) -> dict:
    """Ensure datetime objects not serialized prematurely."""
    for k in ("start_time", "end_time", "created_at", "updated_at"):
        v = s.get(k)
        if isinstance(v, str):
            s[k] = _parse_dt(v) or v
    return s
