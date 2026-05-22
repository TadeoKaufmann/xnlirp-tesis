"""
Validador automático independiente del gold.
Detecta inconsistencias y produce review_queue.jsonl ordenado por prioridad.
"""
import argparse
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import Levenshtein


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RESULTS_DIR = REPO_ROOT / "results"

TUTEO_MARKERS = [
    r"\bcontigo\b", r"\btú\b", r"\btienes\b", r"\beres\b",
    r"\bpuedes\b", r"\bsabes\b", r"\bvienes\b", r"\bdices\b",
    r"\bhaces\b", r"\bvives\b", r"\bquieres\b", r"\bdebes\b",
    r"\bvosotros\b", r"\bvuestro\b", r"\bvuestra\b",
]
PENINSULAR_LEXICON = [
    r"\bcoger\b", r"\bcoges\b", r"\bcogió\b", r"\bcogía\b",
    r"\bordenador\b", r"\bordenadores\b",
    r"\bmóvil\b", r"\bmóviles\b",
    r"\bvale\b",  # interjección — hay que tener cuidado, marcar siempre
    r"\bchaval\b", r"\bchavales\b", r"\bchavala\b",
    r"\bguay\b", r"\bmola\b", r"\bmolan\b",
    r"\baparcar\b", r"\baparcamiento\b",
]
PRIORITY_LABEL_ISSUE = 100
PRIORITY_TYPE_VS_CHANGES = 80
PRIORITY_HIGH_LEV = 50
PRIORITY_TUTEO = 40
PRIORITY_PENINSULAR = 25
PRIORITY_NO_CULTURAL = 10


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def has_changes(prem_es: str, hyp_es: str, prem_rp: str, hyp_rp: str) -> bool:
    return prem_es != prem_rp or hyp_es != hyp_rp


def scan_markers(text: str, patterns: list[str]) -> list[str]:
    hits = []
    for pat in patterns:
        if re.search(pat, text, flags=re.IGNORECASE):
            hits.append(pat.replace(r"\b", "").strip())
    return hits


def lev_ratio(a: str, b: str) -> float:
    if not a:
        return 0.0
    return Levenshtein.distance(a, b) / max(len(a), 1)


def looks_like_cultural_candidate(text: str) -> bool:
    """Heurística muy simple: marcadores culturales peninsulares evidentes."""
    keywords = [r"\beuro\b", r"\beuros\b", r"\btomar el té\b", r"\btío\b", r"\btía\b",
                r"\bjoder\b", r"\bflipar\b", r"\bgenialidad\b"]
    for k in keywords:
        if re.search(k, text, flags=re.IGNORECASE):
            return True
    return False


def validate_row(row: dict, lev_threshold_ratio: float) -> list[dict]:
    issues = []
    prem_es = row.get("prem_es", "")
    hyp_es = row.get("hyp_es", "")
    prem_rp = row.get("prem_rp", "")
    hyp_rp = row.get("hyp_rp", "")
    t = row.get("type", "?")
    changes = row.get("changes", []) or []
    cc = row.get("cultural_candidates", []) or []

    # 1. Type A pero hay cambios
    if t == "A" and (prem_es != prem_rp or hyp_es != hyp_rp):
        issues.append({"code": "A_with_diff", "severity": PRIORITY_TYPE_VS_CHANGES,
                       "msg": "type=A pero prem_rp o hyp_rp difiere de la versión ES."})

    # 2. Type ≠ A pero no hay cambios
    if t in {"B", "C", "D"} and prem_es == prem_rp and hyp_es == hyp_rp:
        issues.append({"code": "nonA_no_diff", "severity": PRIORITY_TYPE_VS_CHANGES,
                       "msg": f"type={t} pero no hay diferencias entre ES y RP."})

    # 3. changes vacío con type ≠ A
    if t in {"B", "C", "D"} and not changes:
        issues.append({"code": "empty_changes_nonA", "severity": PRIORITY_TYPE_VS_CHANGES,
                       "msg": f"type={t} con changes=[]."})

    # 4. changes no vacío con type A
    if t == "A" and changes:
        issues.append({"code": "changes_with_A", "severity": PRIORITY_TYPE_VS_CHANGES,
                       "msg": "type=A pero changes no está vacío."})

    # 5. Levenshtein ratio alto
    r1 = lev_ratio(prem_es, prem_rp)
    r2 = lev_ratio(hyp_es, hyp_rp)
    if max(r1, r2) > lev_threshold_ratio:
        issues.append({"code": "high_lev_ratio", "severity": PRIORITY_HIGH_LEV,
                       "msg": f"Lev ratio alto: prem={r1:.2f}, hyp={r2:.2f} (umbral={lev_threshold_ratio})."})

    # 6. Tuteo residual en RP
    tuteo_hits = scan_markers(prem_rp, TUTEO_MARKERS) + scan_markers(hyp_rp, TUTEO_MARKERS)
    if tuteo_hits:
        # filtrar "vos" no aparece como falso positivo, pero ojo con "tú" en mayúsculas, etc.
        issues.append({"code": "tuteo_residual", "severity": PRIORITY_TUTEO,
                       "msg": f"Marcadores de tuteo en RP: {sorted(set(tuteo_hits))}"})

    # 7. Léxico peninsular residual en RP
    pen_hits = scan_markers(prem_rp, PENINSULAR_LEXICON) + scan_markers(hyp_rp, PENINSULAR_LEXICON)
    if pen_hits:
        issues.append({"code": "peninsular_residual", "severity": PRIORITY_PENINSULAR,
                       "msg": f"Léxico peninsular en RP: {sorted(set(pen_hits))}"})

    # 8. Cultural candidates posibles no marcados
    if not cc and (looks_like_cultural_candidate(prem_es) or looks_like_cultural_candidate(hyp_es)):
        issues.append({"code": "missing_cultural", "severity": PRIORITY_NO_CULTURAL,
                       "msg": "Heurística sugiere posibles cultural_candidates no marcados."})

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validador automático de traducciones RP.")
    parser.add_argument("--input", type=Path, required=True, help=".jsonl con la corrida a validar.")
    parser.add_argument("--lev-threshold", type=float, default=0.5,
                        help="Umbral de Levenshtein ratio (cambio excesivo). Default 0.5.")
    parser.add_argument("--out-jsonl", type=Path, default=None)
    parser.add_argument("--out-md", type=Path, default=None)
    args = parser.parse_args()

    if not args.input.exists():
        print(f"ERROR: no existe {args.input}", file=sys.stderr)
        return 1
    rows = load_jsonl(args.input)

    out_jsonl = args.out_jsonl or (RESULTS_DIR / "review_queue.jsonl")
    out_md = args.out_md or (RESULTS_DIR / f"validation_report_{args.input.stem}.md")
    out_jsonl.parent.mkdir(parents=True, exist_ok=True)

    queue = []
    for row in rows:
        issues = validate_row(row, args.lev_threshold)
        if issues:
            total_score = sum(i["severity"] for i in issues)
            queue.append({
                "idx": row["idx"],
                "priority": total_score,
                "type": row.get("type", "?"),
                "issues": issues,
                "prem_es": row.get("prem_es", ""),
                "hyp_es": row.get("hyp_es", ""),
                "prem_rp": row.get("prem_rp", ""),
                "hyp_rp": row.get("hyp_rp", ""),
                "changes": row.get("changes", []),
            })

    queue.sort(key=lambda x: -x["priority"])

    with out_jsonl.open("w", encoding="utf-8") as f:
        for item in queue:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    # Markdown report
    lines = [f"# Validación: {args.input.name}", "",
             f"- Instancias totales: {len(rows)}",
             f"- Instancias con issues: {len(queue)}",
             f"- Umbral Levenshtein ratio: {args.lev_threshold}", ""]

    code_counts = {}
    for item in queue:
        for i in item["issues"]:
            code_counts[i["code"]] = code_counts.get(i["code"], 0) + 1
    if code_counts:
        lines += ["## Distribución de issues por código", "", "| Código | N |", "|--------|---|"]
        for code, n in sorted(code_counts.items(), key=lambda x: -x[1]):
            lines.append(f"| {code} | {n} |")

    lines += ["", "## Top 30 instancias por prioridad", ""]
    for item in queue[:30]:
        lines.append(f"### idx {item['idx']} (prioridad {item['priority']}, type {item['type']})")
        for i in item["issues"]:
            lines.append(f"- [{i['severity']}] **{i['code']}**: {i['msg']}")
        lines.append(f"- prem_rp: {item['prem_rp']}")
        lines.append(f"- hyp_rp: {item['hyp_rp']}")
        lines.append("")

    out_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"Queue: {out_jsonl}")
    print(f"Reporte: {out_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
