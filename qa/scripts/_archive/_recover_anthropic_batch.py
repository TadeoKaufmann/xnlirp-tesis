"""
Recupera resultados de un batch job de Anthropic que completó pero cuyo polling fue interrumpido.
Uso:
  python qa/scripts/_recover_anthropic_batch.py <batch_id> <round> <n_groups>
"""
import json, sys, time
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv
load_dotenv(REPO_ROOT / ".env")
import os, random
import anthropic

from qa.scripts.validate_consistency import (
    load_groups, build_prompt, parse_answer, report,
    _poll_and_download_anthropic_batch, ROUNDS_DIR, HAIKU_MODEL, RANDOM_SEED
)

batch_id  = sys.argv[1]
round_name = sys.argv[2]
round_dir = ROUNDS_DIR / round_name

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

groups = load_groups(round_dir)
print(f"[recover] {len(groups)} grupos cargados")

rng = random.Random(RANDOM_SEED)
shuffled = []
for g in groups:
    candidates = [g["pos"]] + g["negs"]
    rng.shuffle(candidates)
    shuffled.append((candidates, candidates.index(g["pos"])))

print(f"[recover] descargando resultados de {batch_id} ...")
raw_list = _poll_and_download_anthropic_batch(client, batch_id, len(groups))

results = []
for g, (candidates, correct_idx), raw in zip(groups, shuffled, raw_list):
    chosen_idxs = parse_answer(raw, len(candidates)) if raw else None
    if chosen_idxs is None:
        issue = None
    elif len(chosen_idxs) == 0:
        issue = "answerability"
    elif correct_idx in chosen_idxs and len(chosen_idxs) == 1:
        issue = "clean"
    elif correct_idx in chosen_idxs and len(chosen_idxs) > 1:
        issue = "neg_difficulty"
    else:
        issue = "wrong"

    results.append({
        "story": g["story"], "question": g["question"],
        "question_type": g["question_type"], "split": g.get("split", ""),
        "n_candidates": len(candidates),
        "correct_idx": correct_idx, "chosen_idxs": chosen_idxs,
        "correct": (issue == "clean") if issue is not None else None,
        "issue": issue, "model": HAIKU_MODEL, "model_raw": raw,
    })

out = round_dir / "validation_haiku.jsonl"
with out.open("w", encoding="utf-8") as f:
    for r in results:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print(f"[out] → {out}")
report(results, round_name, "haiku")
