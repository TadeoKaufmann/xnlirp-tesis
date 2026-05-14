"""
Validación zero-shot del dataset QA por consistency check.

Para cada pregunta, presenta al modelo la pregunta + candidatos desordenados
(1 positivo + k negativos) y le pide que elija cuál oración contiene la respuesta.

Si el modelo acierta >> 25% (chance con 4 candidatos) → el dataset tiene sentido semántico.
Si falla sistemáticamente → hay preguntas ambiguas o negativos también respondibles.

Uso:
  python scripts/validate_qa_dataset.py
  python scripts/validate_qa_dataset.py --limit 50
  python scripts/validate_qa_dataset.py --input data/processed/qa_stories_dataset.jsonl
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
from tqdm import tqdm

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = REPO_ROOT / "data" / "processed" / "qa_stories_dataset.jsonl"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "processed" / "qa_validation_results.jsonl"
DEFAULT_REPORT = REPO_ROOT / "data" / "processed" / "qa_validation_report.md"

MODEL = "gemini-2.5-flash"
TEMPERATURE = 0.0   # determinístico para validación
API_PAUSE = 0.25
MAX_RETRIES = 3
RANDOM_SEED = 99

PROMPT_TEMPLATE = """\
Sos un sistema de comprensión lectora. Te doy una pregunta sobre un cuento y \
{n} oraciones candidatas numeradas. Solo UNA de ellas contiene la respuesta directa \
a la pregunta. Las demás son oraciones del mismo cuento que NO responden la pregunta.

Pregunta: {question}

Candidatos:
{candidates}

Respondé SOLO con el número de la oración que contiene la respuesta. \
Sin explicación, sin texto adicional. Solo el número (1, 2, 3...).
"""


def load_groups(path: Path) -> list[dict]:
    """Carga el JSONL y agrupa por (story, answer_unit_idx).
    Devuelve lista de dicts con keys: story, question, question_type, split, pos, negs.
    """
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    buckets: dict[tuple, dict] = {}
    for r in rows:
        key = (r["story"], r["answer_unit_idx"])
        if key not in buckets:
            buckets[key] = {
                "story": r["story"],
                "question": r.get("question", ""),
                "question_type": r["question_type"],
                "split": r["split"],
                "pos": None,
                "negs": [],
            }
        if r["label"] == 1:
            buckets[key]["pos"] = r["unit"]
        else:
            buckets[key]["negs"].append(r["unit"])
    # Filtrar grupos incompletos
    return [g for g in buckets.values() if g["pos"] and g["negs"]]


def build_prompt(question: str, candidates: list[str]) -> str:
    lines = "\n".join(f"{i+1}. {c}" for i, c in enumerate(candidates))
    return PROMPT_TEMPLATE.format(n=len(candidates), question=question, candidates=lines)


def parse_answer(text: str, n_candidates: int) -> int | None:
    """Extrae el número elegido por el modelo. Devuelve índice 0-based o None."""
    text = text.strip()
    m = re.search(r"\b([1-9])\b", text)
    if m:
        idx = int(m.group(1)) - 1
        if 0 <= idx < n_candidates:
            return idx
    return None


def get_client():
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise SystemExit("GOOGLE_API_KEY no está en .env")
    from google import genai
    return genai.Client(api_key=api_key)


def call_gemini(client, prompt: str) -> str | None:
    from google.genai import types as genai_types
    cfg = genai_types.GenerateContentConfig(temperature=TEMPERATURE)
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = client.models.generate_content(model=MODEL, contents=prompt, config=cfg)
            text = (resp.text or "").strip()
            if text:
                return text
        except Exception as e:
            print(f"  [WARN] intento {attempt}: {e}", file=sys.stderr)
            time.sleep(3 * attempt)
    return None


def run_validation(groups: list[dict], client, rng: random.Random) -> list[dict]:
    results = []
    for g in tqdm(groups, desc="validando"):
        candidates = [g["pos"]] + g["negs"]
        rng.shuffle(candidates)
        correct_idx = candidates.index(g["pos"])

        prompt = build_prompt(g["question"], candidates)
        raw = call_gemini(client, prompt)
        time.sleep(API_PAUSE)

        if raw is None:
            chosen_idx = None
            correct = None
        else:
            chosen_idx = parse_answer(raw, len(candidates))
            correct = (chosen_idx == correct_idx) if chosen_idx is not None else None

        results.append({
            "story": g["story"],
            "question": g["question"],
            "question_type": g["question_type"],
            "split": g["split"],
            "n_candidates": len(candidates),
            "correct_idx": correct_idx,
            "chosen_idx": chosen_idx,
            "correct": correct,
            "model_raw": raw,
        })
    return results


def write_report(results: list[dict], output_path: Path) -> None:
    total = len(results)
    answered = [r for r in results if r["correct"] is not None]
    correct = [r for r in answered if r["correct"]]
    n_candidates = results[0]["n_candidates"] if results else 4
    chance = 1 / n_candidates * 100

    lines = [
        "# Reporte de validación zero-shot del dataset QA",
        "",
        f"**Modelo:** {MODEL} (T=0.0, zero-shot)",
        f"**Grupos evaluados:** {total}",
        f"**Respondidos:** {len(answered)} ({len(results) - len(answered)} fallos API)",
        f"**Chance baseline:** {chance:.1f}% (1 de {n_candidates} candidatos)",
        "",
        "## Accuracy global",
        "",
        f"| Métrica | Valor |",
        f"|---------|-------|",
        f"| Correctas | {len(correct)} / {len(answered)} |",
        f"| Accuracy | {len(correct)/len(answered)*100:.1f}% |",
        f"| Chance baseline | {chance:.1f}% |",
        f"| Lift sobre chance | {(len(correct)/len(answered) - 1/n_candidates)*100:+.1f}pp |",
        "",
    ]

    # Por tipo de pregunta
    lines += ["## Por tipo de pregunta", "", "| Tipo | Correctas | Total | Accuracy |", "|------|-----------|-------|----------|"]
    for qtype in ("factual", "inferencial"):
        sub = [r for r in answered if r["question_type"] == qtype]
        if sub:
            acc = sum(1 for r in sub if r["correct"]) / len(sub) * 100
            lines.append(f"| {qtype} | {sum(1 for r in sub if r['correct'])} | {len(sub)} | {acc:.1f}% |")
    lines.append("")

    # Por split
    lines += ["## Por split", "", "| Split | Correctas | Total | Accuracy |", "|-------|-----------|-------|----------|"]
    for split in ("train", "dev", "test"):
        sub = [r for r in answered if r["split"] == split]
        if sub:
            acc = sum(1 for r in sub if r["correct"]) / len(sub) * 100
            lines.append(f"| {split} | {sum(1 for r in sub if r['correct'])} | {len(sub)} | {acc:.1f}% |")
    lines.append("")

    # Por cuento
    lines += ["## Por cuento", "", "| Cuento | Correctas | Total | Accuracy |", "|--------|-----------|-------|----------|"]
    by_story: dict[str, list] = defaultdict(list)
    for r in answered:
        by_story[r["story"]].append(r)
    for story, sub in sorted(by_story.items(), key=lambda x: -len(x[1])):
        acc = sum(1 for r in sub if r["correct"]) / len(sub) * 100
        lines.append(f"| {story} | {sum(1 for r in sub if r['correct'])} | {len(sub)} | {acc:.1f}% |")
    lines.append("")

    # Errores: preguntas donde el modelo falló
    errors = [r for r in answered if not r["correct"]]
    if errors:
        lines += [f"## Errores ({len(errors)} casos)", ""]
        for r in errors[:20]:
            lines += [
                f"**Cuento:** {r['story']} | **Tipo:** {r['question_type']}",
                f"**Pregunta:** {r['question']}",
                f"**Eligió candidato:** {(r['chosen_idx'] or -1) + 1} (correcto era {r['correct_idx'] + 1})",
                "",
            ]
        if len(errors) > 20:
            lines.append(f"_(y {len(errors) - 20} errores más — ver JSONL completo)_")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReporte guardado: {output_path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    ap.add_argument("--limit", type=int, default=None, help="Evaluar solo N grupos (testing).")
    ap.add_argument("--seed", type=int, default=RANDOM_SEED)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    groups = load_groups(args.input)
    print(f"[load] {len(groups)} grupos de preguntas cargados.")

    if args.limit:
        rng_sample = random.Random(args.seed + 1)
        groups = rng_sample.sample(groups, min(args.limit, len(groups)))
        print(f"[limit] evaluando {len(groups)} grupos.")

    client = get_client()
    results = run_validation(groups, client, rng)

    # Guardar resultados raw
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"[export] {len(results)} resultados -> {args.output.name}")

    # Reporte
    write_report(results, args.report)

    # Resumen en consola
    answered = [r for r in results if r["correct"] is not None]
    if answered:
        acc = sum(1 for r in answered if r["correct"]) / len(answered) * 100
        n_cands = results[0]["n_candidates"]
        chance = 100 / n_cands
        print(f"\nAccuracy: {acc:.1f}%  |  Chance: {chance:.1f}%  |  Lift: {acc - chance:+.1f}pp")


if __name__ == "__main__":
    main()
