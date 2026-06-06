"""
Genera un lote de preguntas QA para el dataset de cuentos rioplatenses.

Uso:
  python qa/scripts/generate_batch.py --round round_002 --n 100 --prompt-version v2
  python qa/scripts/generate_batch.py --dry-run
  python qa/scripts/generate_batch.py --round round_002 --n 100 --stories "Axolotl,Wakefield"
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
from tqdm import tqdm

# qa/scripts/ → qa/ → repo root
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
QA_ROOT = REPO_ROOT / "qa"
TEXTS_DIR = REPO_ROOT / "Referencias" / "texts"
PROMPTS_DIR = QA_ROOT / "prompts" / "generation"
ROUNDS_DIR = QA_ROOT / "rounds"
CACHE_PATH = QA_ROOT / "data" / "_qa_questions_raw.jsonl"

EXCLUDE_STORIES = {"Test"}
MIN_WORDS = 8
MAX_WORDS = 80
MIN_NEG_DISTANCE = 3
NEGATIVES_PER_POSITIVE = 4
INFERENTIAL_RATIO = 0.15
MODEL = "gemini-2.5-flash"
TEMPERATURE = 0.7
BATCH_POLL_INTERVAL = 10
MAX_RETRIES = 3
RANDOM_SEED = 42

ABBREVIATIONS = {
    "sr", "sra", "srta", "dr", "dra", "lic", "ing", "prof", "gral",
    "sres", "ud", "uds", "vs", "etc", "av", "atte", "depto", "dpto",
    "no", "cap", "pag", "pág", "fig", "vol", "ed", "núm", "nro",
}

SENT_END_RE = re.compile(
    r'(?<=[\.\!\?…])["\»"\']?\s+(?=[«"\'\¿\¡A-ZÁÉÍÓÚÑ])',
    re.VERBOSE,
)


def slugify(name: str) -> str:
    s = name.lower()
    for a, b in [("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u"),("ü","u"),("ñ","n")]:
        s = s.replace(a, b)
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s or "story"


def load_story_text(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    raw = raw.replace("﻿", "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"^\d+\t", "", ln).strip() for ln in raw.split("\n")]
    lines = [ln for ln in lines if ln]
    fixed = [ln if ln[-1] in ".!?…»\")" else ln + "." for ln in lines]
    return " ".join(fixed)


def split_sentences(text: str) -> list[str]:
    parts = SENT_END_RE.split(text)
    parts = [p.strip() for p in parts if p.strip()]
    merged: list[str] = []
    for p in parts:
        if merged:
            tail = re.search(r"(\w+)\.$", merged[-1])
            if tail and tail.group(1).lower() in ABBREVIATIONS:
                merged[-1] = merged[-1] + " " + p
                continue
        merged.append(p)
    return merged


def is_good_target(sentence: str) -> bool:
    n = len(sentence.split())
    if not (MIN_WORDS <= n <= MAX_WORDS):
        return False
    if re.fullmatch(r'[«""].{0,30}[»""][\.\!\?…]?', sentence):
        return False
    return True


def load_all_stories(story_filter: list[str] | None = None) -> list[tuple[str, list[str]]]:
    stories = []
    for path in sorted(TEXTS_DIR.iterdir()):
        if not path.is_file() or path.name in EXCLUDE_STORIES:
            continue
        if story_filter and path.name not in story_filter:
            continue
        sentences = split_sentences(load_story_text(path))
        stories.append((path.name, sentences))
    return stories


def load_cache() -> set[tuple[str, int]]:
    if not CACHE_PATH.exists():
        return set()
    done = set()
    with CACHE_PATH.open(encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
                done.add((r["story"], int(r["unit_idx"])))
            except Exception:
                pass
    return done


def append_cache(row: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CACHE_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_prompt(version: str) -> str:
    path = PROMPTS_DIR / f"{version}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Prompt no encontrado: {path}")
    return path.read_text(encoding="utf-8")


def build_prompt(template: str, title: str, sentences: list[str], i: int, tipo: str) -> str:
    before = sentences[max(0, i-2):i]
    after = sentences[i+1:i+3]
    return template.format(
        tipo_pregunta=tipo,
        title=title,
        context_before="\n".join(f"- {s}" for s in before) if before else "(inicio del cuento)",
        target=sentences[i],
        context_after="\n".join(f"- {s}" for s in after) if after else "(fin del cuento)",
    )


def get_gemini_client():
    load_dotenv(REPO_ROOT / ".env")
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise SystemExit("GOOGLE_API_KEY no está en .env")
    from google import genai
    return genai.Client(api_key=api_key)


def call_gemini_batch(client, prompts: list[str]) -> list[str | None]:
    from google.genai import types as genai_types
    cfg = genai_types.GenerateContentConfig(temperature=TEMPERATURE)
    inline_requests = [
        genai_types.InlinedRequest(contents=p, config=cfg)
        for p in prompts
    ]
    job = client.batches.create(
        model=f"models/{MODEL}",
        src=inline_requests,
        config={"display_name": f"qa-gen-{int(time.time())}"},
    )
    print(f"[batch] job: {job.name}")
    completed = {"JOB_STATE_SUCCEEDED", "JOB_STATE_FAILED", "JOB_STATE_CANCELLED", "JOB_STATE_EXPIRED"}
    while job.state.name not in completed:
        print(f"[batch] {job.state.name} ...")
        time.sleep(BATCH_POLL_INTERVAL)
        job = client.batches.get(name=job.name)
    if job.state.name != "JOB_STATE_SUCCEEDED":
        raise RuntimeError(f"Batch falló: {job.state.name} — {getattr(job, 'error', '')}")
    results = []
    for r in job.dest.inlined_responses:
        try:
            text = (r.response.text or "").strip()
            results.append(text if text else None)
        except Exception:
            results.append(None)
    return results


def parse_question(text: str) -> tuple[str | None, str | None]:
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None, "no JSON"
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError as e:
        return None, str(e)
    q = obj.get("question")
    return (q.strip() if isinstance(q, str) else None), obj.get("reason")


def build_instances(title: str, sentences: list[str], questions: list[dict], rng: random.Random) -> list[dict]:
    slug = slugify(title)
    candidate_idxs = [i for i, s in enumerate(sentences) if is_good_target(s)]
    instances = []
    for q_idx, qrow in enumerate(questions):
        if not qrow.get("question"):
            continue
        target_idx = qrow["unit_idx"]
        question = qrow["question"]
        qtype = qrow["question_type"]

        instances.append({
            "id": f"{slug}__s{target_idx}__q{q_idx}__pos",
            "story": title, "unit_idx": target_idx,
            "unit": sentences[target_idx], "question": question,
            "label": 1, "question_type": qtype, "answer_unit_idx": target_idx,
            "split": qrow.get("split", "train"),
        })

        far_pool = [i for i in candidate_idxs if abs(i - target_idx) >= MIN_NEG_DISTANCE]
        if len(far_pool) < NEGATIVES_PER_POSITIVE:
            far_pool = [i for i in candidate_idxs if i != target_idx]
        if not far_pool:
            continue
        for j, neg_idx in enumerate(rng.sample(far_pool, min(NEGATIVES_PER_POSITIVE, len(far_pool)))):
            instances.append({
                "id": f"{slug}__s{target_idx}__q{q_idx}__neg{j}",
                "story": title, "unit_idx": neg_idx,
                "unit": sentences[neg_idx], "question": question,
                "label": 0, "question_type": qtype, "answer_unit_idx": target_idx,
                "split": qrow.get("split", "train"),
            })
    return instances


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--round", default=None, help="Nombre del round destino, ej. round_003")
    ap.add_argument("--n", type=int, default=None, help="Total de preguntas a generar (distribuidas proporcionalmente). None = todas.")
    ap.add_argument("--prompt-version", default="v1", dest="prompt_version")
    ap.add_argument("--stories", default=None, help="Cuentos a incluir, separados por coma")
    ap.add_argument("--split", default="train", choices=["train", "dev", "test"], help="Split al que pertenecen estas instancias")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--seed", type=int, default=RANDOM_SEED)
    args = ap.parse_args()

    rng = random.Random(args.seed)

    story_filter = [s.strip() for s in args.stories.split(",")] if args.stories else None
    stories = load_all_stories(story_filter)
    print(f"[load] {len(stories)} cuentos, {sum(len(s) for _,s in stories)} oraciones totales")

    prompt_template = load_prompt(args.prompt_version)
    cached = load_cache()
    print(f"[cache] {len(cached)} preguntas previas en cache (se saltean)")

    # Armar pool de tareas por cuento
    pool_by_story: dict[str, list[tuple[str, int, str, str]]] = {}
    for title, sentences in stories:
        for i, s in enumerate(sentences):
            if not is_good_target(s):
                continue
            if (title, i) in cached:
                continue
            qtype = "inferencial" if rng.random() < INFERENTIAL_RATIO else "factual"
            pool_by_story.setdefault(title, []).append((title, i, s, qtype))

    total_available = sum(len(v) for v in pool_by_story.values())

    # Distribución proporcional por cuento
    if args.n is None or args.n >= total_available:
        tasks = [t for v in pool_by_story.values() for t in v]
    else:
        import math
        tasks = []
        for title, pool in pool_by_story.items():
            cuota = math.ceil(args.n * len(pool) / total_available)
            tasks.extend(pool[:cuota])
        tasks = tasks[:args.n]

    print(f"[plan] {len(tasks)} oraciones target ({args.split}) — dist: { {t: sum(1 for x in tasks if x[0]==t) for t in pool_by_story} }")

    if args.dry_run:
        est_pos = len(tasks)
        print(f"[dry-run] estimación: {est_pos} positivos + {est_pos * NEGATIVES_PER_POSITIVE} negativos = {est_pos * (1 + NEGATIVES_PER_POSITIVE)} instancias")
        return

    # Determinar round destino
    if args.round:
        round_dir = ROUNDS_DIR / args.round
    else:
        existing = sorted([d for d in ROUNDS_DIR.iterdir() if d.is_dir()]) if ROUNDS_DIR.exists() else []
        n = len(existing) + 1
        round_dir = ROUNDS_DIR / f"round_{n:03d}"
    round_dir.mkdir(parents=True, exist_ok=True)

    # Guardar snapshot del prompt usado
    (round_dir / "prompt_snapshot.txt").write_text(prompt_template, encoding="utf-8")

    client = get_gemini_client()
    title_to_sents = {t: s for t, s in stories}
    by_story: dict[str, list[dict]] = {}

    n_skip = n_fail = 0
    all_qrows: list[dict] = []

    print(f"[batch] enviando {len(tasks)} prompts a Gemini Batch API ...")
    prompts = [build_prompt(prompt_template, title, title_to_sents[title], i, qtype)
               for title, i, sent, qtype in tasks]
    raw_results = call_gemini_batch(client, prompts)

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
               "question_type": qtype, "split": args.split, "skip_reason": reason}
        if question.upper() == "SKIP":
            n_skip += 1
        append_cache(row)
        all_qrows.append(row)
        by_story.setdefault(title, []).append(row)

    print(f"[gen] OK={sum(1 for r in all_qrows if r['question'])} SKIP={n_skip} FAIL={n_fail}")

    # Ensamblar instancias
    all_instances = []
    for title, qrows in by_story.items():
        all_instances.extend(build_instances(title, title_to_sents[title], qrows, rng))

    out_path = round_dir / "generated.jsonl"
    write_jsonl(out_path, all_instances)
    print(f"[out] {len(all_instances)} instancias → {out_path}")
    print(f"      pos={sum(1 for r in all_instances if r['label']==1)}  neg={sum(1 for r in all_instances if r['label']==0)}")


if __name__ == "__main__":
    main()
