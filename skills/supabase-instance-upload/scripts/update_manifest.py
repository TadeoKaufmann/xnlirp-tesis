"""Actualiza el upload_manifest.json del skill.

Uso:
  # Marcar un batch como subido
  python update_manifest.py --batch-name <name> --action uploaded \\
      --source-file <path> --count <int>

  # Marcar un batch viejo como retirado (cuando se hace replace-all)
  python update_manifest.py --batch-name <name> --action retired
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

MANIFEST = Path(__file__).resolve().parent / "upload_manifest.json"


def load() -> dict:
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {"current_batch": None, "history": []}


def save(d: dict) -> None:
    MANIFEST.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-name", required=True)
    parser.add_argument("--action", choices=("uploaded", "retired"), required=True)
    parser.add_argument("--source-file", default="")
    parser.add_argument("--count", type=int, default=0)
    parser.add_argument("--mode", default="replace-all")
    args = parser.parse_args()

    m = load()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    if args.action == "uploaded":
        if args.mode == "replace-all":
            for h in m["history"]:
                if h.get("status") == "active":
                    h["status"] = "retired"
                    h["retired_at"] = now
        m["current_batch"] = args.batch_name
        m["history"].append({
            "batch_name": args.batch_name,
            "uploaded_at": now,
            "count": args.count,
            "source_file": args.source_file,
            "mode": args.mode,
            "status": "active",
        })
    elif args.action == "retired":
        for h in m["history"]:
            if h["batch_name"] == args.batch_name and h.get("status") == "active":
                h["status"] = "retired"
                h["retired_at"] = now
        if m.get("current_batch") == args.batch_name:
            m["current_batch"] = None

    save(m)
    print(f"manifest actualizado: {args.batch_name} -> {args.action}")


if __name__ == "__main__":
    main()
