"""
Samplea 1,000 instancias nuevas de XNLI ES (test set), estratificadas por label,
excluyendo las 500 del pilot. Guarda en data/raw/xnli/xnli_next_1000.jsonl.
"""
import json
import random
from collections import defaultdict
from datasets import load_dataset

PILOT_PATH = "data/raw/xnli/xnli_pilot_500.jsonl"
OUTPUT_PATH = "data/raw/xnli/xnli_next_1000.jsonl"
N = 1000
SEED = 42

# Cargar idx ya usados
pilot_idxs = set()
with open(PILOT_PATH, encoding="utf-8") as f:
    for line in f:
        pilot_idxs.add(json.loads(line)["idx"])
print(f"Pilot idxs a excluir: {len(pilot_idxs)}")

# Descargar XNLI ES test set
print("Descargando XNLI ES...")
ds = load_dataset("xnli", "es", split="test")
print(f"Total test set: {len(ds)}")

LABEL_MAP = {0: "entailment", 1: "neutral", 2: "contradiction"}

# Agrupar candidatos por label (excluyendo pilot, usando posición como idx)
buckets = defaultdict(list)
for pos, row in enumerate(ds):
    if pos not in pilot_idxs:
        buckets[row["label"]].append((pos, row))

for lbl, rows in buckets.items():
    print(f"  Disponibles label {LABEL_MAP[lbl]}: {len(rows)}")

# Samplear N/3 por label (estratificado)
per_label = N // 3
random.seed(SEED)
sampled = []
for lbl in [0, 1, 2]:
    sampled.extend(random.sample(buckets[lbl], per_label))

# Completar si N no es divisible por 3
remaining = N - len(sampled)
if remaining:
    used = {pos for pos, _ in sampled}
    extras = [(pos, r) for lbl in [0, 1, 2] for pos, r in buckets[lbl] if pos not in used]
    sampled.extend(random.sample(extras, remaining))

random.shuffle(sampled)

# Escribir JSONL con la misma estructura que pilot_500
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    for pos, row in sampled:
        f.write(json.dumps({
            "idx":       pos,
            "label":     LABEL_MAP[row["label"]],
            "label_int": row["label"],
            "prem_es":   row["premise"],
            "hyp_es":    row["hypothesis"],
        }, ensure_ascii=False) + "\n")

from collections import Counter
labels = [LABEL_MAP[r["label"]] for _, r in sampled]
print(f"\nGuardado: {OUTPUT_PATH}")
print(f"Total: {len(sampled)}")
print(f"Distribución: {Counter(labels)}")
