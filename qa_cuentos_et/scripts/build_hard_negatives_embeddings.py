"""
Variante de build_hard_negatives.py que usa embeddings de OpenAI
(text-embedding-3-small) en vez de TF-IDF para elegir negativas duras.

TF-IDF solo capta solapamiento de palabras; embeddings captan similitud
semantica real (sinonimos, parafraseo), dando negativas conceptualmente
cercanas aunque no compartan vocabulario con la oracion correcta.

Uso:
  python qa/scripts/build_hard_negatives_embeddings.py --split test --groups-file qa/data/difficulty_report.json --bucket medium
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SPLIT_DIR = REPO_ROOT / "experimentos" / "split_QA_50_50_pos_neg"
QA_DATA_DIR = REPO_ROOT / "qa" / "data"
CACHE_PATH = QA_DATA_DIR / "_embeddings_cache.json"

EMBED_MODEL = "text-embedding-3-small"
NEGATIVES_PER_POS = 4


def get_openai_client():
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY no esta en .env")
    import openai
    return openai.OpenAI(api_key=api_key)


def load_cache() -> dict:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    return {}


def save_cache(cache: dict):
    CACHE_PATH.write_text(json.dumps(cache), encoding="utf-8")


def embed_sentences(client, sentences: list[str], cache: dict) -> dict[str, list[float]]:
    """Devuelve {sentence: embedding}, usando cache persistente para no re-pagar."""
    to_fetch = [s for s in set(sentences) if s not in cache]
    if to_fetch:
        print(f"  [embeddings] pidiendo {len(to_fetch)} nuevas (cache tenia {len(cache)})")
        BATCH = 100
        for i in range(0, len(to_fetch), BATCH):
            chunk = to_fetch[i:i+BATCH]
            resp = client.embeddings.create(model=EMBED_MODEL, input=chunk)
            for s, d in zip(chunk, resp.data):
                cache[s] = d.embedding
        save_cache(cache)
    return {s: cache[s] for s in sentences}


def cosine_sim_matrix(vecs: np.ndarray) -> np.ndarray:
    norm = vecs / np.linalg.norm(vecs, axis=1, keepdims=True)
    return norm @ norm.T


def select_negatives_embedding(sentences: dict[int, str], target_idx: int, embeds: dict[str, list[float]],
                                n: int = 4, min_dist: int = 1, max_sim: float = 1.0) -> list[int]:
    """max_sim: techo de similitud coseno. Candidatas por ENCIMA de este valor se
    descartan por ser casi-duplicados semanticos de la respuesta correcta (riesgo
    de que la negativa termine siendo tambien una respuesta valida)."""
    candidate_idxs = sorted(idx for idx in sentences if abs(idx - target_idx) >= min_dist)
    if not candidate_idxs:
        candidate_idxs = [idx for idx in sentences if idx != target_idx]
    if not candidate_idxs:
        return []

    target_vec = np.array(embeds[sentences[target_idx]])
    cand_vecs = np.array([embeds[sentences[i]] for i in candidate_idxs])

    target_norm = target_vec / np.linalg.norm(target_vec)
    cand_norm = cand_vecs / np.linalg.norm(cand_vecs, axis=1, keepdims=True)
    sims = cand_norm @ target_norm

    order = np.argsort(sims)[::-1]
    filtered = [i for i in order if sims[i] <= max_sim]
    chosen = filtered[:n] if len(filtered) >= n else filtered + [i for i in order if i not in filtered][:n - len(filtered)]
    return [candidate_idxs[i] for i in chosen]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--split", required=True, choices=["train", "dev", "test"])
    ap.add_argument("--bucket", default="medium", help="Bucket del difficulty_report a endurecer (default: medium)")
    ap.add_argument("--min-dist", type=int, default=1)
    ap.add_argument("--max-sim", type=float, default=1.0,
                     help="Techo de similitud coseno; candidatas por encima se descartan (casi-duplicados)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    report = json.loads((QA_DATA_DIR / "difficulty_report.json").read_text(encoding="utf-8"))
    target_keys = set()
    for group_id in report[args.split][args.bucket]:
        story, idx = group_id.rsplit("||", 1)
        target_keys.add((story, int(idx)))
    print(f"[load] {len(target_keys)} grupos en bucket '{args.bucket}' de {args.split}")

    v2_path = SPLIT_DIR / f"qa_{args.split}_v2.jsonl"
    src_path = v2_path if v2_path.exists() else SPLIT_DIR / f"qa_{args.split}.jsonl"
    print(f"[src] leyendo {src_path.name}")
    rows = [json.loads(l) for l in src_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    story_sentences: dict[str, dict[int, str]] = defaultdict(dict)
    groups: dict[tuple, dict] = {}
    for r in rows:
        key = (r["story"], r["answer_unit_idx"])
        story_sentences[r["story"]][r["unit_idx"]] = r["unit"]
        if key not in groups:
            groups[key] = {"pos": None, "negs": []}
        if r["label"] == 1:
            groups[key]["pos"] = r
        else:
            groups[key]["negs"].append(r)

    target_keys = {k for k in target_keys if k in groups and groups[k]["pos"] is not None}
    print(f"[match] {len(target_keys)} grupos encontrados en qa_{args.split}.jsonl")

    if args.dry_run:
        print("[dry-run] no se llama a la API")
        return

    client = get_openai_client()
    cache = load_cache()

    all_sentences = [s for story in {k[0] for k in target_keys} for s in story_sentences[story].values()]
    embeds = embed_sentences(client, all_sentences, cache)

    n_updated = 0
    for key in target_keys:
        story, target_idx = key
        sentences = story_sentences[story]
        neg_idxs = select_negatives_embedding(sentences, target_idx, embeds, n=NEGATIVES_PER_POS, min_dist=args.min_dist, max_sim=args.max_sim)
        if len(neg_idxs) < NEGATIVES_PER_POS:
            existing = set(neg_idxs)
            extras = sorted((i for i in sentences if i != target_idx and i not in existing),
                             key=lambda i: -abs(i - target_idx))
            neg_idxs += extras[:NEGATIVES_PER_POS - len(neg_idxs)]

        g = groups[key]
        pos_row = g["pos"]
        new_negs = []
        for j, neg_idx in enumerate(neg_idxs[:NEGATIVES_PER_POS]):
            base = g["negs"][j] if j < len(g["negs"]) else dict(pos_row)
            neg = {**base}
            neg["unit_idx"] = neg_idx
            neg["unit"] = sentences[neg_idx]
            neg["label"] = 0
            neg["id"] = f"{pos_row['id'].replace('__pos', '')}__hn{j}"
            new_negs.append(neg)
        g["negs"] = new_negs
        n_updated += 1

    print(f"[negativas] {n_updated} grupos actualizados con embeddings")

    v2_path = SPLIT_DIR / f"qa_{args.split}_v2.jsonl"
    if v2_path.exists():
        existing_rows = [json.loads(l) for l in v2_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        existing_groups: dict[tuple, dict] = {}
        for r in existing_rows:
            k = (r["story"], r["answer_unit_idx"])
            if k not in existing_groups:
                existing_groups[k] = {"pos": None, "negs": []}
            if r["label"] == 1:
                existing_groups[k]["pos"] = r
            else:
                existing_groups[k]["negs"].append(r)
        for key in target_keys:
            existing_groups[key] = groups[key]
        out_rows = []
        for g in existing_groups.values():
            if g["pos"]:
                out_rows.append(g["pos"])
            out_rows.extend(g["negs"])
    else:
        out_rows = []
        for g in groups.values():
            if g["pos"]:
                out_rows.append(g["pos"])
            out_rows.extend(g["negs"])

    with v2_path.open("w", encoding="utf-8") as f:
        for r in out_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"[out] {len(out_rows)} filas -> {v2_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
