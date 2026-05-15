"""Formatea un run jsonl en bloques chat-friendly para review.

Uso:
    python format_for_review.py \\
        --run results/experiments/xnli_sample_300_v2_test__gemini-2.5-flash__T0.1__v2.jsonl \\
        --output _review_batch_300.txt \\
        --batch-size 25

Genera bloques de N instancias cada uno con:
- idx, label, tipo predicho, review_flag
- prem_es, prem_rp
- hyp_es, hyp_rp
- changes (lista)
- review_note (si flag)

Ordena por:
1. Instancias con review_flag=True (prioridad).
2. Instancias con type=D (riesgo de armonización).
3. Instancias con type=E (riesgo cultural).
4. Sample random de type B/C (verificar reglas).
5. Sample random de type A (verificar que no se perdieron cambios obvios).
"""
from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path


def load_run(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def render_case(r: dict) -> str:
    lines = [
        f"idx {r['idx']} | label={r.get('label','?')} | type={r.get('type','?')}"
        + (f" | review_flag=True" if r.get('review_flag') else "")
    ]
    lines.append(f"  prem_ES: {r.get('prem_es','')}")
    if r.get('prem_rp', '') != r.get('prem_es', ''):
        lines.append(f"  prem_RP: {r.get('prem_rp','')}")
    lines.append(f"  hyp_ES:  {r.get('hyp_es','')}")
    if r.get('hyp_rp', '') != r.get('hyp_es', ''):
        lines.append(f"  hyp_RP:  {r.get('hyp_rp','')}")
    if r.get('changes'):
        lines.append(f"  changes: {r['changes']}")
    if r.get('review_note'):
        lines.append(f"  review_note: {r['review_note']}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--batch-size", type=int, default=25)
    parser.add_argument("--sample-A", type=int, default=20, help="cuántos type=A randomizar")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    run = load_run(Path(args.run))
    random.seed(args.seed)

    flagged = [r for r in run if r.get('review_flag')]
    type_d = [r for r in run if r.get('type') == 'D' and not r.get('review_flag')]
    type_e = [r for r in run if r.get('type') == 'E' and not r.get('review_flag')]
    type_bc = [r for r in run if r.get('type') in ('B', 'C') and not r.get('review_flag')]
    type_a = [r for r in run if r.get('type') == 'A' and not r.get('review_flag')]

    random.shuffle(type_bc)
    random.shuffle(type_a)
    sampled_a = type_a[:args.sample_A]

    ordered = flagged + type_d + type_e + type_bc + sampled_a

    out = Path(args.output)
    types_dist = Counter(r.get('type', '?') for r in run)

    parts = []
    parts.append("=" * 76)
    parts.append(f"BATCH DE REVIEW — {Path(args.run).name}")
    parts.append(f"Total run: {len(run)} | Distribución tipos: {dict(types_dist)}")
    parts.append(f"Para review: {len(ordered)} casos "
                 f"(flagged={len(flagged)}, D={len(type_d)}, E={len(type_e)}, "
                 f"B/C={len(type_bc)}, A_sample={len(sampled_a)})")
    parts.append("=" * 76)
    parts.append("")
    parts.append("Para cada idx, devolver:")
    parts.append("  idx <N>: <APROBAR | REVISAR | RECHAZAR>")
    parts.append("    motivo: <una línea>")
    parts.append("    fix: <propuesta o null>")
    parts.append("")

    n = 0
    for batch_start in range(0, len(ordered), args.batch_size):
        batch = ordered[batch_start:batch_start + args.batch_size]
        parts.append("-" * 76)
        parts.append(f"BLOQUE {batch_start // args.batch_size + 1} "
                     f"({batch_start + 1}-{batch_start + len(batch)} de {len(ordered)})")
        parts.append("-" * 76)
        for r in batch:
            n += 1
            parts.append("")
            parts.append(render_case(r))
        parts.append("")

    out.write_text("\n".join(parts), encoding="utf-8")
    print(f"Escrito: {out} ({n} casos en {(n + args.batch_size - 1) // args.batch_size} bloques)")


if __name__ == "__main__":
    main()
