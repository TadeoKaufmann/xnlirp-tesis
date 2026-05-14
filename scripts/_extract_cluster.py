"""Extrae instancias XNLI por cluster (regex sobre prem+hyp).

Uso: python scripts/_extract_cluster.py <cluster> [--out path.jsonl]
Clusters: fbi_cia | 911_alqaeda | pak_afg | indiana | texas | california | all
"""
import argparse
import json
import re
import sys
from pathlib import Path

CLUSTERS = {
    "fbi_cia": r"\b(fbi|cia|nsa|dea)\b",
    "911_alqaeda": r"\b(qaeda|hazmi|mihdhar|atta|ksm|moussaoui|binalshibh|shehhi|jarrah|mihdar|laden|world\s+trade)\b",
    "pak_afg": r"\b(pakistan|afghanistan|afganistan|talibanes?|taliban|kandahar|kabul)\b",
    "indiana": r"\bindiana(polis)?\b",
    "texas": r"\btexas\b",
    "california": r"\bcalifornia\b",
}

INPUT = Path("data/raw/xnli/xnli_full_7500.jsonl")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cluster", choices=list(CLUSTERS.keys()) + ["all"])
    ap.add_argument("--out", default=None)
    ap.add_argument("--print", action="store_true")
    args = ap.parse_args()

    clusters = [args.cluster] if args.cluster != "all" else list(CLUSTERS.keys())

    rows = []
    with INPUT.open("r", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            text = (r.get("prem_es", "") + " " + r.get("hyp_es", "")).lower()
            for c in clusters:
                if re.search(CLUSTERS[c], text):
                    r["_cluster"] = c
                    rows.append(r)
                    break

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"Escritos {len(rows)} a {args.out}", file=sys.stderr)

    if args.print or not args.out:
        for r in rows:
            print(json.dumps(r, ensure_ascii=False))
    print(f"Total {args.cluster}: {len(rows)}", file=sys.stderr)


if __name__ == "__main__":
    main()
