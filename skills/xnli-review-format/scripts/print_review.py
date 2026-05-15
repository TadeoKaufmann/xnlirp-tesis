"""Genera output con formato del skill xnli-review-format.

Uso:
    python print_review.py --output <path.txt> --task "<descripción>" --cases cases.json

cases.json: lista de objetos con campos
    idx, label, gold_type, pred_type, prem_es, prem_rp, hyp_es, hyp_rp,
    diferencias, decision, contexto, categoria (opcional)

Comportamiento:
- Si <output> no existe, crea archivo con header de fecha de hoy.
- Si existe y la última fecha es la de hoy, agrega bajo la sección activa.
- Si la última fecha es anterior, agrega nuevo header de fecha.
- Numera los casos dentro de la sección de hoy (continuando si ya había casos).
- Agrupa por `categoria` si está presente.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

SEP = "_" * 76


def render_case(n: int, c: dict) -> str:
    label = c.get("label", "?")
    gt = c.get("gold_type", "?")
    pt = c.get("pred_type", "?")
    head = f" {n}. [idx {c['idx']} | {label} | gold={gt} pred={pt}]"
    lines = [head]
    lines.append(f"    PREM ES: {c.get('prem_es', '')}")
    if c.get("prem_rp") and c["prem_rp"] != c.get("prem_es"):
        lines.append(f"    PREM RP: {c['prem_rp']}")
    lines.append(f"    HYP  ES: {c.get('hyp_es', '')}")
    if c.get("hyp_rp") and c["hyp_rp"] != c.get("hyp_es"):
        lines.append(f"    HYP  RP: {c['hyp_rp']}")
    lines.append("")
    if c.get("diferencias"):
        lines.append(f"    DIFERENCIAS: {c['diferencias']}")
    if c.get("decision"):
        lines.append(f"    DECISIÓN PROPUESTA: {c['decision']}")
    if c.get("contexto"):
        lines.append(f"    CONTEXTO: {c['contexto']}")
    return "\n".join(lines) + "\n"


def find_last_date_section(text: str) -> tuple[str | None, int]:
    pattern = re.compile(rf"{re.escape(SEP)}\n(\d{{4}}-\d{{2}}-\d{{2}}) \| .*\n{re.escape(SEP)}")
    matches = list(pattern.finditer(text))
    if not matches:
        return None, 0
    last = matches[-1]
    return last.group(1), last.end()


def count_existing_cases(section_text: str) -> int:
    nums = re.findall(r"^\s+(\d+)\.\s+\[idx ", section_text, flags=re.MULTILINE)
    return max((int(n) for n in nums), default=0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--task", required=True, help="Descripción corta de la tarea de hoy")
    parser.add_argument("--cases", required=True, help="Path a JSON con la lista de casos")
    args = parser.parse_args()

    out_path = Path(args.output)
    today = date.today().isoformat()
    cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))

    existing = out_path.read_text(encoding="utf-8") if out_path.exists() else ""
    last_date, last_pos = find_last_date_section(existing)

    parts = [existing] if existing else []

    if last_date == today:
        section_text = existing[last_pos:]
        n_start = count_existing_cases(section_text) + 1
        if not existing.endswith("\n\n"):
            parts.append("\n" if not existing.endswith("\n") else "")
    else:
        if existing and not existing.endswith("\n"):
            parts.append("\n")
        if existing:
            parts.append("\n")
        parts.append(f"{SEP}\n{today} | {args.task}\n{SEP}\n\n")
        n_start = 1

    by_cat: dict[str, list[dict]] = {}
    order: list[str] = []
    for c in cases:
        cat = c.get("categoria", "")
        if cat not in by_cat:
            by_cat[cat] = []
            order.append(cat)
        by_cat[cat].append(c)

    n = n_start
    for cat in order:
        if cat:
            parts.append(f"\nCATEGORÍA: {cat}\n{'=' * 76}\n\n")
        for c in by_cat[cat]:
            parts.append(render_case(n, c))
            parts.append("\n")
            n += 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("".join(parts), encoding="utf-8")
    print(f"Escrito en {out_path} (casos {n_start} a {n - 1}).")


if __name__ == "__main__":
    main()
