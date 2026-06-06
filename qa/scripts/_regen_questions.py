"""
Regenera preguntas para instancias no-clean de un round, mostrándole a Gemini
la positiva + las negativas actuales para que genere una pregunta discriminativa.

Para cada grupo no-clean, arma un prompt con: contexto + target + negativas + pool
de candidatos. Gemini devuelve una pregunta que distinga la positiva de las negativas,
y opcionalmente swapea una negativa problemática por una del pool.

Salida: generated_v3.jsonl con grupos clean originales + regenerados (sin los SKIP).

Uso:
  python qa/scripts/_regen_questions.py --round round_003
  python qa/scripts/_regen_questions.py --round round_003 --dry-run
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

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
QA_ROOT = REPO_ROOT / "qa"
TEXTS_DIR = REPO_ROOT / "Referencias" / "texts"
ROUNDS_DIR = QA_ROOT / "rounds"

MODEL = "gemini-2.5-flash"
TEMPERATURE = 0.7
BATCH_POLL_INTERVAL = 10
MIN_WORDS = 8
MAX_WORDS = 80
MIN_NEG_DISTANCE = 3
POOL_SIZE = 12
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

REGEN_PROMPT = """\
[ID:{task_id}]
Sos un anotador de datasets de comprensión lectora en español rioplatense (RP).

Tenés una ORACIÓN TARGET y {n_neg} ORACIONES NEGATIVAS del mismo cuento.
Tu tarea es generar una pregunta en español rioplatense tal que:
  1. La ORACIÓN TARGET la responde directamente, leyendo solo esa oración.
  2. Ninguna de las NEGATIVAS la responde.
  3. Reformulá con tus propias palabras. Intentá no superar 2 palabras exactas
     de la oración, pero si la claridad lo requiere podés usar alguna más.
     Preferí palabras que también aparezcan en alguna negativa. Si la oración
     tiene muchos detalles, elegí UNO como ancla — no preguntes sobre dos
     cosas a la vez (evitá "¿qué X y qué Y?").
  4. TEST: si alguien ve SOLO la oración target, sin ningún contexto antes ni
     después, ¿puede responder la pregunta? Si no, SKIP.

TÍTULO: {title}

CONTEXTO PREVIO:
{context_before}

>>> ORACIÓN TARGET:
{target}
<<<

CONTEXTO POSTERIOR:
{context_after}

ORACIONES NEGATIVAS (ninguna debe responder la pregunta):
{negatives}

POOL DE REEMPLAZOS (usá solo si una negativa resulta problemática):
{pool}

Devolvé SOLO el JSON, sin texto adicional. Incluí siempre el campo "id".

Si generás la pregunta sin problemas:
{{"id": {task_id}, "question": "..."}}

Si una negativa también respondería la pregunta, indicá cuál (número 1-{n_neg}) y
elegí su reemplazo exacto del pool:
{{"id": {task_id}, "question": "...", "swap": {{"neg_idx": <1-{n_neg}>, "replacement": "<oración exacta del pool>"}}}}

Si no podés generar una buena pregunta:
{{"id": {task_id}, "question": "SKIP", "reason": "..."}}
"""


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


def load_all_story_sentences() -> dict[str, list[str]]:
    stories = {}
    for path in sorted(TEXTS_DIR.iterdir()):
        if path.is_file():
            stories[path.name] = split_sentences(load_story_text(path))
    return stories


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
        config={"display_name": f"qa-regen-{int(time.time())}"},
    )
    print(f"[batch] job: {job.name}")
    completed = {"JOB_STATE_SUCCEEDED", "JOB_STATE_FAILED", "JOB_STATE_CANCELLED", "JOB_STATE_EXPIRED"}
    while job.state.name not in completed:
        print(f"[batch] {job.state.name} ...")
        time.sleep(BATCH_POLL_INTERVAL)
        job = client.batches.get(name=job.name)
    if job.state.name != "JOB_STATE_SUCCEEDED":
        raise RuntimeError(f"Batch falló: {job.state.name}")
    results = []
    for r in job.dest.inlined_responses:
        try:
            text = (r.response.text or "").strip()
            results.append(text if text else None)
        except Exception:
            results.append(None)
    return results


def parse_regen(text: str, expected_id: int) -> tuple[str | None, dict | None, str | None]:
    """(question, swap_dict_or_None, reason). question=None si falla o ID no coincide."""
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None, None, "no JSON"
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError as e:
        return None, None, str(e)
    returned_id = obj.get("id")
    if returned_id is not None and int(returned_id) != expected_id:
        return None, None, f"ID mismatch: esperado {expected_id}, recibido {returned_id}"
    q = obj.get("question")
    if not isinstance(q, str):
        return None, None, "no question field"
    return q.strip(), obj.get("swap"), obj.get("reason")


def build_regen_prompt(task_id: int, title: str, sentences: list[str], target_idx: int,
                        neg_sentences: list[str], pool_sentences: list[str]) -> str:
    before = sentences[max(0, target_idx - 2):target_idx]
    after = sentences[target_idx + 1:target_idx + 3]
    negs_text = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(neg_sentences))
    pool_text = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(pool_sentences))
    return REGEN_PROMPT.format(
        task_id=task_id,
        n_neg=len(neg_sentences),
        title=title,
        context_before="\n".join(f"- {s}" for s in before) if before else "(inicio del cuento)",
        target=sentences[target_idx],
        context_after="\n".join(f"- {s}" for s in after) if after else "(fin del cuento)",
        negatives=negs_text,
        pool=pool_text,
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--round", required=True, help="Round a reparar, ej. round_003")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=None, help="Limitar a N grupos no-clean (para pruebas)")
    ap.add_argument("--seed", type=int, default=RANDOM_SEED)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    round_dir = ROUNDS_DIR / args.round

    v3_path = round_dir / "generated_v3.jsonl"
    orig_path = round_dir / "generated.jsonl"
    val_path = round_dir / "validation_haiku.jsonl"

    if not val_path.exists():
        raise SystemExit(f"No encontré {val_path} — corré validate_consistency primero")

    # Usar v3 solo si tiene tantos o más grupos que el original (evita usar v3 truncado)
    def count_groups(path: Path) -> int:
        if not path.exists():
            return 0
        keys: set[tuple] = set()
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                keys.add((r["story"], r["answer_unit_idx"]))
        return len(keys)

    n_v3 = count_groups(v3_path)
    n_orig = count_groups(orig_path)

    if v3_path.exists() and n_v3 >= n_orig:
        gen_path = v3_path
    elif orig_path.exists():
        gen_path = orig_path
        if n_v3 > 0:
            print(f"[warn] generated_v3.jsonl tiene {n_v3} grupos vs {n_orig} en generated.jsonl — usando original")
    else:
        raise SystemExit(f"No encontré generated.jsonl en {round_dir}")

    print(f"[src] {gen_path.name}  ({n_orig if gen_path == orig_path else n_v3} grupos)")

    # Agrupar por (story, answer_unit_idx)
    gen_rows = [json.loads(l) for l in gen_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    groups: dict[tuple, dict] = {}
    for r in gen_rows:
        key = (r["story"], r["answer_unit_idx"])
        if key not in groups:
            groups[key] = {
                "story": r["story"], "answer_unit_idx": r["answer_unit_idx"],
                "question": r.get("question", ""), "question_type": r.get("question_type", "factual"),
                "split": r.get("split", "train"), "pos_row": None, "neg_rows": [],
            }
        if r["label"] == 1:
            groups[key]["pos_row"] = r
        else:
            groups[key]["neg_rows"].append(r)

    val_rows = [json.loads(l) for l in val_path.read_text(encoding="utf-8").splitlines() if l.strip()]

    # Preferir matching por answer_unit_idx si está disponible en el archivo de validación
    has_idx = val_rows and "answer_unit_idx" in val_rows[0]
    nonclean_keys: set[tuple] = set()
    if has_idx:
        for r in val_rows:
            if r.get("issue") and r["issue"] != "clean":
                nonclean_keys.add((r["story"], r["answer_unit_idx"]))
    else:
        # Fallback: matchear por pregunta (frágil si las preguntas cambiaron)
        q_to_key: dict[tuple[str, str], tuple] = {}
        for key, g in groups.items():
            q_to_key[(g["story"], g["question"])] = key
        for r in val_rows:
            if r.get("issue") and r["issue"] != "clean":
                k = q_to_key.get((r["story"], r["question"]))
                if k:
                    nonclean_keys.add(k)
        if not nonclean_keys:
            print("[warn] matching por pregunta no encontró no-clean — validation_haiku.jsonl puede estar desactualizado")
            print("[warn] re-corré validate_consistency.py sobre este round antes de regen")

    clean_groups = []
    regen_groups = []
    for key, g in groups.items():
        if key in nonclean_keys:
            regen_groups.append(g)
        else:
            clean_groups.append(g)

    if args.limit:
        rng_limit = random.Random(args.seed + 99)
        regen_groups = rng_limit.sample(regen_groups, min(args.limit, len(regen_groups)))

    print(f"[load] {len(groups)} grupos — {len(clean_groups)} clean (conservados), {len(regen_groups)} a regenerar")

    if args.dry_run:
        by_story: dict[str, int] = {}
        for g in regen_groups:
            by_story[g["story"]] = by_story.get(g["story"], 0) + 1
        print(f"[dry-run] {len(regen_groups)} prompts a Gemini Batch API")
        for story, cnt in sorted(by_story.items(), key=lambda x: -x[1]):
            print(f"  {cnt:4d}  {story}")
        return

    # Cargar textos de cuentos
    story_sentences = load_all_story_sentences()

    # Armar prompts
    tasks = []
    skipped_no_story = 0
    for task_id, g in enumerate(regen_groups):
        sents = story_sentences.get(g["story"])
        if sents is None:
            skipped_no_story += 1
            continue
        pos_row = g["pos_row"]
        if pos_row is None:
            continue
        target_idx = pos_row["unit_idx"]
        neg_sentences = [r["unit"] for r in g["neg_rows"]]
        neg_idxs = {r["unit_idx"] for r in g["neg_rows"]}

        candidate_idxs = [
            i for i, s in enumerate(sents)
            if is_good_target(s)
            and abs(i - target_idx) >= MIN_NEG_DISTANCE
            and i not in neg_idxs
            and i != target_idx
        ]
        pool_idxs = rng.sample(candidate_idxs, min(POOL_SIZE, len(candidate_idxs)))
        pool_sentences = [sents[i] for i in pool_idxs]

        prompt = build_regen_prompt(task_id, g["story"], sents, target_idx, neg_sentences, pool_sentences)
        tasks.append((task_id, g, sents, pool_idxs, pool_sentences, prompt))

    if skipped_no_story:
        print(f"[WARN] {skipped_no_story} grupos sin cuento en texts/ — salteados")

    if not tasks:
        print("[info] 0 grupos a regenerar — nada que hacer")
        # Escribir igual el output con los clean conservados
        out_rows: list[dict] = []
        for g in clean_groups:
            if g["pos_row"]:
                out_rows.append(g["pos_row"])
            out_rows.extend(g["neg_rows"])
        out_path = round_dir / "generated_v3.jsonl"
        with out_path.open("w", encoding="utf-8") as f:
            for r in out_rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"[out] {len(out_rows)} instancias ({len(clean_groups)} grupos) → {out_path}")
        return

    print(f"[batch] enviando {len(tasks)} prompts a Gemini Batch API ...")
    client = get_gemini_client()
    raw_results = call_gemini_batch(client, [t[-1] for t in tasks])

    # Gemini Batch no garantiza orden en inlined_responses → construir mapa id→raw
    id_to_raw: dict[int, str] = {}
    for raw in raw_results:
        if raw is None:
            continue
        m = re.search(r'"id"\s*:\s*(\d+)', raw)
        if m:
            id_to_raw[int(m.group(1))] = raw

    n_positional_matches = sum(1 for (task_id, *_), raw in zip(tasks, raw_results)
                                if raw and f'"id": {task_id}' in raw)
    n_id_matches = len(id_to_raw)
    if n_positional_matches < n_id_matches * 0.5:
        print(f"[info] resultados fuera de orden detectados — usando lookup por ID ({n_id_matches} encontrados)")

    n_ok = n_skip = n_fail = n_mismatch = n_swap = 0
    updated_groups: list[dict] = []

    for task_id, g, sents, pool_idxs, pool_sentences, _ in tasks:
        raw = id_to_raw.get(task_id)
        if raw is None:
            n_fail += 1
            continue
        question, swap, reason = parse_regen(raw, task_id)
        if question is None:
            if reason and "mismatch" in reason:
                n_mismatch += 1
                print(f"  [MISMATCH] task {task_id}: {reason}", file=sys.stderr)
            else:
                n_fail += 1
            continue
        if question.upper() == "SKIP":
            n_skip += 1
            continue

        slug = slugify(g["story"])
        target_idx = g["pos_row"]["unit_idx"]
        neg_rows = [dict(r) for r in g["neg_rows"]]

        # Aplicar swap si Gemini lo pidió
        if swap and isinstance(swap, dict):
            neg_idx_1based = swap.get("neg_idx")
            replacement_text = (swap.get("replacement") or "").strip()
            if isinstance(neg_idx_1based, int) and 1 <= neg_idx_1based <= len(neg_rows):
                matched_pool_idx = next(
                    (pi for pi, ps in zip(pool_idxs, pool_sentences)
                     if ps.strip() == replacement_text),
                    None,
                )
                if matched_pool_idx is not None:
                    new_neg = dict(neg_rows[neg_idx_1based - 1])
                    new_neg["unit_idx"] = matched_pool_idx
                    new_neg["unit"] = sents[matched_pool_idx]
                    new_neg["id"] = f"{slug}__s{target_idx}__neg_swap{neg_idx_1based}"
                    neg_rows[neg_idx_1based - 1] = new_neg
                    n_swap += 1

        pos_row = dict(g["pos_row"])
        pos_row["question"] = question
        for r in neg_rows:
            r["question"] = question

        updated_groups.append({"pos_row": pos_row, "neg_rows": neg_rows})
        n_ok += 1

    print(f"[regen] OK={n_ok}  SKIP={n_skip}  FAIL={n_fail}  MISMATCH={n_mismatch}  swaps={n_swap}")

    # Ensamblar output: clean originales + regenerados
    out_rows: list[dict] = []
    for g in clean_groups:
        if g["pos_row"]:
            out_rows.append(g["pos_row"])
        out_rows.extend(g["neg_rows"])
    for g in updated_groups:
        out_rows.append(g["pos_row"])
        out_rows.extend(g["neg_rows"])

    out_path = round_dir / "generated_v3.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for r in out_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    total_groups = len(clean_groups) + n_ok
    print(f"[out] {len(out_rows)} instancias ({total_groups} grupos) → {out_path}")
    print(f"      pos={sum(1 for r in out_rows if r['label']==1)}  neg={sum(1 for r in out_rows if r['label']==0)}")


if __name__ == "__main__":
    main()
