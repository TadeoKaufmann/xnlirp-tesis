"""
Fase 2 - complejiza el dataset QA sobre el subconjunto 'easy' identificado en
qa/data/difficulty_report.json (Fase 1, ver analyze_difficulty.py).

Para cada grupo (story, answer_unit_idx) flaggeado 'easy' en su split:
  1. Reemplaza sus 4 negativas por las TF-IDF top-4 del cuento (mismo criterio
     que build_hard_negatives.py).
  2. Regenera la pregunta via Gemini Batch API usando las nuevas negativas
     duras como contexto (mismo patron que _regen_questions.py), pidiendo
     mas preguntas inferenciales.

Los grupos 'hard'/'medium' quedan intactos.

Uso:
  python qa/scripts/harden_dataset.py --split test --dry-run
  python qa/scripts/harden_dataset.py --split test
  python qa/scripts/harden_dataset.py --split train dev test
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_hard_negatives as bhn  # noqa: E402
import build_hard_negatives_embeddings as embed_mod  # noqa: E402
import _regen_questions as regen  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
QA_DATA_DIR = REPO_ROOT / "qa" / "data"
SPLIT_DIR = REPO_ROOT / "experimentos" / "split_QA_50_50_pos_neg"
TEXTS_DIR = REPO_ROOT / "Referencias" / "texts"

RANDOM_SEED = 42
INFERENTIAL_RATIO = 0.5  # mas alto que el 0.15 original: estamos complejizando a proposito

HARDEN_PROMPT_PATH = REPO_ROOT / "qa" / "prompts" / "hardening" / "v1.txt"
HARDEN_PROMPT = HARDEN_PROMPT_PATH.read_text(encoding="utf-8")


def load_split(split: str) -> list[dict]:
    """Prefiere qa_{split}_v2.jsonl si ya existe (acumula sobre hardening previo
    de otro bucket); si no, arranca del original."""
    v2_path = SPLIT_DIR / f"qa_{split}_v2.jsonl"
    path = v2_path if v2_path.exists() else SPLIT_DIR / f"qa_{split}.jsonl"
    print(f"[load_split] leyendo {path.name}")
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def load_easy_keys(split: str, bucket: str = "easy") -> set[tuple]:
    report = json.loads((QA_DATA_DIR / "difficulty_report.json").read_text(encoding="utf-8"))
    keys = set()
    for group_id in report[split][bucket]:
        story, idx = group_id.rsplit("||", 1)
        keys.add((story, int(idx)))
    return keys


def group_rows(rows: list[dict]) -> dict[tuple, dict]:
    groups: dict[tuple, dict] = {}
    for r in rows:
        key = (r["story"], r["answer_unit_idx"])
        if key not in groups:
            groups[key] = {"pos": None, "negs": []}
        if r["label"] == 1:
            groups[key]["pos"] = r
        else:
            groups[key]["negs"].append(r)
    return groups


def harden_negatives(groups: dict[tuple, dict], easy_keys: set[tuple], min_dist: int = 2,
                      max_sim: float = 0.55) -> dict[str, int]:
    """Reemplaza in-place las negativas de los grupos 'easy' por embeddings
    (metodo final decidido: gana a TF-IDF en calidad y dificultad con el
    prompt v1 refinado). Techo de similitud max_sim para evitar casi-duplicados."""
    story_sentences: dict[str, dict[int, str]] = defaultdict(dict)
    for (story, _), g in groups.items():
        if g["pos"]:
            story_sentences[story][g["pos"]["unit_idx"]] = g["pos"]["unit"]
        for n in g["negs"]:
            story_sentences[story][n["unit_idx"]] = n["unit"]

    all_sentences = [s for story in {k[0] for k in easy_keys if k in groups}
                      for s in story_sentences[story].values()]
    client = embed_mod.get_openai_client()
    cache = embed_mod.load_cache()
    embeds = embed_mod.embed_sentences(client, all_sentences, cache)

    tfidf_used = fallback_used = skipped = 0
    for key in easy_keys:
        g = groups.get(key)
        if g is None or g["pos"] is None:
            skipped += 1
            continue
        story, target_idx = key
        sentences = story_sentences[story]
        neg_idxs = embed_mod.select_negatives_embedding(sentences, target_idx, embeds,
                                                          n=len(g["negs"]) or 4, min_dist=min_dist, max_sim=max_sim)
        if len(neg_idxs) < len(g["negs"]):
            existing = set(neg_idxs)
            extras = sorted(
                (i for i in sentences if i != target_idx and i not in existing),
                key=lambda i: -abs(i - target_idx),
            )
            neg_idxs += extras[: len(g["negs"]) - len(neg_idxs)]
            fallback_used += 1
        else:
            tfidf_used += 1

        pos_row = g["pos"]
        new_negs = []
        for j, neg_idx in enumerate(neg_idxs[: len(g["negs"]) or 4]):
            base = g["negs"][j] if j < len(g["negs"]) else dict(pos_row)
            neg = {**base}
            neg["unit_idx"] = neg_idx
            neg["unit"] = sentences[neg_idx]
            neg["label"] = 0
            neg["id"] = f"{pos_row['id'].replace('__pos', '')}__hn{j}"
            new_negs.append(neg)
        g["negs"] = new_negs

    return {"tfidf": tfidf_used, "fallback": fallback_used, "skipped": skipped}


def build_prompt(task_id: int, g: dict, sents: list[str]) -> str | None:
    pos = g["pos"]
    target_idx = pos["unit_idx"]
    if target_idx >= len(sents) or sents[target_idx].strip() != pos["unit"].strip():
        # unit_idx no matchea el texto actual de Referencias/texts -> no armar prompt
        return None
    before = sents[max(0, target_idx - 1):target_idx]
    after = sents[target_idx + 1:target_idx + 2]
    negs_text = "\n".join(f"  {i+1}. {n['unit']}" for i, n in enumerate(g["negs"]))
    tipo = "inferencial" if random.random() < INFERENTIAL_RATIO else "factual"
    return HARDEN_PROMPT.format(
        task_id=task_id,
        n_neg=len(g["negs"]),
        tipo_pregunta=tipo,
        old_question=pos["question"],
        title=g["pos"]["story"],
        context_before="\n".join(f"- {s}" for s in before) if before else "(inicio del cuento)",
        target=sents[target_idx],
        context_after="\n".join(f"- {s}" for s in after) if after else "(fin del cuento)",
        negatives=negs_text,
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--split", nargs="+", choices=["train", "dev", "test"], required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=None,
                     help="Limitar a N grupos 'easy' por split (para pruebas chicas antes de correr todo)")
    ap.add_argument("--seed", type=int, default=RANDOM_SEED)
    ap.add_argument("--bucket", default="easy", help="Bucket del difficulty_report a endurecer (default: easy)")
    ap.add_argument("--resume-batch-id", default=None, help="Retomar un batch de Gemini ya enviado (batches/...) en vez de mandar uno nuevo")
    args = ap.parse_args()

    random.seed(args.seed)
    story_texts = regen.load_all_story_sentences()

    for split in args.split:
        print(f"\n=== {split} ===")
        rows = load_split(split)
        easy_keys = load_easy_keys(split, args.bucket)
        groups = group_rows(rows)
        print(f"[load] {len(groups)} grupos totales, {len(easy_keys)} flaggeados 'easy'")

        if args.limit and len(easy_keys) > args.limit:
            limit_rng = random.Random(args.seed + 7)
            easy_keys = set(limit_rng.sample(sorted(easy_keys), args.limit))
            print(f"[limit] recortado a {len(easy_keys)} grupos 'easy' para esta corrida")

        neg_stats = harden_negatives(groups, easy_keys)
        print(f"[negativas] tfidf={neg_stats['tfidf']} fallback={neg_stats['fallback']} skipped={neg_stats['skipped']}")

        tasks = []
        skipped_no_text = 0
        for task_id, key in enumerate(sorted(easy_keys)):
            g = groups.get(key)
            if g is None or g["pos"] is None:
                continue
            sents = story_texts.get(g["pos"]["story"])
            if sents is None:
                skipped_no_text += 1
                continue
            prompt = build_prompt(task_id, g, sents)
            if prompt is None:
                skipped_no_text += 1
                continue
            tasks.append((task_id, key, prompt))

        if skipped_no_text:
            print(f"[warn] {skipped_no_text} grupos sin texto/idx matcheable en Referencias/texts — negativas TF-IDF quedan igual, pregunta no se toca")

        old_questions = {key: groups[key]["pos"]["question"] for _, key, _ in tasks}

        if args.dry_run:
            print(f"[dry-run] {len(tasks)} prompts armados para Gemini Batch API (split={split})")
            continue

        if not tasks:
            print("[info] nada para regenerar en este split")
            continue

        client = regen.get_gemini_client()
        if args.resume_batch_id:
            print(f"[batch] retomando job existente: {args.resume_batch_id}")
            job = client.batches.get(name=args.resume_batch_id)
            if job.state.name != "JOB_STATE_SUCCEEDED":
                raise SystemExit(f"El batch {args.resume_batch_id} no esta SUCCEEDED (estado: {job.state.name})")
            raw_results = []
            for r in job.dest.inlined_responses:
                try:
                    text = (r.response.text or "").strip()
                    raw_results.append(text if text else None)
                except Exception:
                    raw_results.append(None)
        else:
            print(f"[batch] enviando {len(tasks)} prompts a Gemini Batch API ...")
            raw_results = regen.call_gemini_batch(client, [t[2] for t in tasks])

        id_to_raw: dict[int, str] = {}
        for raw in raw_results:
            if raw is None:
                continue
            m = re.search(r'"id"\s*:\s*(\d+)', raw)
            if m:
                id_to_raw[int(m.group(1))] = raw

        n_ok = n_skip = n_fail = 0
        for task_id, key, _ in tasks:
            raw = id_to_raw.get(task_id)
            if raw is None:
                n_fail += 1
                continue
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            if not m:
                n_fail += 1
                continue
            try:
                obj = json.loads(m.group(0))
            except json.JSONDecodeError:
                n_fail += 1
                continue
            q = obj.get("question")
            if not isinstance(q, str) or q.strip().upper() == "SKIP":
                n_skip += 1
                continue
            qtype = obj.get("question_type", "factual")
            if qtype not in ("factual", "inferencial"):
                qtype = "factual"

            g = groups[key]
            g["pos"]["question"] = q.strip()
            g["pos"]["question_type"] = qtype
            for n in g["negs"]:
                n["question"] = q.strip()
                n["question_type"] = qtype
            n_ok += 1

            if args.limit:
                old_q = old_questions.get(key, "?")
                print(f"  [{key[0]} / q{key[1]}]")
                print(f"    antes:   {old_q}")
                print(f"    despues: {q.strip()}  ({qtype})")

        print(f"[regen] OK={n_ok} SKIP={n_skip} FAIL={n_fail}")

        out_rows: list[dict] = []
        for g in groups.values():
            if g["pos"]:
                out_rows.append(g["pos"])
            out_rows.extend(g["negs"])

        suffix = "_sample" if args.limit else ""
        out_path = SPLIT_DIR / f"qa_{split}_v2{suffix}.jsonl"
        with out_path.open("w", encoding="utf-8") as f:
            for r in out_rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"[out] {len(out_rows)} instancias -> {out_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
