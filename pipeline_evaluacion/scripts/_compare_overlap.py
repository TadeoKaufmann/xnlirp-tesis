import json

batch = {json.loads(l)["idx"]: json.loads(l) for l in open("results/experiments/xnli_full_7500__gemini-2.5-flash__T0.1__v2.jsonl", encoding="utf-8")}
gold  = {json.loads(l)["idx"]: json.loads(l) for l in open("data/dev/xnli_combined_dev_200.jsonl", encoding="utf-8")}

overlap = [idx for idx in batch if idx in gold]
print(f"Overlap: {overlap}")

for idx in overlap:
    b = batch[idx]
    g = gold[idx]
    same_type = b["type"] == g["type"]
    same_prem = b["prem_rp"] == g["prem_rp"]
    same_hyp  = b["hyp_rp"]  == g["hyp_rp"]
    print(f"\n--- idx {idx} ---")
    print(f"  type:   gemini={b['type']}  gold={g['type']}  match={same_type}")
    print(f"  prem_rp match: {same_prem}")
    print(f"  hyp_rp  match: {same_hyp}")
    if not (same_type and same_prem and same_hyp):
        print(f"  prem_es:        {b['prem_es']}")
        print(f"  hyp_es:         {b['hyp_es']}")
        print(f"  prem_rp gemini: {b['prem_rp']}")
        print(f"  prem_rp gold:   {g['prem_rp']}")
        print(f"  hyp_rp  gemini: {b['hyp_rp']}")
        print(f"  hyp_rp  gold:   {g['hyp_rp']}")
    else:
        print("  -> COINCIDE exactamente")
