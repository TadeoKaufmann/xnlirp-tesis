import json, sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

input_path = "results/experiments/batch_500_input__gemini-2.5-flash__T0.1__v2.jsonl"
sonnet_path = "results/experiments/grader_output/veredictos_batch_500.jsonl"
gpt_path = "results/experiments/grader_output/batch_500_input__gemini-2.5-flash__T0.1__v2_graded.jsonl"

def load_jsonl_idx(path):
    d = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                obj = json.loads(line)
                d[obj["idx"]] = obj
    return d

instances = load_jsonl_idx(input_path)
sonnet = load_jsonl_idx(sonnet_path)
gpt = load_jsonl_idx(gpt_path)

common = sorted(set(sonnet) & set(gpt))
disagree = [(idx, sonnet[idx], gpt[idx]) for idx in common if sonnet[idx]["verdict"] != gpt[idx]["verdict"]]

print(f"Total desacuerdos: {len(disagree)}\n")
for idx, va, vb in disagree:
    inst = instances.get(idx, {})
    label = inst.get("label", "?")
    prem_es = inst.get("prem_es", "?")
    prem_rp = inst.get("prem_rp", "?")
    hyp_es = inst.get("hyp_es", "?")
    hyp_rp = inst.get("hyp_rp", "?")
    note_a = va.get("note", "")[:150]
    note_b = vb.get("note", "")[:150]
    issues_a = "; ".join(va.get("issues", []))[:150]
    issues_b = "; ".join(vb.get("issues", []))[:150]

    print(f"{'='*70}")
    print(f"idx {idx} | label: {label}")
    print(f"  prem_es: {prem_es}")
    print(f"  prem_rp: {prem_rp}")
    print(f"  hyp_es:  {hyp_es}")
    print(f"  hyp_rp:  {hyp_rp}")
    print(f"  SONNET [{va['verdict']}]: {note_a}")
    if issues_a:
        print(f"    issues: {issues_a}")
    print(f"  GPT-4o  [{vb['verdict']}]: {note_b}")
    if issues_b:
        print(f"    issues: {issues_b}")
    print()
