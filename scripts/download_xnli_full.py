"""
Descarga el XNLI ES completo (test + validation = 7,500 ejemplos) y lo guarda
en data/raw/xnli/xnli_full_7500.jsonl con la misma estructura que pilot_500.
"""
import json
from pathlib import Path
from collections import Counter
from datasets import load_dataset

OUTPUT = Path("data/raw/xnli/xnli_full_7500.jsonl")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

LABEL_MAP = {0: "entailment", 1: "neutral", 2: "contradiction"}

rows = []
for split in ["test", "validation"]:
    print(f"Descargando split '{split}'...")
    ds = load_dataset("xnli", "es", split=split)
    print(f"  {len(ds)} ejemplos")
    for pos, row in enumerate(ds):
        rows.append({
            "idx":       row.get("idx", pos),
            "split":     split,
            "label":     LABEL_MAP[row["label"]],
            "label_int": row["label"],
            "prem_es":   row["premise"],
            "hyp_es":    row["hypothesis"],
        })

print(f"\nTotal: {len(rows)} ejemplos")
print(f"Distribución: {Counter(r['label'] for r in rows)}")

with open(OUTPUT, "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

print(f"Guardado: {OUTPUT}")
