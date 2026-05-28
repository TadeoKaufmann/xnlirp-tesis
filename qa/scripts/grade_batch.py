"""
Gradea un round de preguntas QA usando Claude Sonnet como juez.

Evalúa cada instancia en 4 dimensiones (1-3) y produce:
  - grades.jsonl: score por instancia
  - grade_report.md: resumen de issues + sugerencias de mejora al prompt

Uso:
  python qa/scripts/grade_batch.py --round round_001
  python qa/scripts/grade_batch.py --round round_001 --limit 20
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
from tqdm import tqdm

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
QA_ROOT = REPO_ROOT / "qa"
ROUNDS_DIR = QA_ROOT / "rounds"
PROMPTS_DIR = QA_ROOT / "prompts" / "grader"

MODEL = "claude-sonnet-4-5"
MAX_TOKENS = 300
API_PAUSE = 0.15
MAX_RETRIES = 3
RANDOM_SEED = 42

DIMENSIONS = ["rp_quality", "answerability", "reformulation", "neg_difficulty"]


def load_round(round_dir: Path) -> tuple[list[dict], list[dict]]:
    """Carga generated.jsonl y agrupa en grupos (1 pos + k neg) por pregunta."""
    gen_path = round_dir / "generated.jsonl"

    # Intentar cargar generated.jsonl; si no existe, usar qa_stories_dataset.jsonl (round_001)
    if not gen_path.exists():
        alt = round_dir / "qa_stories_dataset.jsonl"
        if alt.exists():
            gen_path = alt
        else:
            raise FileNotFoundError(f"No se encontró generated.jsonl ni qa_stories_dataset.jsonl en {round_dir}")

    rows = [json.loads(l) for l in gen_path.read_text(encoding="utf-8").splitlines() if l.strip()]

    # Agrupar por answer_unit_idx dentro de cada cuento
    groups: dict[tuple, dict] = {}
    for r in rows:
        key = (r["story"], r["answer_unit_idx"])
        if key not in groups:
            groups[key] = {"story": r["story"], "question": r["question"],
                           "question_type": r["question_type"],
                           "answer_unit_idx": r["answer_unit_idx"],
                           "pos": None, "negs": []}
        if r["label"] == 1:
            groups[key]["pos"] = r["unit"]
        else:
            groups[key]["negs"].append(r["unit"])

    valid = [g for g in groups.values() if g["pos"] and g["negs"] and g["question"]]
    return valid, rows


def get_anthropic_client():
    load_dotenv(REPO_ROOT / ".env")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("ANTHROPIC_API_KEY no está en .env — agregála para usar el grader Sonnet")
    import anthropic
    return anthropic.Anthropic(api_key=api_key)


def load_grader_prompt() -> str:
    # Usa la versión más reciente
    versions = sorted(PROMPTS_DIR.glob("v*.txt"), reverse=True)
    if not versions:
        raise FileNotFoundError(f"No hay prompts de grader en {PROMPTS_DIR}")
    return versions[0].read_text(encoding="utf-8")


def build_grader_prompt(template: str, group: dict) -> str:
    negs_text = "\n".join(f"{i+1}. {n}" for i, n in enumerate(group["negs"]))
    return template.format(
        story=group["story"],
        question_type=group["question_type"],
        question=group["question"],
        positive=group["pos"],
        negatives=negs_text,
    )


def call_sonnet(client, prompt: str) -> str | None:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            msg = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text.strip()
        except Exception as e:
            print(f"  [WARN] intento {attempt}: {e}", file=sys.stderr)
            time.sleep(3 * attempt)
    return None


def parse_grade(text: str) -> dict | None:
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
        scores = obj.get("scores", {})
        if not all(k in scores for k in DIMENSIONS):
            return None
        return obj
    except (json.JSONDecodeError, KeyError):
        return None


def write_report(round_dir: Path, grades: list[dict], groups: list[dict]) -> None:
    valid = [g for g in grades if g.get("scores")]
    n = len(valid)
    if n == 0:
        return

    overall_counts = Counter(g.get("overall", "?") for g in valid)
    pass_rate = overall_counts.get("pass", 0) / n * 100

    lines = [
        f"# Reporte de calidad — {round_dir.name}",
        "",
        f"**Grader:** {MODEL}",
        f"**Instancias evaluadas:** {n}",
        f"**Pass rate:** {overall_counts.get('pass', 0)}/{n} ({pass_rate:.1f}%)",
        f"**Borderline:** {overall_counts.get('borderline', 0)}",
        f"**Fail:** {overall_counts.get('fail', 0)}",
        "",
        "## Scores por dimensión (promedio)",
        "",
        "| Dimensión | Promedio | % con score 1 (problema) |",
        "|-----------|----------|--------------------------|",
    ]

    for dim in DIMENSIONS:
        vals = [g["scores"][dim] for g in valid if dim in g.get("scores", {})]
        if vals:
            avg = sum(vals) / len(vals)
            pct_bad = sum(1 for v in vals if v == 1) / len(vals) * 100
            lines.append(f"| {dim} | {avg:.2f} | {pct_bad:.1f}% |")

    # Issues más frecuentes
    all_issues: list[str] = []
    for g in valid:
        all_issues.extend(g.get("issues", []))
    issue_counts = Counter(all_issues)

    lines += ["", "## Issues más frecuentes", ""]
    for issue, count in issue_counts.most_common(10):
        lines.append(f"- ({count}x) {issue}")

    # Casos fail
    fails = [g for g in valid if g.get("overall") == "fail"]
    if fails:
        lines += ["", f"## Casos fail ({len(fails)})", ""]
        for g in fails[:10]:
            grp = next((x for x in groups if x["story"] == g["story"]
                        and x["answer_unit_idx"] == g.get("answer_unit_idx")), {})
            lines += [
                f"**Cuento:** {g['story']}",
                f"**Pregunta:** {grp.get('question', '?')}",
                f"**Scores:** {g.get('scores', {})}",
                f"**Issues:** {', '.join(g.get('issues', []))}",
                "",
            ]

    lines += [
        "## Sugerencias para mejorar el prompt de generación",
        "",
        "> Revisar estas sugerencias y actualizar `qa/prompts/generation/vX.txt`",
        "",
    ]

    # Agregar sugerencias del grader si las hay
    suggestions_dim = []
    for dim in DIMENSIONS:
        vals = [g["scores"][dim] for g in valid if dim in g.get("scores", {})]
        if vals and sum(1 for v in vals if v <= 1) / len(vals) > 0.10:
            suggestions_dim.append(dim)

    if "rp_quality" in suggestions_dim:
        lines.append("- **rp_quality**: Reforzar en el prompt la lista de peninsularismos a evitar y ejemplos de léxico RP.")
    if "answerability" in suggestions_dim:
        lines.append("- **answerability**: Agregar instrucción explícita: la pregunta debe poder responderse SOLO con la oración target, sin leer el contexto.")
    if "reformulation" in suggestions_dim:
        lines.append("- **reformulation**: Agregar ejemplos de buena reformulación. Prohibir usar más de 2 palabras exactas de la oración.")
    if "neg_difficulty" in suggestions_dim:
        lines.append("- **neg_difficulty**: Considerar aumentar distancia mínima entre target y negativos, o filtrar negativos semánticamente similares.")

    out_path = round_dir / "grade_report.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[report] → {out_path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--round", required=True, help="Nombre del round, ej. round_001")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--grader-version", default=None, dest="grader_version",
                    help="Versión del prompt de grader (default: más reciente)")
    args = ap.parse_args()

    round_dir = ROUNDS_DIR / args.round
    if not round_dir.exists():
        raise SystemExit(f"Round no encontrado: {round_dir}")

    groups, _ = load_round(round_dir)
    print(f"[load] {len(groups)} grupos de preguntas en {args.round}")

    if args.limit:
        groups = groups[:args.limit]
        print(f"[limit] evaluando {len(groups)} grupos")

    # Cargar prompt de grader
    if args.grader_version:
        grader_template = (PROMPTS_DIR / f"{args.grader_version}.txt").read_text(encoding="utf-8")
    else:
        versions = sorted(PROMPTS_DIR.glob("v*.txt"), reverse=True)
        grader_template = versions[0].read_text(encoding="utf-8")

    client = get_anthropic_client()

    grades: list[dict] = []
    n_fail = 0

    for group in tqdm(groups, desc=f"gradeando [{args.round}]"):
        prompt = build_grader_prompt(grader_template, group)
        raw = call_sonnet(client, prompt)
        time.sleep(API_PAUSE)

        if raw is None:
            n_fail += 1
            grades.append({"story": group["story"], "answer_unit_idx": group["answer_unit_idx"],
                           "scores": None, "issues": [], "overall": "error"})
            continue

        parsed = parse_grade(raw)
        if parsed is None:
            n_fail += 1
            grades.append({"story": group["story"], "answer_unit_idx": group["answer_unit_idx"],
                           "scores": None, "issues": [f"parse error: {raw[:100]}"], "overall": "error"})
        else:
            grades.append({
                "story": group["story"],
                "answer_unit_idx": group["answer_unit_idx"],
                **parsed,
            })

    # Guardar grades
    out_grades = round_dir / "grades.jsonl"
    out_grades.parent.mkdir(parents=True, exist_ok=True)
    with out_grades.open("w", encoding="utf-8") as f:
        for g in grades:
            f.write(json.dumps(g, ensure_ascii=False) + "\n")
    print(f"[grades] → {out_grades}")

    valid = [g for g in grades if g.get("scores")]
    if valid:
        overall = Counter(g["overall"] for g in valid)
        print(f"\nResultado: pass={overall['pass']} borderline={overall['borderline']} fail={overall['fail']}")
        for dim in DIMENSIONS:
            vals = [g["scores"][dim] for g in valid]
            print(f"  {dim}: avg={sum(vals)/len(vals):.2f}  fail%={sum(1 for v in vals if v==1)/len(vals)*100:.1f}%")

    write_report(round_dir, grades, groups)
    print(f"\n[done] Revisá qa/rounds/{args.round}/grade_report.md para las sugerencias")


if __name__ == "__main__":
    main()
