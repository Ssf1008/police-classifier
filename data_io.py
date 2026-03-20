from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

import pandas as pd


@dataclass(frozen=True)
class IncidentRow:
    id: str
    text: str
    label: str


def load_incidents(input_path: str) -> List[IncidentRow]:
    p = Path(input_path)
    if not p.exists():
        raise FileNotFoundError(str(p))

    if p.suffix.lower() == ".csv":
        df = pd.read_csv(p)
        for col in ("id", "text", "label"):
            if col not in df.columns:
                raise ValueError(f"CSV missing required column: {col}")
        rows: List[IncidentRow] = []
        for _, r in df.iterrows():
            rows.append(
                IncidentRow(id=str(r["id"]), text=str(r["text"]), label=str(r["label"]))
            )
        return rows

    if p.suffix.lower() in (".jsonl", ".json"):
        rows = []
        if p.suffix.lower() == ".json":
            data = json.loads(p.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                raise ValueError("JSON must be a list of objects")
            iter_data = data
        else:
            iter_data = []
            with p.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    iter_data.append(json.loads(line))

        for obj in iter_data:
            for k in ("id", "text", "label"):
                if k not in obj:
                    raise ValueError(f"{p.suffix} missing required field: {k}")
            rows.append(
                IncidentRow(id=str(obj["id"]), text=str(obj["text"]), label=str(obj["label"]))
            )
        return rows

    raise ValueError("Unsupported input format. Use .csv, .jsonl or .json")

