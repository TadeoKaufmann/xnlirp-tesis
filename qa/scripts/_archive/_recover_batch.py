"""
Recupera un batch job de Gemini que completó pero cuyo polling fue interrumpido.
Uso:
  python qa/scripts/_recover_batch.py <job_name> <round> <split> <stories_csv>
"""
import json, re, sys, random
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv
load_dotenv(REPO_ROOT / ".env")

import os
from google import genai

job_name  = sys.argv[1]
round_name = sys.argv[2]
split_name = sys.argv[3]
stories_csv = sys.argv[4]

# Reproducir las mismas tareas que se enviaron (mismo seed, mismas stories)
from qa.scripts.generate_batch import (
    load_all_stories, load_cache, is_good_target,
    parse_question, append_cache, build_instances, write_jsonl,
    INFERENTIAL_RATIO, RANDOM_SEED, ROUNDS_DIR, NEGATIVES_PER_POSITIVE
)

story_filter = [s.strip() for s in stories_csv.split(",")]
stories = load_all_stories(story_filter)
cached = load_cache()
rng = random.Random(RANDOM_SEED)

tasks = []
for title, sentences in stories:
    for i, s in enumerate(sentences):
        if not is_good_target(s): continue
        if (title, i) in cached: continue
        qtype = "inferencial" if rng.random() < INFERENTIAL_RATIO else "factual"
        tasks.append((title, i, s, qtype))

print(f"[recover] {len(tasks)} tareas reconstruidas")

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
job = client.batches.get(name=job_name)
print(f"[recover] job estado: {job.state.name}, respuestas: {len(job.dest.inlined_responses)}")

raw_results = []
for r in job.dest.inlined_responses:
    try:
        raw_results.append((r.response.text or "").strip())
    except Exception:
        raw_results.append(None)

title_to_sents = {t: s for t, s in stories}
by_story = {}
n_skip = n_fail = 0
all_qrows = []

for (title, i, sent, qtype), raw in zip(tasks, raw_results):
    if raw is None:
        n_fail += 1
        continue
    question, reason = parse_question(raw)
    if question is None:
        n_fail += 1
        continue
    row = {"story": title, "unit_idx": i, "unit": sent,
           "question": None if question.upper() == "SKIP" else question,
           "question_type": qtype, "split": split_name, "skip_reason": reason}
    if question.upper() == "SKIP":
        n_skip += 1
    append_cache(row)
    all_qrows.append(row)
    by_story.setdefault(title, []).append(row)

print(f"[gen] OK={sum(1 for r in all_qrows if r['question'])} SKIP={n_skip} FAIL={n_fail}")

rng2 = random.Random(RANDOM_SEED)
all_instances = []
for title, qrows in by_story.items():
    all_instances.extend(build_instances(title, title_to_sents[title], qrows, rng2))

round_dir = ROUNDS_DIR / round_name
round_dir.mkdir(parents=True, exist_ok=True)
out_path = round_dir / "generated.jsonl"
write_jsonl(out_path, all_instances)
print(f"[out] {len(all_instances)} instancias → {out_path}")
print(f"      pos={sum(1 for r in all_instances if r['label']==1)}  neg={sum(1 for r in all_instances if r['label']==0)}")
