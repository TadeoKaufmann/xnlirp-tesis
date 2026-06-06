import json
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
round_dir = REPO_ROOT / "qa" / "rounds" / "round_003"

val_rows = [json.loads(l) for l in (round_dir / "validation_haiku.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]

groups = {}
for r in [json.loads(l) for l in (round_dir / "generated_v3.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]:
    key = (r["story"], r["answer_unit_idx"])
    groups.setdefault(key, {"pos": None, "negs": []})
    if r["label"] == 1:
        groups[key]["pos"] = r["unit"]
    else:
        groups[key]["negs"].append(r["unit"])

target = {"Rebeca", "Embarrar la magia", "La salud de los enfermos"}
nonclean = [r for r in val_rows if r.get("issue") not in ("clean", None) and r.get("story") in target]

for r in nonclean[:8]:
    key = (r["story"], r.get("answer_unit_idx"))
    g = groups.get(key, {})
    print("===", r["story"], "|", r["issue"], "===")
    print("P: ", g.get("pos", "?"))
    print("Q: ", r["question"])
    for i, n in enumerate(g.get("negs", [])[:4], 1):
        print(f"N{i}:", n)
    print()
