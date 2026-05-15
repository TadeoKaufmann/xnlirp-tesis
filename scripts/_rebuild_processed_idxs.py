"""Reconstruye data/processed/processed_idxs.json desde los jsonl fuente.

Uso: ejecutar después de cada batch nuevo que se quiera marcar como procesado.

Lee:
  - data/processed/cultural_adaptations.jsonl
  - data/processed/xnli_combined_dev_200.jsonl
  - cualquier otro jsonl listado en `processed_idxs.json` sin la flag `pending=true`

Escribe el conjunto unión a processed_idxs.json + un campo `idxs_set` con la lista
plana ordenada (útil para usar desde otros scripts).
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX_FILE = ROOT / "data" / "processed" / "processed_idxs.json"


def load_jsonl_idxs(path: Path) -> set[int]:
    if not path.exists():
        return set()
    idxs = set()
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            idx = row.get("idx")
            if isinstance(idx, int) and idx < 99000:
                idxs.add(idx)
    return idxs


def main():
    index = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    union = set()
    for name, src in index.get("sources", {}).items():
        if src.get("pending"):
            continue
        path = ROOT / src["file"]
        idxs = load_jsonl_idxs(path)
        src["count"] = len(idxs)
        union |= idxs

    index["_last_updated"] = date.today().isoformat()
    index["_total"] = len(union)
    index["idxs_set"] = sorted(union)
    INDEX_FILE.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Reconstruido: {len(union)} idxs únicos procesados.")


if __name__ == "__main__":
    main()
