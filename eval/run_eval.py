"""
Measure field-level extraction against gold labels (JSON fixtures).

Usage (API must be running, e.g. uvicorn main:app --reload):
  set API_BASE_URL=http://localhost:8000
  python eval/run_eval.py

Reports exact-match rate on (field_name, normalized field_value) pairs you label.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import requests

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
API = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


def _norm(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[\s,$]+", "", s)
    return s


def _fields_to_map(fields: list) -> dict[str, str]:
    out: dict[str, str] = {}
    for f in fields:
        name = (f.get("field_name") or "").strip()
        val = str(f.get("field_value") or "").strip()
        if name:
            out[name] = val
    return out


def score_one(transcript: str, gold: dict[str, str]) -> tuple[int, int, list[str]]:
    r = requests.post(
        f"{API}/extract-fields",
        json={"transcript": transcript},
        timeout=120,
    )
    r.raise_for_status()
    body = r.json()
    fields = body.get("response", {}).get("fields") or []
    pred = _fields_to_map(fields)
    notes: list[str] = []
    matched = 0
    total = 0
    for name, gold_val in gold.items():
        total += 1
        pv = pred.get(name)
        if pv is None:
            notes.append(f"missing: {name}")
            continue
        if _norm(pv) == _norm(gold_val):
            matched += 1
        else:
            notes.append(f"mismatch {name!r}: pred={pv!r} gold={gold_val!r}")
    return matched, total, notes


def main() -> int:
    files = sorted(FIXTURES_DIR.glob("*.json"))
    if not files:
        print("No fixtures in eval/fixtures/*.json — add labeled examples.", file=sys.stderr)
        return 1

    all_m, all_t = 0, 0
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        tid = data.get("id", path.stem)
        tr = data.get("transcript", "")
        gold = data.get("gold_fields") or {}
        if not tr or not gold:
            print(f"skip {tid}: need transcript + gold_fields", file=sys.stderr)
            continue
        m, t, notes = score_one(tr, gold)
        all_m += m
        all_t += t
        pct = 100.0 * m / t if t else 0.0
        print(f"{tid}: {m}/{t} exact ({pct:.1f}%)")
        for n in notes[:8]:
            print(f"  - {n}")
        if len(notes) > 8:
            print(f"  ... +{len(notes) - 8} more")

    if all_t == 0:
        return 1
    overall = 100.0 * all_m / all_t
    print(f"\nOverall (micro-average over gold keys): {all_m}/{all_t} = {overall:.1f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
