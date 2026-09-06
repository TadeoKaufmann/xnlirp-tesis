"""
build_dataset_final.py — Merge combined + to_fix con provenance labels.

Fuentes:
  - combined_6884_full.jsonl  → grader_verdict "ok"  (6760 rows)
  - to_fix_corrected.jsonl    → grader_verdict propio (2850 rows, 2115 solapan con combined)
  → 7495 instancias únicas (combined gana en solapamientos)

Provenance fields añadidos:
  row["provenance"] = {
    "grader_verdict": "ok" | "<valor original>",
    "corrections":    ["ppc", "manual"],   # solo tipos detectables
    "quality_scores": [{"model": "claude-sonnet-4-6", "score": N}],
    "human_validation": {"n_raters": N, "avg_score": F, "palabras_marcadas": [...]} | null
  }
  row["is_cultural"] = bool   (type == "E")
  row["in_dev_set"]  = bool   (idx en xnli_combined_dev_200.jsonl)
"""

import json, csv, sys
from pathlib import Path
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT     = Path(".")
COMBINED = ROOT / "validation_app/to_upload/combined_6884_full.jsonl"
TO_FIX   = ROOT / "pipeline_evaluacion/error_cases/to_fix_corrected.jsonl"
PPC_CORR = ROOT / "pipeline_evaluacion/error_cases/scoring_output/ppc_corrections.jsonl"
SCORES1  = ROOT / "pipeline_evaluacion/error_cases/scoring_output/rescore_input_claude_scores.jsonl"
SCORES2  = ROOT / "pipeline_evaluacion/error_cases/scoring_output/rescore2_input_claude_scores.jsonl"
APP_CSV  = ROOT / "pipeline_evaluacion/respuestas_anotadores/Validación_App.csv"
DEV_200  = ROOT / "data/dev/xnli_combined_dev_200.jsonl"
RAW_XNLI  = ROOT / "data/raw/xnli/xnli_full_7500.jsonl"
MISSING   = ROOT / "pipeline_evaluacion/error_cases/missing_129_translated.jsonl"
OUT       = ROOT / "data/processed/dataset_final.jsonl"

# ── Correcciones manuales (gradeadas en chat, 2026-06-05) ────────────────────
MANUAL_IDX    = {523, 5240, 6872, 3766, 555, 556, 598, 754, 2494}
MANUAL_SCORES = {523: 3, 5240: 4, 6872: 3, 3766: 3, 555: 4, 556: 4, 598: 3, 754: 3, 2494: 4}

LABEL_MAP = {"entailment": 0, "neutral": 1, "contradiction": 2}

# ── Helpers ──────────────────────────────────────────────────────────────────
def load_jsonl(p, enc="utf-8"):
    return [json.loads(l) for l in Path(p).read_text(encoding=enc).splitlines() if l.strip()]

# ── PPC: idx con corrección real (excluye mantener) ──────────────────────────
ppc_rows = load_jsonl(PPC_CORR)
ppc_idx  = {r["idx"] for r in ppc_rows if "prem_rp" in r or "hyp_rp" in r}
print(f"PPC corrections tracked: {len(ppc_idx)} idx")

# ── Sonnet quality scores ─────────────────────────────────────────────────────
sonnet_scores: dict[int, int] = {}
for f in [SCORES1, SCORES2]:
    if Path(f).exists():
        for r in load_jsonl(f):
            sonnet_scores[r["idx"]] = r["score"]
for idx, score in MANUAL_SCORES.items():
    sonnet_scores[idx] = score
print(f"Sonnet scores available: {len(sonnet_scores)} idx")

# ── Human validation from app ─────────────────────────────────────────────────
human_val: dict[int, list] = defaultdict(list)
with open(APP_CSV, encoding="utf-8-sig", errors="replace") as f:
    for row in csv.DictReader(f):
        try:
            idx   = int(row["idx"])
            score = int(row["respuesta"]) if row.get("respuesta", "").strip() else None
        except (ValueError, KeyError):
            continue
        palabras = [p.strip() for p in row.get("palabras_marcadas", "").split(",") if p.strip()]
        if score is not None:
            human_val[idx].append({"score": score, "palabras": palabras})
print(f"Human validation: {len(human_val)} unique idx from app")

def make_human_validation(idx: int):
    entries = human_val.get(idx)
    if not entries:
        return None
    scores   = [e["score"] for e in entries]
    palabras = sorted(set(p for e in entries for p in e["palabras"]))
    return {
        "n_raters":        len(scores),
        "avg_score":       round(sum(scores) / len(scores), 2),
        "palabras_marcadas": palabras,
    }

# ── Dev-200 idx ───────────────────────────────────────────────────────────────
dev_idx = {json.loads(l)["idx"] for l in DEV_200.read_text(encoding="utf-8").splitlines() if l.strip()}
print(f"Dev-200 idx: {len(dev_idx)}")

# ── Raw XNLI lookup (para filas de to_fix con schema incompleto) ─────────────
# El raw usa idx 0-based por split. Pipeline reindexa validación: raw_idx + 5010.
raw_test: dict[int, dict] = {}
raw_val:  dict[int, dict] = {}
if RAW_XNLI.exists():
    for line in RAW_XNLI.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("split") == "validation":
            raw_val[r["idx"]] = r
        else:
            raw_test[r["idx"]] = r

def get_raw(pipeline_idx: int) -> dict | None:
    if pipeline_idx < 5010:
        return raw_test.get(pipeline_idx)
    return raw_val.get(pipeline_idx - 5010)

print(f"Raw XNLI loaded: {len(raw_test)} test + {len(raw_val)} validation")

# ── Traducciones de las 129 instancias faltantes ──────────────────────────────
missing_translated = {}
if MISSING.exists():
    for line in MISSING.read_text(encoding="utf-8").splitlines():
        if not line.strip(): continue
        r = json.loads(line)
        missing_translated[r["idx"]] = r
print(f"Missing translations loaded: {len(missing_translated)} instancias")

REQUIRED_FIELDS = {"label", "prem_es", "hyp_es", "prem_rp", "hyp_rp"}
STRIP_FIELDS   = {"verdict", "confidence", "issues", "vs_gold", "gold_divergence_type"}

def complete_row(row: dict) -> dict | None:
    idx = row.get("idx")
    raw = get_raw(idx)
    if raw is None:
        return None
    # Merge: raw como base, row sobreescribe (excepto campos internos del grader y None)
    merged = {**raw, **{k: v for k, v in row.items() if v is not None and k not in STRIP_FIELDS}}
    # Si no hay prem_rp: usar traducción del archivo missing_129
    if "prem_rp" not in merged or not merged["prem_rp"]:
        translated = missing_translated.get(idx)
        if translated:
            merged.update({k: translated[k] for k in ("prem_rp","hyp_rp","type","changes","lev_prem","lev_hyp","lev_total") if k in translated})
        else:
            return None  # sin traducción disponible, descartar
    if not REQUIRED_FIELDS.issubset(merged):
        return None
    return merged

# ── Provenance builder ────────────────────────────────────────────────────────
def build_provenance(idx: int, grader_verdict: str, missing_rp: bool = False) -> dict:
    corrections = []
    if idx in ppc_idx:
        corrections.append("ppc")
    if idx in MANUAL_IDX:
        corrections.append("manual")

    quality_scores = []
    if idx in sonnet_scores:
        quality_scores.append({"model": "claude-sonnet-4-6", "score": sonnet_scores[idx]})

    prov = {
        "grader_verdict":    grader_verdict,
        "corrections":       corrections,
        "quality_scores":    quality_scores,
        "human_validation":  make_human_validation(idx),
    }
    if missing_rp:
        prov["translation_status"] = "missing_rp"
    return prov

# ── Merge ─────────────────────────────────────────────────────────────────────
combined_rows = load_jsonl(COMBINED)
tofix_rows    = load_jsonl(TO_FIX, enc="utf-8-sig")

combined_idx_set = {r["idx"] for r in combined_rows}
overlap_count    = sum(1 for r in tofix_rows if r["idx"] in combined_idx_set)
print(f"\ncombined: {len(combined_rows)} rows")
print(f"to_fix:   {len(tofix_rows)} rows ({overlap_count} solapan con combined, se descartan)")

output: list[dict] = []
seen:   set[int]   = set()

# 1. Combined (grader OK) — fuente autoritativa
for row in combined_rows:
    idx = row["idx"]
    if "label_int" not in row:
        row["label_int"] = LABEL_MAP.get(row.get("label", ""), -1)
    row["provenance"]  = build_provenance(idx, "ok")
    row["is_cultural"] = row.get("type") == "E"
    row["in_dev_set"]  = idx in dev_idx
    output.append(row)
    seen.add(idx)

# 2. To_fix (solo los no solapados)
internal_fields = {"grader_issues", "grader_note", "source", "prem_rp_canonical",
                   "verdict", "confidence", "issues", "vs_gold", "gold_divergence_type"}
skipped = 0
for row in tofix_rows:
    idx = row["idx"]
    if idx in seen:
        continue
    row = complete_row(row)
    if row is None:
        skipped += 1
        continue
    grader_verdict = row.pop("grader_verdict", "to_fix")
    for field in internal_fields:
        row.pop(field, None)
    if "label_int" not in row:
        row["label_int"] = LABEL_MAP.get(row.get("label", ""), -1)
    missing_rp = row.pop("_missing_rp", False)
    row["provenance"]  = build_provenance(idx, grader_verdict, missing_rp=missing_rp)
    row["is_cultural"] = row.get("type") == "E"
    row["in_dev_set"]  = idx in dev_idx
    output.append(row)
    seen.add(idx)

if skipped:
    print(f"  ⚠ to_fix rows skipped (sin datos recuperables): {skipped}")

# 3. Instancias nunca procesadas en ningún archivo → usar missing_129_translated
from_missing = 0
for pipeline_idx, translated in missing_translated.items():
    if pipeline_idx in seen:
        continue
    row = dict(translated)
    row["provenance"]  = build_provenance(pipeline_idx, "translated_missing")
    row["is_cultural"] = row.get("type") == "E"
    row["in_dev_set"]  = pipeline_idx in dev_idx
    output.append(row)
    seen.add(pipeline_idx)
    from_missing += 1

if from_missing:
    print(f"  + {from_missing} instancias incorporadas desde missing_129_translated")

output.sort(key=lambda r: r["idx"])

# ── Sanity checks ─────────────────────────────────────────────────────────────
assert len(output) == len(seen), "Duplicados en output"
bad_labels = [r["idx"] for r in output if r.get("label") not in LABEL_MAP]
if bad_labels:
    print(f"  ⚠ {len(bad_labels)} filas con label inválido (se incluyen igual): {bad_labels[:5]}")

verdict_dist = {}
for r in output:
    v = r["provenance"]["grader_verdict"]
    verdict_dist[v] = verdict_dist.get(v, 0) + 1

corr_dist: dict[str, int] = {}
for r in output:
    for c in r["provenance"]["corrections"]:
        corr_dist[c] = corr_dist.get(c, 0) + 1

has_sonnet  = sum(1 for r in output if r["provenance"]["quality_scores"])
has_human   = sum(1 for r in output if r["provenance"]["human_validation"])
is_cultural = sum(1 for r in output if r["is_cultural"])
in_dev      = sum(1 for r in output if r["in_dev_set"])

# ── Write ─────────────────────────────────────────────────────────────────────
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(
    "\n".join(json.dumps(r, ensure_ascii=False) for r in output) + "\n",
    encoding="utf-8"
)

print(f"\n✓ dataset_final.jsonl — {len(output)} instancias → {OUT}")
print(f"\n── grader_verdict ──────────────────────────────")
for v, n in sorted(verdict_dist.items(), key=lambda x: -x[1]):
    print(f"  {v:<30} {n:>5}")
print(f"\n── corrections (por tipo) ───────────────────────")
for c, n in sorted(corr_dist.items(), key=lambda x: -x[1]):
    print(f"  {c:<20} {n:>5}")
print(f"\n── coverage ─────────────────────────────────────")
print(f"  con score Sonnet:     {has_sonnet:>5}  ({has_sonnet/len(output)*100:.1f}%)")
print(f"  con validación nativa:{has_human:>5}  ({has_human/len(output)*100:.1f}%)")
print(f"  is_cultural:          {is_cultural:>5}")
print(f"  in_dev_set:           {in_dev:>5}")
