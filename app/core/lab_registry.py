"""Lab registry loading."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LabDefinition:
    id: str
    name: str
    path: str
    role: str
    default_symbol: str
    default_timeframe: str


def load_lab_registry(path: Path) -> list[LabDefinition]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [LabDefinition(**item) for item in payload.get("labs", [])]
