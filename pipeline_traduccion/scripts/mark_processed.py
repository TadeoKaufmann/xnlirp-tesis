"""
mark_processed.py — Registra idx de uno o más JSONLs en el set global de procesados.

Uso:
    python pipeline_traduccion/scripts/mark_processed.py \
        validation_app/to_upload/batch_500_ok.jsonl \
        pipeline_evaluacion/error_cases/to_fix_batch_500.jsonl

Después de correr esto, translate_xnli.py --batch-mode saltea esos idx automáticamente.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from translate_xnli import mark_processed

paths = [Path(p) for p in sys.argv[1:]]
if not paths:
    print("Uso: mark_processed.py <jsonl1> [jsonl2 ...]")
    sys.exit(1)

total = mark_processed(paths)
print(f"processed_idx_set.json actualizado: {total} idx en total")
for p in paths:
    print(f"  {p}")
