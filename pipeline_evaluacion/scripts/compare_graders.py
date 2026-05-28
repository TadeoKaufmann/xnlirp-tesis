"""
compare_graders.py — Compara veredictos de dos graders sobre el mismo conjunto de instancias.

Uso:
    python pipeline_evaluacion/scripts/compare_graders.py \
        --a results/experiments/grader_output/veredictos_batch_500.jsonl \
        --b results/experiments/grader_output/batch_500_input__gemini-2.5-flash__T0.1__v2_graded.jsonl \
        --label-a sonnet --label-b gpt-4o-mini
"""

import argparse
import json
from collections import Counter
from pathlib import Path


def load_verdicts(path: Path) -> dict[int, dict]:
    with open(path, encoding="utf-8") as f:
        return {obj["idx"]: obj for line in f if line.strip() for obj in [json.loads(line)]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--a", required=True, help="JSONL grader A (referencia)")
    parser.add_argument("--b", required=True, help="JSONL grader B (a calibrar)")
    parser.add_argument("--label-a", default="grader_a")
    parser.add_argument("--label-b", default="grader_b")
    args = parser.parse_args()

    a = load_verdicts(Path(args.a))
    b = load_verdicts(Path(args.b))

    common = sorted(set(a) & set(b))
    only_a = sorted(set(a) - set(b))
    only_b = sorted(set(b) - set(a))

    print(f"\n=== Comparación {args.label_a} vs {args.label_b} ===")
    print(f"  {args.label_a}: {len(a)} instancias")
    print(f"  {args.label_b}: {len(b)} instancias")
    print(f"  Común: {len(common)} | Solo en A: {len(only_a)} | Solo en B: {len(only_b)}")

    agree = []
    disagree = []
    for idx in common:
        va, vb = a[idx]["verdict"], b[idx]["verdict"]
        if va == vb:
            agree.append(idx)
        else:
            disagree.append((idx, va, vb))

    agreement = len(agree) / len(common) * 100 if common else 0
    print(f"\n  Acuerdo: {len(agree)}/{len(common)} ({agreement:.1f}%)")
    print(f"  Desacuerdo: {len(disagree)}")

    if disagree:
        print(f"\n  Distribución de desacuerdos ({args.label_a} → {args.label_b}):")
        diff_counts = Counter(f"{va} → {vb}" for _, va, vb in disagree)
        for pattern, cnt in diff_counts.most_common():
            print(f"    {cnt}x  {pattern}")

        print(f"\n  Detalle de desacuerdos:")
        for idx, va, vb in disagree:
            note_a = a[idx].get("note", "")[:80]
            note_b = b[idx].get("note", "")[:80]
            print(f"    idx {idx:5d}:  {args.label_a}={va:<16} {args.label_b}={vb}")
            if note_a: print(f"             A: {note_a}")
            if note_b: print(f"             B: {note_b}")

    print(f"\n  Distribución {args.label_a}: {dict(Counter(a[i]['verdict'] for i in common))}")
    print(f"  Distribución {args.label_b}: {dict(Counter(b[i]['verdict'] for i in common))}")


if __name__ == "__main__":
    main()
