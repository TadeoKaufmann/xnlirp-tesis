"""
Recupera el estado de validación cruzando generated.jsonl con generated_v3.jsonl,
sin necesidad de volver a correr Haiku.

Lógica:
  - Grupos en generated_v3.jsonl → ya procesados (clean original o regenerado OK)
  - Grupos en generated.jsonl pero NO en generated_v3.jsonl → necesitan regeneración

Produce:
  - generated_v3.jsonl: merged con TODOS los grupos (buenos + pendientes de regen)
  - validation_haiku.jsonl: sintético con answer_unit_idx para que _regen_questions.py funcione

Uso:
  python qa/scripts/_recover_validation.py --round round_003
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ROUNDS_DIR = REPO_ROOT / "qa" / "rounds"


def load_groups(path: Path) -> dict[tuple, list[dict]]:
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    groups: dict[tuple, list[dict]] = {}
    for r in rows:
        key = (r["story"], r["answer_unit_idx"])
        groups.setdefault(key, []).append(r)
    return groups


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--round", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    round_dir = ROUNDS_DIR / args.round
    v3_path = round_dir / "generated_v3.jsonl"
    orig_path = round_dir / "generated.jsonl"
    val_path = round_dir / "validation_haiku.jsonl"

    if not orig_path.exists():
        raise SystemExit(f"No encontré {orig_path}")
    if not v3_path.exists():
        raise SystemExit(f"No encontré {v3_path} — no hay nada que recuperar")

    orig_groups = load_groups(orig_path)
    v3_groups = load_groups(v3_path)

    v3_keys = set(v3_groups.keys())
    orig_keys = set(orig_groups.keys())
    missing_keys = orig_keys - v3_keys

    print(f"[{args.round}]")
    print(f"  generated.jsonl:    {len(orig_keys)} grupos")
    print(f"  generated_v3.jsonl: {len(v3_keys)} grupos (ya procesados)")
    print(f"  a regenerar:        {len(missing_keys)} grupos")

    if args.dry_run:
        by_story: dict[str, int] = {}
        for story, _ in missing_keys:
            by_story[story] = by_story.get(story, 0) + 1
        for story, cnt in sorted(by_story.items(), key=lambda x: -x[1]):
            print(f"    {cnt:4d}  {story}")
        return

    # Construir validation_haiku.jsonl sintético
    val_rows = []
    for key in v3_keys:
        rows = v3_groups[key]
        pos = next((r for r in rows if r["label"] == 1), None)
        val_rows.append({
            "story": key[0],
            "answer_unit_idx": key[1],
            "question": pos["question"] if pos else "",
            "question_type": pos.get("question_type", "factual") if pos else "factual",
            "split": pos.get("split", "") if pos else "",
            "issue": "clean",
            "model": "recovered",
        })
    for key in missing_keys:
        rows = orig_groups[key]
        pos = next((r for r in rows if r["label"] == 1), None)
        val_rows.append({
            "story": key[0],
            "answer_unit_idx": key[1],
            "question": pos["question"] if pos else "",
            "question_type": pos.get("question_type", "factual") if pos else "factual",
            "split": pos.get("split", "") if pos else "",
            "issue": "wrong",
            "model": "recovered",
        })

    with val_path.open("w", encoding="utf-8") as f:
        for r in val_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"[out] validation_haiku.jsonl → {len(val_rows)} rows ({len(v3_keys)} clean, {len(missing_keys)} non-clean)")

    # Construir generated_v3.jsonl merged: v3 + faltantes de orig
    merged_rows: list[dict] = []
    for rows in v3_groups.values():
        merged_rows.extend(rows)
    for key in missing_keys:
        merged_rows.extend(orig_groups[key])

    with v3_path.open("w", encoding="utf-8") as f:
        for r in merged_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    total_groups = len(v3_keys) + len(missing_keys)
    print(f"[out] generated_v3.jsonl → {len(merged_rows)} instancias ({total_groups} grupos)")
    print()
    print("Próximos pasos:")
    print(f"  python qa/scripts/_regen_questions.py --round {args.round}")
    print(f"  python qa/scripts/validate_consistency.py --round {args.round} --model haiku --batch")


if __name__ == "__main__":
    main()
