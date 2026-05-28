import json, os
from collections import Counter

TRANSCRIPT = r"C:\Users\tadeo\.claude\projects\C--Users-tadeo-Desktop-Tesis-Datasets-Codigo\edd89a67-1e41-4a26-bcbc-511f1d57fe76.jsonl"
OUT = r"results\experiments\grader_output\veredictos_batch_500.jsonl"

verdicts = []
seen_idx = set()

with open(TRANSCRIPT, encoding="utf-8") as f:
    for line in f:
        try:
            entry = json.loads(line)
        except Exception:
            continue
        content = entry.get("message", {}).get("content", "")
        if not isinstance(content, list):
            content = [{"text": str(content)}] if content else []
        for block in content:
            text = block.get("text", "") if isinstance(block, dict) else str(block)
            i = 0
            while i < len(text):
                if text[i] == "{":
                    depth, j = 0, i
                    while j < len(text):
                        if text[j] == "{":
                            depth += 1
                        elif text[j] == "}":
                            depth -= 1
                            if depth == 0:
                                try:
                                    obj = json.loads(text[i:j+1])
                                    if "verdict" in obj and "idx" in obj:
                                        idx = obj["idx"]
                                        if idx not in seen_idx:
                                            seen_idx.add(idx)
                                            verdicts.append(obj)
                                except Exception:
                                    pass
                                i = j + 1
                                break
                        j += 1
                    else:
                        i += 1
                else:
                    i += 1

BATCH_INPUT = "data/batch_500_input.jsonl"
with open(BATCH_INPUT, encoding="utf-8") as f:
    batch_idxs = {json.loads(line)["idx"] for line in f if line.strip()}

verdicts = [v for v in verdicts if v.get("idx") in batch_idxs]
verdicts.sort(key=lambda x: x.get("idx", 0))

os.makedirs("results/experiments/grader_output", exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    for v in verdicts:
        f.write(json.dumps(v, ensure_ascii=False) + "\n")

idxs = [v["idx"] for v in verdicts]
counts = Counter(v["verdict"] for v in verdicts)
print(f"Total en batch_500: {len(batch_idxs)}")
print(f"Veredictos recuperados del batch: {len(verdicts)}")
print(f"idx range: {min(idxs)} - {max(idxs)}")
print(f"Distribucion: {dict(counts)}")
print(f"Accuracy: {counts.get('ok', 0) / len(verdicts) * 100:.1f}%")
print(f"Guardado en: {OUT}")
