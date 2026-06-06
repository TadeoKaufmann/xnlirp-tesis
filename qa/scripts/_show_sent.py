import re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TEXTS_DIR = Path(__file__).resolve().parent.parent.parent / "Referencias" / "texts"
SENT_END_RE = re.compile(r'(?<=[\.\!\?…])["\»"\']?\s+(?=[«"\'\¿\¡A-ZÁÉÍÓÚÑ])')
ABBREVIATIONS = {"sr","sra","dr","dra","no","etc","av"}

def split_sentences(text):
    parts = SENT_END_RE.split(text)
    merged = []
    for p in [x.strip() for x in parts if x.strip()]:
        if merged:
            tail = re.search(r"(\w+)\.$", merged[-1])
            if tail and tail.group(1).lower() in ABBREVIATIONS:
                merged[-1] = merged[-1] + " " + p
                continue
        merged.append(p)
    return merged

story = sys.argv[1] if len(sys.argv) > 1 else "La gallina degollada"
idx = int(sys.argv[2]) if len(sys.argv) > 2 else 15
path = TEXTS_DIR / story
raw = path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
lines = [re.sub(r"^\d+\t", "", ln).strip() for ln in raw.split("\n") if ln.strip()]
fixed = [ln if ln[-1] in ".!?…»\")" else ln + "." for ln in lines]
sents = split_sentences(" ".join(fixed))
print(sents[idx])
