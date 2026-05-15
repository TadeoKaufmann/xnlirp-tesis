"""Genera SQL para upload de instancias XNLI a Supabase.

Modos:
  --mode replace-all : DELETE FROM instancias + INSERT del batch
  --mode append      : INSERT con ON CONFLICT (idx) DO UPDATE
  --mode delete-batch: DELETE FROM instancias WHERE batch_name = ...

Uso:
  python generate_upload_sql.py --input <run.jsonl> --batch-name <name> \\
      --mode replace-all --output validation_app/upload_sql/<name>.sql
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path


def escape_dollar(text: str) -> str:
    """Escape para dollar-quoted strings de Postgres. Reemplaza $$ por $%$."""
    return (text or "").replace("$$", "$%$")


def load_instances(path: Path) -> list[dict]:
    """Lee jsonl, retorna lista de {idx, prem, hyp} usando prem_rp/hyp_rp (fallback a prem_es/hyp_es)."""
    out = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            prem = r.get("prem_rp") or r.get("prem_es", "")
            hyp = r.get("hyp_rp") or r.get("hyp_es", "")
            if not prem or not hyp:
                continue
            out.append({"idx": r["idx"], "prem": prem, "hyp": hyp})
    return out


def render_insert(rows: list[dict], batch_name: str, source_file: str, mode: str) -> str:
    lines = []
    lines.append(f"-- {len(rows)} instancias del batch {batch_name}")
    lines.append(f"-- source: {source_file}")
    lines.append(f"-- generado: {date.today().isoformat()}")
    lines.append("")
    if not rows:
        return "\n".join(lines) + "\n-- (sin filas)\n"

    lines.append("INSERT INTO instancias (idx, prem, hyp, batch_name, source_file) VALUES")
    value_lines = []
    for r in rows:
        prem = escape_dollar(r["prem"])
        hyp = escape_dollar(r["hyp"])
        bn = escape_dollar(batch_name)
        sf = escape_dollar(source_file)
        value_lines.append(f"  ({r['idx']}, $${prem}$$, $${hyp}$$, $${bn}$$, $${sf}$$)")
    lines.append(",\n".join(value_lines))

    if mode == "append":
        lines.append("ON CONFLICT (idx) DO UPDATE SET")
        lines.append("  prem = EXCLUDED.prem,")
        lines.append("  hyp = EXCLUDED.hyp,")
        lines.append("  batch_name = EXCLUDED.batch_name,")
        lines.append("  source_file = EXCLUDED.source_file,")
        lines.append("  uploaded_at = now()")
    elif mode == "replace-all":
        # los samples XNLI pueden tener idxs duplicados (mismo idx con distinto hyp en tripletes);
        # ignorar duplicados dentro del INSERT mantiene solo la primera ocurrencia por idx.
        lines.append("ON CONFLICT (idx) DO NOTHING")
    lines.append(";")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, help="jsonl de entrada (run de Gemini o equivalente)")
    parser.add_argument("--batch-name", required=True)
    parser.add_argument("--mode", choices=("replace-all", "append", "delete-batch"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    out_path = args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    parts: list[str] = []

    if args.mode == "replace-all":
        if not args.input:
            raise SystemExit("--input requerido para replace-all")
        rows = load_instances(args.input)
        parts.append(f"-- REPLACE ALL — batch {args.batch_name}")
        parts.append("BEGIN;")
        parts.append("DELETE FROM instancias;")
        parts.append("")
        parts.append(render_insert(rows, args.batch_name, str(args.input), args.mode))
        parts.append("COMMIT;")
        print(f"replace-all: {len(rows)} filas -> {out_path}")
    elif args.mode == "append":
        if not args.input:
            raise SystemExit("--input requerido para append")
        rows = load_instances(args.input)
        parts.append(f"-- APPEND — batch {args.batch_name}")
        parts.append(render_insert(rows, args.batch_name, str(args.input), args.mode))
        print(f"append: {len(rows)} filas -> {out_path}")
    elif args.mode == "delete-batch":
        parts.append(f"-- DELETE BATCH — {args.batch_name}")
        bn = escape_dollar(args.batch_name)
        parts.append(f"DELETE FROM instancias WHERE batch_name = $${bn}$$;")
        print(f"delete-batch: {args.batch_name} -> {out_path}")

    out_path.write_text("\n".join(parts) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
