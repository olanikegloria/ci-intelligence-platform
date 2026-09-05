"""In-memory / JSON-file store for CI runs and derived signals."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .models import WorkflowRun

_DEFAULT_DATA = Path(__file__).resolve().parents[2] / "data"


def _data_dir() -> Path:
    return Path(os.environ.get("DATA_DIR", _DEFAULT_DATA))


def _store_path() -> Path:
    return _data_dir() / "store.json"


class Store:
    def __init__(self) -> None:
        self.runs: dict[str, WorkflowRun] = {}
        _data_dir().mkdir(parents=True, exist_ok=True)

    def clear(self) -> None:
        self.runs.clear()
        self._persist()

    def upsert_run(self, run: WorkflowRun) -> WorkflowRun:
        self.runs[run.id] = run
        self._persist()
        return run

    def list_runs(self) -> list[WorkflowRun]:
        return sorted(self.runs.values(), key=lambda r: r.created_at, reverse=True)

    def get_run(self, run_id: str) -> WorkflowRun | None:
        return self.runs.get(run_id)

    def load(self) -> None:
        path = _store_path()
        if not path.exists():
            return
        raw = json.loads(path.read_text())
        for item in raw.get("runs", []):
            run = WorkflowRun.model_validate(item)
            self.runs[run.id] = run

    def _persist(self) -> None:
        _data_dir().mkdir(parents=True, exist_ok=True)
        payload: dict[str, Any] = {
            "runs": [r.model_dump() for r in self.list_runs()],
        }
        _store_path().write_text(json.dumps(payload, indent=2))


store = Store()
