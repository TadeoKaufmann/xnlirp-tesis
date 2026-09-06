"""
Reconstruye el dataset QA con negativas más difíciles usando similitud TF-IDF.

Para cada positivo, en vez de negativas random, selecciona las 4 oraciones del cuento
con mayor similitud TF-IDF coseno respecto al positivo (excluyendo ±MIN_DIST posiciones).
Esto fuerza que las negativas compartan vocabulario con el positivo y con la pregunta,
eliminando el atajo de "descarta por off-topic".

Input:  qa/data/qa_final_{train,dev,test}.jsonl
Output: qa/data/qa_hard_tfidf_{train,dev,test}.jsonl

Uso:
  python qa/scripts/build_hard_negatives.py
  python qa/scripts/build_hard_negatives.py --min-dist 2 --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR  = REPO_ROOT / "qa" / "data"

NEGATIVES_PER_POS = 4


def select_negatives_tfidf(
    sentences: dict[int, str],
    target_idx: int,
    n: int = 4,
    min_dist: int = 2,
) -> list[int]:
    """
    Dado un diccionario {idx: oración}, devuelve los n índices más similares
    al target por TF-IDF, excluyendo posiciones a distancia < min_dist.
    """
    candidate_idxs = sorted(
        idx for idx in sentences if abs(idx - target_idx) >= min_dist
    )
    if not candidate_idxs:
        candidate_idxs = [idx for idx in sentences if idx != target_idx]
    if not candidate_idxs:
        return []

    corpus = [sentences[i] for i in candidate_idxs]
    target_text = sentences[target_idx]

    # TF-IDF sobre las candidatas + el target
    vec = TfidfVectorizer(min_df=1, sublinear_tf=True)
    try:
        mat = vec.fit_transform(corpus + [target_text])
    except ValueError:
        # Corpus vacío o todos tokens stopwords
        return candidate_idxs[:n]

    sims = cosine_similarity(mat[-1:], mat[:-1])[0]
    top_indices = np.argsort(sims)[::-1][:n]
    return [candidate_idxs[i] for i in top_indices]


def rebuild_split(rows: list[dict], min_dist: int) -> list[dict]:
    """
    Recibe instancias de un split (positivos + negativos mezclados).
    Devuelve instancias con las negativas reemplazadas por TF-IDF.
    """
    # Agrupar por cuento para construir pool de oraciones por cuento
    story_sentences: dict[str, dict[int, str]] = defaultdict(dict)
    for r in rows:
        story_sentences[r["story"]][r["unit_idx"]] = r["unit"]

    # Agrupar por (story, answer_unit_idx) para procesar grupo a grupo
    groups: dict[tuple, dict] = {}
    for r in rows:
        key = (r["story"], r["answer_unit_idx"])
        if key not in groups:
            groups[key] = {"pos": None, "old_negs": [], "meta": r}
        if r["label"] == 1:
            groups[key]["pos"] = r
        else:
            groups[key]["old_negs"].append(r)

    out: list[dict] = []
    skipped = 0
    tfidf_used = 0
    fallback_used = 0

    for key, g in groups.items():
        if g["pos"] is None:
            skipped += 1
            continue

        pos_row = g["pos"]
        story   = pos_row["story"]
        target_idx = pos_row["answer_unit_idx"]
        sentences  = story_sentences[story]

        # Seleccionar nuevas negativas por TF-IDF
        neg_idxs = select_negatives_tfidf(sentences, target_idx, n=NEGATIVES_PER_POS, min_dist=min_dist)

        if len(neg_idxs) < NEGATIVES_PER_POS:
            # Fallback: completar con los índices más lejanos disponibles
            existing = set(neg_idxs)
            extras = sorted(
                (idx for idx in sentences if idx != target_idx and idx not in existing),
                key=lambda i: -abs(i - target_idx),
            )
            neg_idxs += extras[: NEGATIVES_PER_POS - len(neg_idxs)]
            fallback_used += 1
        else:
            tfidf_used += 1

        # Emitir positivo
        out.append(pos_row)

        # Emitir nuevas negativas (reusar campos del positivo excepto unit/unit_idx/label/id)
        for j, neg_idx in enumerate(neg_idxs[:NEGATIVES_PER_POS]):
            neg = {**pos_row}
            neg["unit_idx"] = neg_idx
            neg["unit"]     = sentences[neg_idx]
            neg["label"]    = 0
            neg["id"]       = f"{pos_row['id'].replace('__pos', '')}__hn{j}"
            out.append(neg)

    print(f"  grupos procesados: {len(groups) - skipped}  |  tfidf={tfidf_used}  fallback={fallback_used}  sin_pos={skipped}")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--min-dist", type=int, default=2,
                    help="Distancia mínima (en posición) entre positivo y negativa (default: 2)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    for split in ("train", "dev", "test"):
        src = DATA_DIR / f"qa_final_{split}.jsonl"
        if not src.exists():
            print(f"[skip] {src.name} no existe")
            continue

        rows = [json.loads(l) for l in src.read_text(encoding="utf-8").splitlines() if l.strip()]
        print(f"\n[{split}] {len(rows)} instancias de entrada")

        new_rows = rebuild_split(rows, min_dist=args.min_dist)

        pos_out = sum(1 for r in new_rows if r["label"] == 1)
        neg_out = sum(1 for r in new_rows if r["label"] == 0)
        print(f"  salida: {len(new_rows)} instancias ({pos_out} pos + {neg_out} neg)")

        if not args.dry_run:
            dst = DATA_DIR / f"qa_hard_tfidf_{split}.jsonl"
            with dst.open("w", encoding="utf-8") as f:
                for r in new_rows:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
            print(f"  -> {dst.name}")

    if args.dry_run:
        print("\n[dry-run] no se escribió nada")


if __name__ == "__main__":
    main()
