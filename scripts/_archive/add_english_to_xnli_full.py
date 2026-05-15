"""
Descarga XNLI EN (test + validation) y agrega prem_en / hyp_en
a data/raw/xnli/xnli_full_7500.jsonl, que solo tenía campos ES.
"""
import json
from pathlib import Path
from datasets import load_dataset

INPUT  = Path("data/raw/xnli/xnli_full_7500.jsonl")
OUTPUT = Path("data/raw/xnli/xnli_full_7500.jsonl")  # sobreescribir in-place

# 1. Cargar el ES ya descargado
print("Cargando ES existente...")
rows = []
with open(INPUT, encoding="utf-8") as f:
    for line in f:
        rows.append(json.loads(line))
print(f"  {len(rows):,} filas cargadas")

# 2. Construir lookup EN por (split, idx)
print("Descargando EN...")
en_lookup = {}
for split in ["test", "validation"]:
    ds = load_dataset("xnli", "en", split=split)
    print(f"  {split}: {len(ds):,} ejemplos")
    for pos, row in enumerate(ds):
        idx = row.get("idx", pos)
        en_lookup[(split, idx)] = {
            "prem_en": row["premise"],
            "hyp_en":  row["hypothesis"],
        }

print(f"  Total EN en lookup: {len(en_lookup):,}")

# 3. Mergear
matched = 0
for row in rows:
    key = (row["split"], row["idx"])
    en = en_lookup.get(key)
    if en:
        row["prem_en"] = en["prem_en"]
        row["hyp_en"]  = en["hyp_en"]
        matched += 1
    else:
        row["prem_en"] = ""
        row["hyp_en"]  = ""

print(f"\nMerge: {matched:,}/{len(rows):,} filas con EN ({matched/len(rows)*100:.1f}%)")

# 4. Guardar
with open(OUTPUT, "w", encoding="utf-8") as f:
    for row in rows:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

print(f"Guardado: {OUTPUT}")
print("Ejemplo fila 0:")
print(json.dumps(rows[0], ensure_ascii=False, indent=2)[:400])
