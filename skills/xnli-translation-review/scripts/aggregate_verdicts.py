"""Parsea líneas de veredicto del reviewer y agrega métricas.

Espera input en formato:
    idx 1234: APROBAR
      motivo: voseo correcto
      fix: null
    idx 5678: RECHAZAR
      motivo: armoniza ED con hyp
      fix: revertir prem a "ED"

Uso:
    python aggregate_verdicts.py --input verdicts.txt --run <run.jsonl> --output report.md
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

VERDICT_RE = re.compile(r"^idx\s+(\d+):\s*(APROBAR|REVISAR|RECHAZAR)\s*$", re.IGNORECASE)
MOTIVO_RE = re.compile(r"^\s*motivo:\s*(.+)$", re.IGNORECASE)
FIX_RE = re.compile(r"^\s*fix:\s*(.+)$", re.IGNORECASE)


def parse_verdicts(text: str) -> list[dict]:
    verdicts = []
    current = None
    for line in text.splitlines():
        m = VERDICT_RE.match(line)
        if m:
            if current:
                verdicts.append(current)
            current = {"idx": int(m.group(1)), "verdict": m.group(2).upper(), "motivo": "", "fix": ""}
            continue
        if current is None:
            continue
        m = MOTIVO_RE.match(line)
        if m:
            current["motivo"] = m.group(1).strip()
            continue
        m = FIX_RE.match(line)
        if m:
            current["fix"] = m.group(1).strip()
            continue
    if current:
        verdicts.append(current)
    return verdicts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="archivo con los veredictos del reviewer")
    parser.add_argument("--run", required=True, help="jsonl original del run (para contexto)")
    parser.add_argument("--output", required=True, help="reporte markdown")
    args = parser.parse_args()

    verdicts = parse_verdicts(Path(args.input).read_text(encoding="utf-8"))
    run = {json.loads(l)["idx"]: json.loads(l)
           for l in Path(args.run).read_text(encoding="utf-8").splitlines() if l.strip()}

    counts = Counter(v["verdict"] for v in verdicts)
    n = len(verdicts)
    pct = lambda k: f"{counts[k]/n*100:.1f}%" if n else "0%"

    rejected = [v for v in verdicts if v["verdict"] == "RECHAZAR"]
    review = [v for v in verdicts if v["verdict"] == "REVISAR"]
    motivos = Counter(v["motivo"] for v in (rejected + review) if v["motivo"])

    lines = []
    lines.append(f"# Review aggregate — {Path(args.input).name}")
    lines.append("")
    lines.append(f"- Total veredictos: **{n}**")
    lines.append(f"- APROBAR: {counts['APROBAR']} ({pct('APROBAR')})")
    lines.append(f"- REVISAR: {counts['REVISAR']} ({pct('REVISAR')})")
    lines.append(f"- RECHAZAR: {counts['RECHAZAR']} ({pct('RECHAZAR')})")
    lines.append("")

    if motivos:
        lines.append("## Top motivos (REVISAR + RECHAZAR)")
        lines.append("")
        for motivo, count in motivos.most_common(15):
            lines.append(f"- ({count}) {motivo}")
        lines.append("")

    if rejected:
        lines.append("## Rechazados")
        lines.append("")
        for v in rejected[:30]:
            r = run.get(v["idx"], {})
            lines.append(f"### idx {v['idx']} — {v['motivo']}")
            lines.append(f"- type predicho: {r.get('type','?')}")
            lines.append(f"- prem_RP: {r.get('prem_rp','')}")
            lines.append(f"- hyp_RP: {r.get('hyp_rp','')}")
            if v["fix"] and v["fix"].lower() not in ("null", "none", ""):
                lines.append(f"- fix sugerido: {v['fix']}")
            lines.append("")

    aprobado_pct = counts['APROBAR'] / n if n else 0
    rechazado_pct = counts['RECHAZAR'] / n if n else 0
    lines.append("## Decisión sugerida")
    lines.append("")
    if aprobado_pct >= 0.9 and rechazado_pct <= 0.05:
        lines.append("**Batch listo** para validación humana (≥90% aprobados, ≤5% rechazados).")
    elif aprobado_pct >= 0.7:
        lines.append("**Iterar prompt** sobre los patrones de rechazo y re-correr.")
    else:
        lines.append("**Revisar prompt seriamente** — hay problema sistémico.")

    Path(args.output).write_text("\n".join(lines), encoding="utf-8")
    print(f"Escrito: {args.output}")
    print(f"APROBAR {pct('APROBAR')} | REVISAR {pct('REVISAR')} | RECHAZAR {pct('RECHAZAR')}")


if __name__ == "__main__":
    main()
