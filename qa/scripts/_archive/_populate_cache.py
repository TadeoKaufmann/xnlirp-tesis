"""
Pre-popula _qa_questions_raw.jsonl con preguntas ya generadas en rounds anteriores.
Evita re-generar oraciones ya procesadas en futuros runs.

Uso:
  python qa/scripts/_populate_cache.py
"""
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CACHE_PATH = REPO_ROOT / "qa" / "data" / "_qa_questions_raw.jsonl"
ROUNDS_DIR = REPO_ROOT / "qa" / "rounds"

SOURCES = [
    ROUNDS_DIR / "round_001" / "qa_stories_dataset.jsonl",
    ROUNDS_DIR / "round_002" / "generated.jsonl",
]

existing = set()
if CACHE_PATH.exists():
    for line in CACHE_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            existing.add((r["story"], int(r["unit_idx"])))
print(f"[cache] {len(existing)} entradas existentes")

new_rows = []
for src in SOURCES:
    if not src.exists():
        print(f"[skip] no existe: {src}")
        continue
    rows = [json.loads(l) for l in src.read_text(encoding="utf-8").splitlines() if l.strip()]
    # Solo tomar los positivos (label=1) para extraer la pregunta
    positives = [r for r in rows if r.get("label", 1) == 1]
    for r in positives:
        key = (r["story"], int(r.get("unit_idx", r.get("answer_unit_idx", -1))))
        if key in existing:
            continue
        new_rows.append({
            "story": r["story"],
            "unit_idx": key[1],
            "unit": r["unit"],
            "question": r.get("question", ""),
            "question_type": r.get("question_type", "factual"),
            "skip_reason": None,
        })
        existing.add(key)

if new_rows:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CACHE_PATH.open("a", encoding="utf-8") as f:
        for r in new_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"[cache] +{len(new_rows)} entradas nuevas → total {len(existing)}")
else:
    print("[cache] nada nuevo para agregar")
