import re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TEXTS_DIR = Path(__file__).resolve().parent.parent.parent / "Referencias" / "texts"
MIN_WORDS, MAX_WORDS = 8, 80
MIN_NEG_DISTANCE = 3
NEGATIVES_PER_POSITIVE = 4
ABBREVIATIONS = {"sr","sra","srta","dr","dra","lic","ing","prof","gral","sres","ud","uds",
                 "vs","etc","av","atte","depto","dpto","no","cap","pag","pag","fig","vol","ed","num","nro"}
SENT_END_RE = re.compile(r'(?<=[\.\!\?…])["\»"\']?\s+(?=[«"\'\¿\¡A-ZÁÉÍÓÚÑ])', re.VERBOSE)

def load_story(path):
    raw = path.read_text(encoding="utf-8", errors="replace").replace("﻿","").replace("\r\n","\n").replace("\r","\n")
    lines = [re.sub(r"^\d+\t","", ln).strip() for ln in raw.split("\n") if ln.strip()]
    fixed = [ln if ln[-1] in ".!?…»\")" else ln+"." for ln in lines]
    return " ".join(fixed)

def split_sentences(text):
    parts = SENT_END_RE.split(text)
    parts = [p.strip() for p in parts if p.strip()]
    merged = []
    for p in parts:
        if merged:
            tail = re.search(r"(\w+)\.$", merged[-1])
            if tail and tail.group(1).lower() in ABBREVIATIONS:
                merged[-1] = merged[-1] + " " + p
                continue
        merged.append(p)
    return merged

def is_good(s):
    n = len(s.split())
    if not (MIN_WORDS <= n <= MAX_WORDS): return False
    if re.fullmatch(r'[«""].{0,30}[»""][\.\!\?…]?', s): return False
    return True

rows = []
for path in sorted(TEXTS_DIR.iterdir()):
    if not path.is_file(): continue
    sents = split_sentences(load_story(path))
    candidate_idxs = [i for i,s in enumerate(sents) if is_good(s)]
    usable = sum(
        1 for i,s in enumerate(sents)
        if is_good(s) and len([j for j in candidate_idxs if abs(j-i) >= MIN_NEG_DISTANCE]) >= NEGATIVES_PER_POSITIVE
    )
    rows.append((path.name, len(sents), len(candidate_idxs), usable, usable * 5))

total_sents = sum(r[1] for r in rows)
total_valid = sum(r[2] for r in rows)
total_usable = sum(r[3] for r in rows)
total_inst = sum(r[4] for r in rows)

print(f"{'Cuento':<45} {'oracs':>5} {'valid':>5} {'usable':>6} {'inst':>6}")
print("-" * 72)
for name, t, v, u, inst in rows:
    print(f"{name:<45} {t:>5} {v:>5} {u:>6} {inst:>6}")
print("-" * 72)
print(f"{'TOTAL':<45} {total_sents:>5} {total_valid:>5} {total_usable:>6} {total_inst:>6}")
print(f"\nInstancias potenciales: {total_inst:,}  (pos={total_usable:,}  neg={total_usable*4:,})")
