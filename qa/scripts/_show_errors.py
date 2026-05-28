import json
from pathlib import Path
import sys

round_name = sys.argv[1] if len(sys.argv) > 1 else "round_001"
path = Path(f"qa/rounds/{round_name}/validation_haiku.jsonl")
rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]

for issue in ("neg_difficulty", "wrong", "answerability"):
    subset = [r for r in rows if r.get("issue") == issue]
    if not subset:
        continue
    print(f"\n{'='*60}")
    print(f"[{issue.upper()}]  {len(subset)} casos")
    print(f"{'='*60}")
    for r in subset:
        chosen = r.get("chosen_idxs", [])
        correct = r.get("correct_idx")
        print(f"Cuento:   {r['story']}")
        print(f"Tipo:     {r['question_type']}")
        print(f"Pregunta: {r['question']}")
        print(f"Eligio:   {[i+1 for i in chosen]}  |  correcto: #{correct+1 if correct is not None else '?'}")
        print()
