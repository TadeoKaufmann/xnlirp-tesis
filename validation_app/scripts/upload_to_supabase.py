"""Upload instances to Supabase via REST API in batches.

Usage:
    python validation_app/scripts/upload_to_supabase.py \
        --input validation_app/to_upload/combined_6884_full.jsonl \
        --batch-name xnli_rp_main_2026-05-26 \
        [--delete-first]  # DELETE all existing before uploading
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SUPABASE_URL = "https://gtfuywoegczehmpbmaky.supabase.co"
SUPABASE_ANON_KEY = "sb_publishable_cYbYP4tE7OF9-i2KgCpeIA_gRnhkUmc"

HEADERS = {
    "apikey": SUPABASE_ANON_KEY,
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}

CHUNK_SIZE = 200  # rows per request


def delete_all() -> None:
    print("Borrando todas las instancias existentes...")
    resp = requests.delete(
        f"{SUPABASE_URL}/rest/v1/instancias",
        headers=HEADERS,
        params={"idx": "gte.0"},
    )
    if resp.status_code not in (200, 204):
        print(f"  ERROR al borrar: {resp.status_code} — {resp.text[:300]}")
        print("  Intentá correr manualmente en el SQL editor: DELETE FROM instancias;")
        sys.exit(1)
    print(f"  OK ({resp.status_code})")


def load_instances(path: Path) -> list[dict]:
    rows = []
    seen = set()
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            idx = r["idx"]
            if idx in seen:
                continue
            seen.add(idx)
            prem = r.get("prem_rp") or r.get("prem_es", "")
            hyp = r.get("hyp_rp") or r.get("hyp_es", "")
            if not prem or not hyp:
                continue
            rows.append({"idx": idx, "prem": prem, "hyp": hyp})
    return rows


def upload_chunk(rows: list[dict], batch_name: str, source_file: str) -> bool:
    payload = [
        {
            "idx": r["idx"],
            "prem": r["prem"],
            "hyp": r["hyp"],
            "batch_name": batch_name,
            "source_file": source_file,
        }
        for r in rows
    ]
    headers = dict(HEADERS)
    headers["Prefer"] = "resolution=merge-duplicates,return=minimal"
    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/instancias",
        headers=headers,
        json=payload,
    )
    if resp.status_code not in (200, 201, 204):
        print(f"  ERROR: {resp.status_code} — {resp.text[:300]}")
        return False
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--batch-name", default="xnli_rp_main_2026-05-26")
    parser.add_argument("--delete-first", action="store_true")
    args = parser.parse_args()

    if args.delete_first:
        delete_all()

    print(f"Cargando instancias de {args.input}...")
    rows = load_instances(args.input)
    print(f"  {len(rows)} instancias únicas con prem_rp/prem_es")

    total = len(rows)
    uploaded = 0
    errors = 0
    for i in range(0, total, CHUNK_SIZE):
        chunk = rows[i : i + CHUNK_SIZE]
        ok = upload_chunk(chunk, args.batch_name, str(args.input))
        if ok:
            uploaded += len(chunk)
        else:
            errors += len(chunk)
        pct = (i + len(chunk)) / total * 100
        status = "OK" if ok else "ERR"
        print(f"  [{status}] {i + len(chunk)}/{total} ({pct:.0f}%) — chunk {i//CHUNK_SIZE + 1}")
        if not ok:
            time.sleep(1)

    print(f"\nResultado: {uploaded} subidas, {errors} errores")


if __name__ == "__main__":
    main()
