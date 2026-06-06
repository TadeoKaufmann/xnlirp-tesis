"""
Ensambla el dataset QA final desde todos los rounds validados.

Para cada round usa generated_v3.jsonl si existe (post-regen), sino generated.jsonl
filtrado por las instancias clean de validation_haiku.jsonl.

Desduplicación: si la misma (story, answer_unit_idx) aparece en múltiples rounds,
se queda con la más reciente.

Salida:
  qa/data/qa_final_train.jsonl
  qa/data/qa_final_dev.jsonl
  qa/data/qa_final_test.jsonl
  qa/data/qa_final_stats.json

Uso:
  python qa/scripts/build_qa_final.py
  python qa/scripts/build_qa_final.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
QA_ROOT = REPO_ROOT / "qa"
ROUNDS_DIR = QA_ROOT / "rounds"
OUT_DIR = QA_ROOT / "data"

ET_STORIES = {
    "Ahora debería reírme, si no estuviera muerto",
    "Buenos Aires",
    "Cómo funciona caminar en la nieve",
    "Cómo funcionan los bolsillos",
    "Educar para escalar y bucear",
    "El almohadón de plumas",
    "El espejo",
    "El golpe de gracia",
    "Embarrar la magia",
    "La canción que cantábamos todos los días",
    "La de la Obsesión por la Patineta",
    "La gallina degollada",
    "La lluvia de fuego",
    "La máscara de la Muerte Roja",
    "La noche de los feos",
    "La salud de los enfermos",
    "Las fotografías",
    "Rubí y el lago danzante",
    "Una rosa para Emilia",
    "Wakefield",
}

ROUND_ORDER = ["round_001", "round_002", "round_003", "round_004", "round_005", "round_006"]
SPLIT_FALLBACK = {
    "round_001": "train",
    "round_002": "train",
}


def load_clean_questions(round_dir: Path) -> set[tuple[str, str]]:
    """Retorna set de (story, question) que son clean según validation_haiku."""
    val = round_dir / "validation_haiku.jsonl"
    if not val.exists():
        return set()
    rows = [json.loads(l) for l in val.read_text(encoding="utf-8").splitlines() if l.strip()]
    return {(r["story"], r["question"]) for r in rows if r.get("issue") == "clean"}


def load_round(round_dir: Path, round_name: str) -> list[dict]:
    """Carga grupos clean de un round. Prefiere generated_v3.jsonl."""
    # Si hay generated_v3.jsonl, contiene clean originales + regenerados — usar directo
    v3 = round_dir / "generated_v3.jsonl"
    gen = round_dir / "generated.jsonl"
    if not gen.exists():
        gen = round_dir / "qa_stories_dataset.jsonl"

    if v3.exists():
        rows = [json.loads(l) for l in v3.read_text(encoding="utf-8").splitlines() if l.strip()]
        # v3 ya viene filtrado: no necesita cruzar con validation
    elif gen.exists():
        # Filtrar por clean según validation_haiku
        clean_qs = load_clean_questions(round_dir)
        if not clean_qs:
            return []
        all_rows = [json.loads(l) for l in gen.read_text(encoding="utf-8").splitlines() if l.strip()]
        rows = [r for r in all_rows if (r["story"], r.get("question", "")) in clean_qs]
    else:
        return []

    # Anotar round y corregir split '?'
    fallback_split = SPLIT_FALLBACK.get(round_name)
    for r in rows:
        r["round"] = round_name
        r["is_et"] = r["story"] in ET_STORIES
        if r.get("split") in (None, "", "?") and fallback_split:
            r["split"] = fallback_split

    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    # Cargar todos los rounds en orden (más tarde sobreescribe más temprano en dedup)
    all_rows: list[dict] = []
    for round_name in ROUND_ORDER:
        round_dir = ROUNDS_DIR / round_name
        if not round_dir.exists():
            continue
        rows = load_round(round_dir, round_name)
        if rows:
            source = "generated_v3.jsonl" if (round_dir / "generated_v3.jsonl").exists() else "generated.jsonl"
            print(f"[{round_name}] {len(rows)} filas desde {source}")
        all_rows.extend(rows)

    # Deduplicar por (story, answer_unit_idx): quedarse con el round más reciente
    # Primero determinar qué round gana para cada clave
    key_to_round: dict[tuple, str] = {}
    for r in all_rows:
        key = (r["story"], r["answer_unit_idx"])
        key_to_round[key] = r["round"]  # último en orden = más reciente

    # Luego filtrar: para cada fila, incluirla solo si su round es el ganador
    final_rows = [r for r in all_rows if key_to_round[(r["story"], r["answer_unit_idx"])] == r["round"]]

    # Agrupar por split
    by_split: dict[str, list[dict]] = {"train": [], "dev": [], "test": []}
    unknown = []
    for r in final_rows:
        s = r.get("split", "")
        if s in by_split:
            by_split[s].append(r)
        else:
            unknown.append(r)

    # Stats
    print(f"\n[resumen]")
    total_groups = len(key_to_round)
    for split_name, rows in by_split.items():
        groups = len({(r["story"], r["answer_unit_idx"]) for r in rows})
        stories = len({r["story"] for r in rows})
        pos = sum(1 for r in rows if r["label"] == 1)
        print(f"  {split_name}: {pos} preguntas | {groups} grupos | {stories} cuentos")
    if unknown:
        print(f"  sin split: {len(unknown)} filas")

    total_pos = sum(1 for r in final_rows if r["label"] == 1)
    print(f"  TOTAL: {total_pos} preguntas")

    if args.dry_run:
        print("\n[dry-run] no se escribió nada")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    stats = {}
    for split_name, rows in by_split.items():
        if not rows:
            continue
        out = OUT_DIR / f"qa_final_{split_name}.jsonl"
        with out.open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        pos = sum(1 for r in rows if r["label"] == 1)
        groups = len({(r["story"], r["answer_unit_idx"]) for r in rows})
        stories = sorted({r["story"] for r in rows})
        print(f"[out] {out.name}: {len(rows)} filas ({pos} positivos, {groups} grupos)")
        stats[split_name] = {"rows": len(rows), "positives": pos, "groups": groups, "stories": stories}

    stats_path = OUT_DIR / "qa_final_stats.json"
    stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[out] qa_final_stats.json")


if __name__ == "__main__":
    main()
