"""
Consistency check zero-shot del dataset QA.

Para cada pregunta, presenta al modelo la pregunta + candidatos desordenados
(1 positivo + k negativos) y le pide que elija cuál oración contiene la respuesta.

Si el modelo acierta >> chance (20% con 5 candidatos) → el dataset tiene sentido semántico.

Modelos soportados:
  --model gemini   → Gemini 2.5 Flash (GOOGLE_API_KEY)
  --model haiku    → Claude Haiku 4.5 (ANTHROPIC_API_KEY)
  --model sonnet   → Claude Sonnet 4.5 (ANTHROPIC_API_KEY)

Uso:
  python qa/scripts/validate_consistency.py --round round_001 --model haiku --limit 50
  python qa/scripts/validate_consistency.py --round round_001 --model gemini
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
from tqdm import tqdm

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
QA_ROOT = REPO_ROOT / "qa"
ROUNDS_DIR = QA_ROOT / "rounds"

GEMINI_MODEL = "gemini-2.5-flash"
HAIKU_MODEL = "claude-haiku-4-5-20251001"
SONNET_MODEL = "claude-sonnet-4-5"

API_PAUSE = 0.20
MAX_RETRIES = 3
RANDOM_SEED = 99

PROMPT = """\
Sos un sistema de comprensión lectora. Te doy una pregunta sobre un cuento y \
{n} oraciones candidatas numeradas.

Pregunta: {question}

Candidatos:
{candidates}

Listá los números de TODAS las oraciones que contienen la respuesta directa a la pregunta. \
Si ninguna la contiene, respondé 0. \
Si hay más de una, listalas separadas por coma. \
Sin explicación, sin texto adicional. Solo número(s) o 0.\
"""


def load_groups(round_dir: Path) -> list[dict]:
    gen_path = round_dir / "generated_v3.jsonl"
    if not gen_path.exists():
        gen_path = round_dir / "generated.jsonl"
    if not gen_path.exists():
        gen_path = round_dir / "qa_stories_dataset.jsonl"
    if not gen_path.exists():
        raise FileNotFoundError(f"No se encontró generated.jsonl en {round_dir}")

    rows = [json.loads(l) for l in gen_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    buckets: dict[tuple, dict] = {}
    for r in rows:
        key = (r["story"], r["answer_unit_idx"])
        if key not in buckets:
            buckets[key] = {"story": r["story"], "question": r.get("question", ""),
                            "question_type": r["question_type"], "split": r.get("split", ""),
                            "answer_unit_idx": r["answer_unit_idx"], "pos": None, "negs": []}
        if r["label"] == 1:
            buckets[key]["pos"] = r["unit"]
        else:
            buckets[key]["negs"].append(r["unit"])

    return [g for g in buckets.values() if g["pos"] and g["negs"] and g["question"]]


def build_prompt(question: str, candidates: list[str]) -> str:
    lines = "\n".join(f"{i+1}. {c}" for i, c in enumerate(candidates))
    return PROMPT.format(n=len(candidates), question=question, candidates=lines)


def parse_answer(text: str, n: int) -> list[int]:
    t = text.strip()
    if re.fullmatch(r"0", t):
        return []
    idxs = []
    for m in re.finditer(r"\b([1-9])\b", t):
        idx = int(m.group(1)) - 1
        if 0 <= idx < n and idx not in idxs:
            idxs.append(idx)
    return idxs


def get_gemini_client():
    load_dotenv(REPO_ROOT / ".env")
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise SystemExit("GOOGLE_API_KEY no está en .env")
    from google import genai
    return genai.Client(api_key=api_key)


def get_anthropic_client():
    load_dotenv(REPO_ROOT / ".env")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("ANTHROPIC_API_KEY no está en .env")
    import anthropic
    return anthropic.Anthropic(api_key=api_key)


def call_gemini(client, prompt: str) -> str | None:
    from google.genai import types as genai_types
    cfg = genai_types.GenerateContentConfig(temperature=0.0)
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = client.models.generate_content(model=GEMINI_MODEL, contents=prompt, config=cfg)
            return (resp.text or "").strip()
        except Exception as e:
            print(f"  [WARN] intento {attempt}: {e}", file=sys.stderr)
            time.sleep(3 * attempt)
    return None


def call_anthropic(client, model: str, prompt: str) -> str | None:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            msg = client.messages.create(
                model=model, max_tokens=20,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text.strip()
        except Exception as e:
            print(f"  [WARN] intento {attempt}: {e}", file=sys.stderr)
            time.sleep(3 * attempt)
    return None


def run_anthropic_batch(client, model: str, prompts: list[str]) -> list[str | None]:
    import anthropic
    requests = [
        anthropic.types.message_create_params.MessageCreateParamsNonStreaming(
            model=model,
            max_tokens=20,
            messages=[{"role": "user", "content": p}],
        )
        for p in prompts
    ]
    batch_requests = [
        {"custom_id": str(i), "params": r}
        for i, r in enumerate(requests)
    ]
    batch = client.messages.batches.create(requests=batch_requests)
    print(f"[batch] id: {batch.id}")
    return _poll_and_download_anthropic_batch(client, batch.id, len(prompts))


def _poll_and_download_anthropic_batch(client, batch_id: str, n: int) -> list[str | None]:
    completed = {"ended"}
    batch = None
    while True:
        try:
            batch = client.messages.batches.retrieve(batch_id)
            if batch.processing_status in completed:
                break
            print(f"[batch] {batch.processing_status} ...")
            time.sleep(10)
        except Exception as e:
            print(f"  [WARN] polling error: {e} — reintentando en 15s", file=sys.stderr)
            time.sleep(15)
    print(f"[batch] completado — {batch.request_counts}")
    results_map: dict[int, str | None] = {}
    while True:
        try:
            for result in client.messages.batches.results(batch_id):
                idx = int(result.custom_id)
                if result.result.type == "succeeded":
                    results_map[idx] = result.result.message.content[0].text.strip()
                else:
                    results_map[idx] = None
            break
        except Exception as e:
            print(f"  [WARN] error descargando resultados: {e} — reintentando en 15s", file=sys.stderr)
            time.sleep(15)
    return [results_map.get(i) for i in range(n)]


def run(groups: list[dict], model_name: str, rng: random.Random, use_batch: bool = False) -> list[dict]:
    if model_name == "gemini":
        client = get_gemini_client()
        call_fn = lambda prompt: call_gemini(client, prompt)
        model_label = GEMINI_MODEL
        use_batch = False
    elif model_name == "haiku":
        client = get_anthropic_client()
        call_fn = lambda prompt: call_anthropic(client, HAIKU_MODEL, prompt)
        model_label = HAIKU_MODEL
    else:  # sonnet
        client = get_anthropic_client()
        call_fn = lambda prompt: call_anthropic(client, SONNET_MODEL, prompt)
        model_label = SONNET_MODEL

    print(f"[model] {model_label}  [modo {'batch' if use_batch else 'secuencial'}]")

    # Preparar candidatos y prompts
    shuffled = []
    for g in groups:
        candidates = [g["pos"]] + g["negs"]
        rng.shuffle(candidates)
        shuffled.append((candidates, candidates.index(g["pos"])))

    if use_batch and model_name in ("haiku", "sonnet"):
        prompts = [build_prompt(g["question"], cands) for g, (cands, _) in zip(groups, shuffled)]
        print(f"[batch] enviando {len(prompts)} requests a Anthropic Batch API ...")
        raw_list = run_anthropic_batch(client, model_label, prompts)
    else:
        raw_list = []
        for g, (candidates, _) in tqdm(zip(groups, shuffled), total=len(groups), desc=f"validando [{model_name}]"):
            raw = call_fn(build_prompt(g["question"], candidates))
            time.sleep(API_PAUSE)
            raw_list.append(raw)

    results = []
    for g, (candidates, correct_idx), raw in zip(groups, shuffled, raw_list):
        chosen_idxs = parse_answer(raw, len(candidates)) if raw else None
        if chosen_idxs is None:
            issue = None
        elif len(chosen_idxs) == 0:
            issue = "answerability"
        elif correct_idx in chosen_idxs and len(chosen_idxs) == 1:
            issue = "clean"
        elif correct_idx in chosen_idxs and len(chosen_idxs) > 1:
            issue = "neg_difficulty"
        else:
            issue = "wrong"

        results.append({
            "story": g["story"],
            "answer_unit_idx": g["answer_unit_idx"],
            "question": g["question"],
            "question_type": g["question_type"],
            "split": g["split"],
            "n_candidates": len(candidates),
            "correct_idx": correct_idx,
            "chosen_idxs": chosen_idxs,
            "correct": (issue == "clean") if issue is not None else None,
            "issue": issue,
            "model": model_label,
            "model_raw": raw,
        })

    return results


def report(results: list[dict], round_name: str, model_name: str) -> None:
    answered = [r for r in results if r["issue"] is not None]
    if not answered:
        print("Sin resultados válidos.")
        return

    n = len(answered)
    by_issue = Counter(r["issue"] for r in answered)
    n_cands = results[0]["n_candidates"]
    chance = 100 / n_cands
    clean_pct = by_issue["clean"] / n * 100

    print(f"\n{'='*50}")
    print(f"Modelo: {results[0]['model']}")
    print(f"Round:  {round_name}")
    print(f"{'='*50}")
    print(f"Clean:         {clean_pct:.1f}%  ({by_issue['clean']}/{n})  |  chance: {chance:.1f}%  |  lift: {clean_pct - chance:+.1f}pp")
    print(f"neg_difficulty:{by_issue['neg_difficulty']:4d}  ({by_issue['neg_difficulty']/n*100:.1f}%)  — positivo correcto pero también eligió negativo(s)")
    print(f"wrong:         {by_issue['wrong']:4d}  ({by_issue['wrong']/n*100:.1f}%)  — eligió solo negativo(s)")
    print(f"answerability: {by_issue['answerability']:4d}  ({by_issue['answerability']/n*100:.1f}%)  — no eligió ninguna")

    print("\nPor tipo de pregunta:")
    for qtype in ("factual", "inferencial"):
        sub = [r for r in answered if r["question_type"] == qtype]
        if sub:
            c = sum(1 for r in sub if r["issue"] == "clean")
            nd = sum(1 for r in sub if r["issue"] == "neg_difficulty")
            print(f"  {qtype}: clean={c/len(sub)*100:.1f}%  neg_diff={nd}  ({c}/{len(sub)})")

    print("\nPor cuento (ordenado por no-clean):")
    by_story: dict[str, list] = defaultdict(list)
    for r in answered:
        by_story[r["story"]].append(r)
    for story, sub in sorted(by_story.items(), key=lambda x: sum(1 for r in x[1] if r["issue"] != "clean"), reverse=True):
        c = sum(1 for r in sub if r["issue"] == "clean")
        nd = sum(1 for r in sub if r["issue"] == "neg_difficulty")
        wr = sum(1 for r in sub if r["issue"] == "wrong")
        pct = c / len(sub) * 100
        marker = " ←" if pct < 80 else ""
        print(f"  {pct:5.1f}%  clean={c}  neg_diff={nd}  wrong={wr}  {story}{marker}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--round", default=None, help="Round a validar (default: el más reciente)")
    ap.add_argument("--model", choices=["gemini", "haiku", "sonnet"], default="haiku")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--seed", type=int, default=RANDOM_SEED)
    ap.add_argument("--batch", action="store_true", help="Usar Anthropic Batch API (async, 50% descuento)")
    ap.add_argument("--only-new", action="store_true", help="Saltear grupos ya validados en validation_<model>.jsonl")
    ap.add_argument("--output", type=Path, default=None,
                    help="Guardar resultados en JSONL (default: qa/rounds/<round>/validation_<model>.jsonl)")
    args = ap.parse_args()

    rng = random.Random(args.seed)

    # Detectar round
    if args.round:
        round_dir = ROUNDS_DIR / args.round
    else:
        rounds = sorted([d for d in ROUNDS_DIR.iterdir() if d.is_dir()])
        if not rounds:
            raise SystemExit("No hay rounds en qa/rounds/")
        round_dir = rounds[-1]
    round_name = round_dir.name
    print(f"[round] {round_name}")

    groups = load_groups(round_dir)
    print(f"[load] {len(groups)} grupos de preguntas")

    if args.only_new:
        out_path_check = args.output or round_dir / f"validation_{args.model}.jsonl"
        if out_path_check.exists():
            already_done: set[tuple] = set()
            for line in out_path_check.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    r = json.loads(line)
                    already_done.add((r["story"], r.get("answer_unit_idx", r["question"])))
            before = len(groups)
            groups = [g for g in groups if (g["story"], g["answer_unit_idx"]) not in already_done]
            print(f"[only-new] {before - len(groups)} ya validados salteados — {len(groups)} nuevos")

    if args.limit:
        groups = random.Random(args.seed + 1).sample(groups, min(args.limit, len(groups)))
        print(f"[limit] {len(groups)} grupos")

    results = run(groups, args.model, rng, use_batch=args.batch)

    # Guardar (append si --only-new, overwrite si no)
    out = args.output or round_dir / f"validation_{args.model}.jsonl"
    mode = "a" if args.only_new else "w"
    with out.open(mode, encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"[out] → {out}")

    report(results, round_name, args.model)


if __name__ == "__main__":
    main()
