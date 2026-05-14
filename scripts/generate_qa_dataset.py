"""
Generador de dataset de QA binaria (oración, pregunta) -> {0, 1}
a partir de cuentos literarios rioplatenses ubicados en `texts/`.

Conexión con la tesis:
- Cuando un lector busca la respuesta a una pregunta, sus fijaciones aumentan
  sobre la oración que contiene la respuesta. Esa señal de eye-tracking es el
  oro al que aspira un modelo de QA-binaria oración-nivel.
- El dataset se usa para entrenar/evaluar clasificación binaria sobre el par
  (oración, pregunta) -> contiene_respuesta {0, 1}.

Decisiones de diseño (justificadas en el reporte adjunto):
  A) Unidad = oración individual (regex aware de abreviaturas).
  B) Contexto al generar pregunta = título + ventana ±2 oraciones, marcando target.
  C) Negativos del MISMO cuento, k=4 por positivo, distancia >= 3 al target.
  D) Split por HISTORIA: 20 train / 5 dev / 5 test (resto si lo hubiera).
  E) 85% factual / 15% inferencial.

Output:
  - data/processed/qa_stories_dataset.jsonl   (raw, todas las instancias)
  - data/processed/qa_stories_train.jsonl     (1000, balanceado por label)
  - data/processed/qa_stories_dev.jsonl
  - data/processed/qa_stories_test.jsonl

Resumible: cada pregunta generada se appendea inmediatamente a un archivo
intermedio `data/processed/_qa_questions_raw.jsonl`. Al reiniciar, se saltean
las (story, unit_idx) ya procesadas.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
from tqdm import tqdm


# ----------------------------- paths ---------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
TEXTS_DIR = REPO_ROOT / "texts"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"

RAW_QUESTIONS_PATH = PROCESSED_DIR / "_qa_questions_raw.jsonl"  # cache resumible
DATASET_PATH = PROCESSED_DIR / "qa_stories_dataset.jsonl"
TRAIN_PATH = PROCESSED_DIR / "qa_stories_train.jsonl"
DEV_PATH = PROCESSED_DIR / "qa_stories_dev.jsonl"
TEST_PATH = PROCESSED_DIR / "qa_stories_test.jsonl"


# ----------------------------- config --------------------------------------

EXCLUDE_FILES = {"Test"}
MIN_WORDS_PER_UNIT = 8           # filtro de oraciones demasiado cortas
MAX_WORDS_PER_UNIT = 80          # oraciones gigantes -> probablemente mal partidas
MIN_NEG_DISTANCE = 3             # idx |i - j| >= MIN_NEG_DISTANCE
NEGATIVES_PER_POSITIVE = 4
INFERENTIAL_RATIO = 0.15         # 15% inferenciales
MODEL = "gemini-2.5-flash"
TEMPERATURE = 0.7
API_PAUSE_SECONDS = 0.20         # ~5 RPS, muy por debajo de 1000 RPM Tier 1
API_PAUSE_AFTER_ERROR = 5.0
MAX_RETRIES = 3
RANDOM_SEED = 42

# Split por historia. Si hay menos de 30 historias, se ajustan estas cifras
# proporcionalmente con priority train > dev > test.
SPLIT_TRAIN_STORIES = 20
SPLIT_DEV_STORIES = 5
SPLIT_TEST_STORIES = 5

TARGET_TRAIN = 1000              # tamaño objetivo de train balanceado


# ----------------------- splitting de oraciones ----------------------------

# Abreviaturas comunes que NO terminan oración. Lowercase comparado.
ABBREVIATIONS = {
    "sr", "sra", "srta", "dr", "dra", "lic", "ing", "prof", "gral",
    "sres", "ud", "uds", "vs", "etc", "av", "atte", "depto", "dpto",
    "no",  # "no." raro pero existe
    "cap", "pag", "pág", "fig", "vol", "ed", "núm", "nro",
}


def slugify(name: str) -> str:
    """Slug ascii minúsculo y sin espacios para usar como id."""
    s = name.lower()
    s = re.sub(r"[áàä]", "a", s)
    s = re.sub(r"[éèë]", "e", s)
    s = re.sub(r"[íìï]", "i", s)
    s = re.sub(r"[óòö]", "o", s)
    s = re.sub(r"[úùü]", "u", s)
    s = re.sub(r"ñ", "n", s)
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = s.strip("_")
    return s or "story"


def strip_paragraph_number(line: str) -> str:
    """Saca el prefijo `\\d+\\t` que tienen algunos archivos."""
    return re.sub(r"^\d+\t", "", line)


def load_story_text(path: Path) -> str:
    """Lee el archivo y normaliza:
    - Saca BOM y CRLF.
    - Saca el prefijo numérico de párrafo en cada línea.
    - Une todo en un solo string para sentence splitting; los newlines actúan
      como separadores fuertes (se consideran fin de oración si la línea no
      terminaba en signo de puntuación).
    """
    raw = path.read_text(encoding="utf-8", errors="replace")
    raw = raw.replace("﻿", "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [strip_paragraph_number(ln).strip() for ln in raw.split("\n")]
    lines = [ln for ln in lines if ln]
    # Garantizar que cada línea termine con un signo que el splitter respete,
    # para que un "\n" dentro de un párrafo numerado igual corte oración.
    fixed = []
    for ln in lines:
        if ln[-1] not in ".!?…»\")":
            ln = ln + "."
        fixed.append(ln)
    return " ".join(fixed)


# Splitter regex. Captura un signo final + comilla/cierre opcional, y corta
# en el siguiente espacio que sea seguido por mayúscula o apertura de cita.
SENT_END_RE = re.compile(
    r"""(?<=[\.\!\?…])               # signo final
        ["»”’\)]?                    # cierre opcional
        \s+                          # whitespace
        (?=[«"“¿¡A-ZÁÉÍÓÚÑ])         # inicio del siguiente
    """,
    re.VERBOSE,
)


def split_sentences(text: str) -> list[str]:
    """Sentence splitter regex con manejo simple de abreviaturas.

    Estrategia: split inicial por SENT_END_RE; luego merge hacia atrás cuando
    el final del segmento previo es una abreviatura conocida.
    """
    parts = SENT_END_RE.split(text)
    parts = [p.strip() for p in parts if p.strip()]
    merged: list[str] = []
    for p in parts:
        if merged:
            prev = merged[-1]
            # token final del prev sin signo
            tail = re.search(r"(\w+)\.$", prev)
            if tail and tail.group(1).lower() in ABBREVIATIONS:
                merged[-1] = prev + " " + p
                continue
        merged.append(p)
    return merged


def is_good_target(sentence: str) -> bool:
    """Filtra oraciones poco útiles como target de pregunta."""
    n_words = len(sentence.split())
    if n_words < MIN_WORDS_PER_UNIT:
        return False
    if n_words > MAX_WORDS_PER_UNIT:
        return False
    # Oraciones que son puramente diálogo de una palabra entrecomillada
    if re.fullmatch(r"[«\"“].{0,30}[»\"”][\.\!\?…]?", sentence):
        return False
    # Oraciones que son solo onomatopeyas o interjecciones
    if re.fullmatch(r"[¡!¿\?\.\,\-\—\s]+", sentence):
        return False
    return True


# ----------------------------- prompt --------------------------------------

QUESTION_PROMPT = """\
Sos un anotador de datasets de comprensión lectora en español rioplatense (RP).

Te paso fragmentos de un cuento literario rioplatense. Te marco una ORACIÓN TARGET
dentro de una ventana de contexto. Tu tarea es generar UNA pregunta en español
rioplatense natural (voseo donde corresponda, léxico RP) tal que:

  1. La pregunta sea respondible LEYENDO ÚNICAMENTE LA ORACIÓN TARGET. Las
     oraciones del contexto NO deben contener la respuesta; son solo para que
     entiendas el referente (quién es el personaje, de qué se habla).
  2. La pregunta NO debe pedir una cita literal. Debe poder formularse incluso
     sin haber leído el cuento, mencionando al personaje o referente con su
     nombre o una descripción mínima.
  3. La pregunta debe ser de tipo {tipo_pregunta}.
     - factual: pregunta directa sobre un hecho explícito en la oración target
       (qué hizo X, dónde fue, cuándo, quién, con qué).
     - inferencial: pregunta que requiere combinar información de la oración
       target con conocimiento del mundo, pero cuya pieza clave de evidencia
       SIGUE ESTANDO en la oración target (no en el contexto).
  4. Usá español rioplatense: voseo si la pregunta es a un personaje (raro,
     evitalo), pero sobre todo léxico y giros RP. Evitá peninsularismos.
  5. NO repitas las palabras exactas de la oración target en la pregunta más
     de lo necesario. Reformulá.
  6. Si la oración target no permite generar una buena pregunta (es muy
     descriptiva, ambigua, o demasiado dependiente del contexto), devolvé el
     string exacto: SKIP

TÍTULO: {title}

CONTEXTO PREVIO:
{context_before}

>>> ORACIÓN TARGET (de acá tiene que salir la respuesta):
{target}
<<<

CONTEXTO POSTERIOR:
{context_after}

Devolvé SOLO el JSON, sin texto adicional, con este formato exacto:
{{"question": "..."}}

O bien:
{{"question": "SKIP", "reason": "..."}}
"""


def build_prompt(title: str, sentences: list[str], i: int, tipo_pregunta: str) -> str:
    before = sentences[max(0, i - 2):i]
    after = sentences[i + 1:i + 3]
    return QUESTION_PROMPT.format(
        title=title,
        context_before="\n".join(f"- {s}" for s in before) if before else "(inicio del cuento)",
        target=sentences[i],
        context_after="\n".join(f"- {s}" for s in after) if after else "(fin del cuento)",
        tipo_pregunta=tipo_pregunta,
    )


# ----------------------------- gemini --------------------------------------

def get_client():
    from google import genai  # type: ignore
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise SystemExit("GOOGLE_API_KEY no está en .env")
    return genai.Client(api_key=api_key)


def call_gemini(client, prompt: str) -> str | None:
    """Llama a Gemini, devuelve el texto o None si falla tras retries."""
    from google.genai import types as genai_types  # type: ignore
    cfg = genai_types.GenerateContentConfig(temperature=TEMPERATURE)
    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=cfg,
            )
            text = (resp.text or "").strip()
            if text:
                return text
            last_err = "respuesta vacía"
        except Exception as e:  # noqa: BLE001
            last_err = repr(e)
            time.sleep(API_PAUSE_AFTER_ERROR * attempt)
    print(f"  [WARN] Gemini falló tras {MAX_RETRIES} intentos: {last_err}", file=sys.stderr)
    return None


def parse_question_json(text: str) -> tuple[str | None, str | None]:
    """Devuelve (question, reason). question puede ser 'SKIP' o el string."""
    # Aislar el JSON aunque venga con ```json fences.
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None, "no JSON found"
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError as e:
        return None, f"json decode: {e}"
    q = obj.get("question")
    if not isinstance(q, str):
        return None, "no question field"
    return q.strip(), obj.get("reason")


# ------------------------- carga de cuentos --------------------------------

def discover_stories() -> list[tuple[str, Path]]:
    items: list[tuple[str, Path]] = []
    for p in sorted(TEXTS_DIR.iterdir()):
        if not p.is_file():
            continue
        if p.name in EXCLUDE_FILES:
            continue
        items.append((p.name, p))
    return items


def segment_story(title: str, path: Path) -> list[str]:
    text = load_story_text(path)
    sentences = split_sentences(text)
    return sentences


# --------------------------- IO incremental --------------------------------

def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def load_already_processed() -> dict[tuple[str, int], dict]:
    """Lee el cache resumible y devuelve {(story, unit_idx): row}."""
    if not RAW_QUESTIONS_PATH.exists():
        return {}
    out: dict[tuple[str, int], dict] = {}
    with RAW_QUESTIONS_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            key = (r["story"], int(r["unit_idx"]))
            out[key] = r
    return out


# --------------------------- decisión tipo Q -------------------------------

def pick_question_type(rng: random.Random) -> str:
    return "inferencial" if rng.random() < INFERENTIAL_RATIO else "factual"


# --------------------------- main pipeline ---------------------------------

def stage_generate_questions(
    stories: list[tuple[str, list[str]]],
    rng: random.Random,
    dry_run: bool,
) -> list[dict]:
    """Stage 1: para cada (story, target_idx) genera una pregunta con Gemini.

    Devuelve la lista completa de filas {story, unit_idx, unit, question, question_type}.
    """
    cached = load_already_processed()
    print(f"[cache] {len(cached)} preguntas previamente generadas se reusan.")

    # Lista de tareas (story, idx, sentence, qtype) para las oraciones target.
    tasks: list[tuple[str, int, str, str]] = []
    for title, sentences in stories:
        for i, s in enumerate(sentences):
            if not is_good_target(s):
                continue
            qtype = pick_question_type(rng)
            tasks.append((title, i, s, qtype))

    print(f"[plan] {len(tasks)} oraciones target a procesar "
          f"({sum(1 for t in tasks if t[3] == 'inferencial')} inferenciales).")

    if dry_run:
        print("[dry-run] no se llama a la API.")
        # Estimación de instancias finales bajo el supuesto de 100% éxito.
        est_pos = len(tasks)
        est_neg = est_pos * NEGATIVES_PER_POSITIVE
        print(f"[dry-run] estimación: {est_pos} positivos + {est_neg} negativos "
              f"= {est_pos + est_neg} instancias totales.")
        return []

    client = get_client()

    rows: list[dict] = []
    n_skipped = 0
    n_failed = 0

    # mapa título -> oraciones, para construir el prompt
    title_to_sents = {t: s for t, s in stories}

    for title, i, sent, qtype in tqdm(tasks, desc="generando preguntas"):
        key = (title, i)
        if key in cached:
            rows.append(cached[key])
            continue

        prompt = build_prompt(title, title_to_sents[title], i, qtype)
        text = call_gemini(client, prompt)
        if text is None:
            n_failed += 1
            time.sleep(API_PAUSE_SECONDS)
            continue

        question, reason = parse_question_json(text)
        if question is None:
            n_failed += 1
            print(f"  [WARN] {title} idx {i}: parse error ({reason}). Raw: {text[:120]!r}",
                  file=sys.stderr)
            time.sleep(API_PAUSE_SECONDS)
            continue

        if question.upper() == "SKIP":
            n_skipped += 1
            row = {
                "story": title,
                "unit_idx": i,
                "unit": sent,
                "question": None,
                "question_type": qtype,
                "skip_reason": reason or "model said SKIP",
            }
        else:
            row = {
                "story": title,
                "unit_idx": i,
                "unit": sent,
                "question": question,
                "question_type": qtype,
            }
        append_jsonl(RAW_QUESTIONS_PATH, row)
        rows.append(row)
        time.sleep(API_PAUSE_SECONDS)

    print(f"[stage1] OK={sum(1 for r in rows if r.get('question'))} "
          f"SKIP={n_skipped} FAIL={n_failed}")
    return rows


def stage_build_instances(
    stories: list[tuple[str, list[str]]],
    question_rows: list[dict],
    rng: random.Random,
) -> list[dict]:
    """Stage 2: para cada pregunta válida arma 1 positivo + k negativos del mismo cuento."""
    title_to_sents = {t: s for t, s in stories}

    # Agrupar preguntas por cuento
    by_story: dict[str, list[dict]] = defaultdict(list)
    for r in question_rows:
        if r.get("question"):
            by_story[r["story"]].append(r)

    instances: list[dict] = []
    for title, q_rows in by_story.items():
        sentences = title_to_sents[title]
        # candidatos a negativo: cualquier oración del cuento que pase el filtro
        # y no sea la target. Filtramos por distancia al elegir.
        candidate_idxs = [i for i, s in enumerate(sentences) if is_good_target(s)]
        if len(candidate_idxs) < NEGATIVES_PER_POSITIVE + 1:
            print(f"  [WARN] '{title}' tiene solo {len(candidate_idxs)} oraciones "
                  f"viables; podría faltar negativos.", file=sys.stderr)

        for q_idx, qrow in enumerate(q_rows):
            target_idx = qrow["unit_idx"]
            question = qrow["question"]
            qtype = qrow["question_type"]
            slug = slugify(title)

            # POSITIVO
            pos_id = f"{slug}__s{target_idx}__q{q_idx}__pos"
            instances.append({
                "id": pos_id,
                "story": title,
                "unit_idx": target_idx,
                "unit": sentences[target_idx],
                "question": question,
                "label": 1,
                "question_type": qtype,
                "answer_unit_idx": target_idx,
                "split": None,  # se completa en stage 3
            })

            # NEGATIVOS: mismo cuento, distancia >= MIN_NEG_DISTANCE
            far_pool = [i for i in candidate_idxs
                        if abs(i - target_idx) >= MIN_NEG_DISTANCE]
            if len(far_pool) < NEGATIVES_PER_POSITIVE:
                # fallback: aflojar a distancia >= 1
                far_pool = [i for i in candidate_idxs if i != target_idx]

            if len(far_pool) == 0:
                continue
            k = min(NEGATIVES_PER_POSITIVE, len(far_pool))
            neg_idxs = rng.sample(far_pool, k)
            for j, neg_idx in enumerate(neg_idxs):
                instances.append({
                    "id": f"{slug}__s{target_idx}__q{q_idx}__neg{j}",
                    "story": title,
                    "unit_idx": neg_idx,
                    "unit": sentences[neg_idx],
                    "question": question,
                    "label": 0,
                    "question_type": qtype,
                    "answer_unit_idx": target_idx,
                    "split": None,
                })

    return instances


def stage_split(
    instances: list[dict],
    rng: random.Random,
) -> list[dict]:
    """Stage 3: split por historia. Asigna 'split' in {train, dev, test}."""
    stories_present = sorted({r["story"] for r in instances})
    rng.shuffle(stories_present)

    n = len(stories_present)
    n_train = min(SPLIT_TRAIN_STORIES, max(1, n - 2))
    n_dev = min(SPLIT_DEV_STORIES, max(1, (n - n_train) // 2))
    n_test = n - n_train - n_dev
    if n_test <= 0:
        n_test = 1
        n_dev = max(1, n - n_train - n_test)

    train_stories = set(stories_present[:n_train])
    dev_stories = set(stories_present[n_train:n_train + n_dev])
    test_stories = set(stories_present[n_train + n_dev:n_train + n_dev + n_test])

    print(f"[split] {n_train} train / {n_dev} dev / {n_test} test (cuentos)")

    for r in instances:
        if r["story"] in train_stories:
            r["split"] = "train"
        elif r["story"] in dev_stories:
            r["split"] = "dev"
        else:
            r["split"] = "test"
    return instances


def stage_export(instances: list[dict]) -> None:
    """Stage 4: dump del raw + train/dev/test en archivos separados.

    Train: balanceado por label hasta TARGET_TRAIN.
    """
    write_jsonl(DATASET_PATH, instances)

    train = [r for r in instances if r["split"] == "train"]
    dev = [r for r in instances if r["split"] == "dev"]
    test = [r for r in instances if r["split"] == "test"]

    rng = random.Random(RANDOM_SEED + 1)

    # Balanceo del train: tomar mitad y mitad hasta TARGET_TRAIN.
    pos = [r for r in train if r["label"] == 1]
    neg = [r for r in train if r["label"] == 0]
    rng.shuffle(pos)
    rng.shuffle(neg)
    half = TARGET_TRAIN // 2
    train_balanced = pos[:half] + neg[:half]
    rng.shuffle(train_balanced)

    write_jsonl(TRAIN_PATH, train_balanced)
    write_jsonl(DEV_PATH, dev)
    write_jsonl(TEST_PATH, test)

    print(f"[export] raw={len(instances)} -> {DATASET_PATH.name}")
    print(f"[export] train={len(train_balanced)} (de {len(train)} totales) "
          f"-> {TRAIN_PATH.name}")
    print(f"[export] dev={len(dev)}   -> {DEV_PATH.name}")
    print(f"[export] test={len(test)} -> {TEST_PATH.name}")


def report(instances: list[dict]) -> None:
    print("\n========== REPORTE ==========")
    print(f"total instancias: {len(instances)}")
    label_counts = Counter(r["label"] for r in instances)
    print(f"distribución label: {dict(label_counts)}")

    qtype_counts = Counter(r["question_type"] for r in instances)
    print(f"distribución tipo de pregunta: {dict(qtype_counts)}")

    by_story = Counter(r["story"] for r in instances)
    print(f"\ncuentos cubiertos: {len(by_story)}")
    print("instancias por cuento:")
    for story, c in sorted(by_story.items(), key=lambda x: -x[1]):
        print(f"  {c:5d}  {story}")

    by_split = Counter(r["split"] for r in instances)
    print(f"\ndistribución por split: {dict(by_split)}")
    for split in ("train", "dev", "test"):
        sub = [r for r in instances if r["split"] == split]
        if not sub:
            continue
        sub_labels = Counter(r["label"] for r in sub)
        sub_qtypes = Counter(r["question_type"] for r in sub)
        print(f"  {split}: label={dict(sub_labels)}  qtype={dict(sub_qtypes)}")


# ----------------------------- CLI -----------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true",
                    help="No llama a la API; cuenta instancias esperadas.")
    ap.add_argument("--limit-stories", type=int, default=None,
                    help="Procesar solo las primeras N historias (testing).")
    ap.add_argument("--seed", type=int, default=RANDOM_SEED)
    args = ap.parse_args()

    rng = random.Random(args.seed)

    # 1. Descubrir y segmentar
    raw_stories = discover_stories()
    if args.limit_stories is not None:
        raw_stories = raw_stories[:args.limit_stories]
    print(f"[load] {len(raw_stories)} historias en {TEXTS_DIR}")

    stories: list[tuple[str, list[str]]] = []
    n_short = 0
    for title, path in raw_stories:
        sents = segment_story(title, path)
        good = [s for s in sents if is_good_target(s)]
        n_short += len(sents) - len(good)
        stories.append((title, sents))
        print(f"  {title}: {len(sents)} oraciones ({len(good)} target-viables)")
    print(f"[load] {n_short} oraciones descartadas por longitud/forma "
          f"(min={MIN_WORDS_PER_UNIT}, max={MAX_WORDS_PER_UNIT}).")

    # 2. Generar preguntas (resumible)
    question_rows = stage_generate_questions(stories, rng, args.dry_run)
    if args.dry_run:
        return

    # 3. Construir instancias positivo + negativos
    instances = stage_build_instances(stories, question_rows, rng)
    print(f"[build] {len(instances)} instancias armadas "
          f"({sum(1 for r in instances if r['label']==1)} pos / "
          f"{sum(1 for r in instances if r['label']==0)} neg).")

    # 4. Split por historia
    instances = stage_split(instances, rng)

    # 5. Exportar
    stage_export(instances)

    # 6. Reporte
    report(instances)


if __name__ == "__main__":
    main()
