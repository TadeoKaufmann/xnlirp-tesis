"""
Harness de experimentación para traducción XNLI ES → RP.
Itera por modelo × temperatura × variante de prompt.
Reanudable, robusto, con outputs por configuración.
"""
import argparse
import json
import os
import sys
import time
from itertools import product
from pathlib import Path
from typing import Any, Iterable

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import Levenshtein
from dotenv import load_dotenv
from tqdm import tqdm

from google import genai
from google.genai import types as genai_types


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEV_200 = REPO_ROOT / "data" / "dev" / "xnli_combined_dev_200.jsonl"
EXPERIMENTS_DIR = REPO_ROOT / "results" / "experiments"
PROMPTS_DIR = REPO_ROOT / "pipeline_traduccion" / "prompts"

REQUIRED_OUTPUT_FIELDS = [
    "idx", "label", "prem_rp", "hyp_rp", "type",
    "changes", "secondary_features", "cultural_candidates",
    "review_flag", "review_note", "note"
]


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


PROCESSED_SET_PATH = Path("data/dev/processed_idx_set.json")


def already_processed_idxs(path: Path) -> set[int]:
    done = set()
    # Leer output JSONL del run actual
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    done.add(json.loads(line)["idx"])
                except Exception:
                    pass
    # Leer set global (to_fix + to_upload de batches anteriores)
    if PROCESSED_SET_PATH.exists():
        try:
            done.update(json.loads(PROCESSED_SET_PATH.read_text(encoding="utf-8")))
        except Exception:
            pass
    return done


def mark_processed(jsonl_paths: list[Path]) -> int:
    """Agrega los idx de uno o más JSONLs al set global de procesados."""
    existing = set()
    if PROCESSED_SET_PATH.exists():
        try:
            existing = set(json.loads(PROCESSED_SET_PATH.read_text(encoding="utf-8")))
        except Exception:
            pass
    for p in jsonl_paths:
        if not p.exists():
            continue
        with p.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        existing.add(json.loads(line)["idx"])
                    except Exception:
                        pass
    PROCESSED_SET_PATH.write_text(json.dumps(sorted(existing), ensure_ascii=False), encoding="utf-8")
    return len(existing)


def load_prompt_template(variant: str) -> str:
    path = PROMPTS_DIR / f"prompt_{variant}.txt"
    if not path.exists():
        # Buscar prefijo (v1, v2 → matchear nombre completo)
        candidates = sorted(PROMPTS_DIR.glob(f"prompt_{variant}*.txt"))
        if not candidates:
            raise FileNotFoundError(f"No se encontró prompt para variante '{variant}' en {PROMPTS_DIR}")
        path = candidates[0]
    return path.read_text(encoding="utf-8")


def build_user_message(template: str, row: dict, include_english: bool) -> str:
    en_block = (
        f"\nINGLÉS DE REFERENCIA (solo para detectar errores tipo D, no traducir directamente):\n"
        f"prem_en: {row['prem_en']}\nhyp_en: {row['hyp_en']}\n"
        if include_english else ""
    )
    return template.replace(
        "{{INSTANCE}}",
        f"INSTANCIA A ADAPTAR:\nidx: {row['idx']}\nlabel: {row['label']}\n"
        f"prem_es: {row['prem_es']}\nhyp_es: {row['hyp_es']}{en_block}"
    )


def call_gemini_with_retries(
    client: genai.Client,
    model_name: str,
    temperature: float,
    user_message: str,
    max_api_retries: int = 5,
    max_parse_retries: int = 3,
    base_backoff: float = 2.0,
) -> dict:
    last_err = None
    for api_attempt in range(max_api_retries):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=user_message,
                config=genai_types.GenerateContentConfig(
                    temperature=temperature,
                    response_mime_type="application/json",
                ),
            )
            text = response.text
            for parse_attempt in range(max_parse_retries):
                try:
                    parsed = json.loads(text)
                    return parsed
                except json.JSONDecodeError as je:
                    last_err = f"JSONDecodeError: {je}"
                    # Intentar limpiar markdown fences
                    cleaned = text.strip()
                    if cleaned.startswith("```"):
                        cleaned = cleaned.strip("`")
                        if cleaned.startswith("json"):
                            cleaned = cleaned[4:].strip()
                    try:
                        parsed = json.loads(cleaned)
                        return parsed
                    except json.JSONDecodeError:
                        pass
                    if parse_attempt < max_parse_retries - 1:
                        time.sleep(0.5)
            raise ValueError(f"Falla parseo JSON tras {max_parse_retries} intentos. Último: {last_err}")
        except Exception as e:
            last_err = str(e)
            if api_attempt < max_api_retries - 1:
                wait = base_backoff * (2 ** api_attempt)
                time.sleep(wait)
            else:
                raise RuntimeError(f"Falla API tras {max_api_retries} intentos: {last_err}") from e


def normalize_response(parsed: dict, original: dict) -> dict:
    """Asegura todos los campos requeridos, calcula Levenshtein desde Python."""
    out = {
        "idx": original["idx"],
        "label": original["label"],
        "label_int": original["label_int"],
        "prem_en": original["prem_en"],
        "hyp_en": original["hyp_en"],
        "prem_es": original["prem_es"],
        "hyp_es": original["hyp_es"],
        "prem_rp": parsed.get("prem_rp", original["prem_es"]),
        "hyp_rp": parsed.get("hyp_rp", original["hyp_es"]),
        "type": parsed.get("type", "A"),
        "changes": parsed.get("changes", []) or [],
        "secondary_features": parsed.get("secondary_features", []) or [],
        "cultural_candidates": parsed.get("cultural_candidates", []) or [],
        "review_flag": bool(parsed.get("review_flag", False)),
        "review_note": parsed.get("review_note", "") or "",
        "note": parsed.get("note", "") or "",
    }
    out["lev_prem"] = Levenshtein.distance(out["prem_es"], out["prem_rp"])
    out["lev_hyp"] = Levenshtein.distance(out["hyp_es"], out["hyp_rp"])
    out["lev_total"] = out["lev_prem"] + out["lev_hyp"]
    return out


def apply_slice(instances: list[dict], offset: int, limit: int | None) -> list[dict]:
    if offset:
        instances = instances[offset:]
    if limit is not None:
        instances = instances[:limit]
    return instances


def write_report(out_path: Path, rows: list[dict], failed: list[dict], config_label: str) -> None:
    if not rows and not failed:
        return
    by_type = {"A": [], "B": [], "C": [], "D": [], "?": []}
    for r in rows:
        t = r.get("type", "?")
        by_type.setdefault(t, []).append(r)

    def stats(values: list[int]) -> tuple[float, float, int]:
        if not values:
            return 0.0, 0.0, 0
        s = sorted(values)
        mean = sum(s) / len(s)
        median = s[len(s) // 2] if len(s) % 2 else (s[len(s)//2 - 1] + s[len(s)//2]) / 2
        return mean, median, max(s)

    lines = [f"# Reporte: {config_label}", "", f"Total procesadas: {len(rows)}", f"Fallidas: {len(failed)}", "", "## Distribución por tipo", ""]
    lines.append("| Tipo | N | % |")
    lines.append("|------|---|---|")
    total = max(len(rows), 1)
    for t in ["A", "B", "C", "D", "E", "?"]:
        n = len(by_type.get(t, []))
        if n:
            lines.append(f"| {t} | {n} | {n/total*100:.1f}% |")

    lines += ["", "## Levenshtein por tipo", "", "| Tipo | mean | median | max |", "|------|------|--------|-----|"]
    for t in ["A", "B", "C", "D", "E"]:
        items = by_type.get(t, [])
        if items:
            mean, median, mx = stats([r["lev_total"] for r in items])
            lines.append(f"| {t} | {mean:.2f} | {median:.1f} | {mx} |")
    if rows:
        mean, median, mx = stats([r["lev_total"] for r in rows])
        lines.append(f"| **Global** | **{mean:.2f}** | **{median:.1f}** | **{mx}** |")

    if failed:
        lines += ["", "## Instancias fallidas", ""]
        for f in failed:
            lines.append(f"- idx {f['idx']}: {f['error']}")

    out_path.write_text("\n".join(lines), encoding="utf-8")


def update_global_summary(summary_path: Path, config_label: str, rows: list[dict], failed: list[dict]) -> None:
    summary = {}
    if summary_path.exists():
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except Exception:
            summary = {}

    by_type_count = {"A": 0, "B": 0, "C": 0, "D": 0}
    lev_values = []
    for r in rows:
        t = r.get("type", "?")
        if t in by_type_count:
            by_type_count[t] += 1
        lev_values.append(r["lev_total"])

    summary[config_label] = {
        "n_processed": len(rows),
        "n_failed": len(failed),
        "type_distribution": by_type_count,
        "lev_total_mean": sum(lev_values) / len(lev_values) if lev_values else 0.0,
        "lev_total_max": max(lev_values) if lev_values else 0,
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")


def translate_realtime(
    args,
    client: genai.Client,
    model_name: str,
    temperature: float,
    variant: str,
    instances: list[dict],
    prefix: str = "",
) -> None:
    config_label = f"{prefix}{model_name}__T{temperature}__{variant}"
    out_path = EXPERIMENTS_DIR / f"{config_label}.jsonl"
    failed_path = EXPERIMENTS_DIR / f"failed_{config_label}.jsonl"
    report_path = EXPERIMENTS_DIR / f"report_{config_label}.md"

    EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)
    template = load_prompt_template(variant)

    done = already_processed_idxs(out_path)
    pending = [r for r in instances if r["idx"] not in done]
    if args.limit is not None:
        pending = pending[:args.limit]

    print(f"\n[{config_label}] {len(pending)} instancias pendientes ({len(done)} ya hechas).")
    if not pending:
        print(f"[{config_label}] Nada por hacer.")
        # igual reescribimos reporte/summary con lo existente
        existing_rows = load_jsonl(out_path) if out_path.exists() else []
        existing_failed = load_jsonl(failed_path) if failed_path.exists() else []
        write_report(report_path, existing_rows, existing_failed, config_label)
        update_global_summary(EXPERIMENTS_DIR / "experiments_summary.json", config_label, existing_rows, existing_failed)
        return

    pbar = tqdm(total=len(pending), desc=config_label)
    for batch_start in range(0, len(pending), args.batch_size):
        batch = pending[batch_start:batch_start + args.batch_size]
        for row in batch:
            user_msg = build_user_message(template, row, args.include_english)
            try:
                parsed = call_gemini_with_retries(client, model_name, temperature, user_msg)
                normalized = normalize_response(parsed, row)
                append_jsonl(out_path, normalized)
            except Exception as e:
                append_jsonl(failed_path, {"idx": row["idx"], "error": str(e)[:500]})
            pbar.update(1)
        if batch_start + args.batch_size < len(pending):
            time.sleep(args.batch_pause)
    pbar.close()

    rows = load_jsonl(out_path)
    failed = load_jsonl(failed_path) if failed_path.exists() else []
    write_report(report_path, rows, failed, config_label)
    update_global_summary(EXPERIMENTS_DIR / "experiments_summary.json", config_label, rows, failed)
    print(f"[{config_label}] OK. Outputs en {out_path}, reporte en {report_path}.")


def _parse_json_text(text: str) -> dict:
    """Parsea JSON de una respuesta de texto, limpiando markdown fences si es necesario."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()
        return json.loads(cleaned)


def translate_batch(
    args,
    client: genai.Client,
    model_name: str,
    temperature: float,
    variant: str,
    instances: list[dict],
    prefix: str = "",
) -> None:
    """Traducción via Gemini Batch API — async, ~50% más barato que realtime."""
    from datetime import datetime, timezone

    config_label = f"{prefix}{model_name}__T{temperature}__{variant}"
    out_path = EXPERIMENTS_DIR / f"{config_label}.jsonl"
    failed_path = EXPERIMENTS_DIR / f"failed_{config_label}.jsonl"
    report_path = EXPERIMENTS_DIR / f"report_{config_label}.md"
    state_path = EXPERIMENTS_DIR / f"{config_label}.batch_job.json"

    EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)
    template = load_prompt_template(variant)

    done = already_processed_idxs(out_path)
    pending = [r for r in instances if r["idx"] not in done]
    if args.limit is not None:
        pending = pending[:args.limit]

    print(f"\n[{config_label}] batch mode. {len(pending)} instancias pendientes ({len(done)} ya hechas).")

    if not pending:
        print(f"[{config_label}] Nada por hacer.")
        existing_rows = load_jsonl(out_path) if out_path.exists() else []
        existing_failed = load_jsonl(failed_path) if failed_path.exists() else []
        write_report(report_path, existing_rows, existing_failed, config_label)
        update_global_summary(EXPERIMENTS_DIR / "experiments_summary.json", config_label, existing_rows, existing_failed)
        return

    idx_map = {row["idx"]: row for row in pending}

    if args.resume:
        job_name = args.resume
        print(f"[batch] Retomando job: {job_name}")
        batch_job = client.batches.get(name=job_name)
    else:
        inline_requests = [
            {
                "model": model_name,
                "contents": [{"role": "user", "parts": [{"text": build_user_message(template, row, args.include_english)}]}],
                "metadata": {"idx": str(row["idx"])},
                "config": {"temperature": temperature, "response_mime_type": "application/json"},
            }
            for row in pending
        ]
        print(f"[batch] Enviando {len(inline_requests)} requests...")
        _MAX_429_RETRIES = 30
        _RETRY_WAIT = 120  # segundos entre reintentos
        batch_job = None
        for _attempt in range(_MAX_429_RETRIES):
            try:
                batch_job = client.batches.create(
                    model=model_name,
                    src=inline_requests,
                    config={"display_name": config_label},
                )
                break
            except Exception as _e:
                if "429" in str(_e) or "RESOURCE_EXHAUSTED" in str(_e):
                    from datetime import datetime as _dt
                    _ts = _dt.now().strftime("%H:%M:%S")
                    print(f"  [{_ts}] 429 RESOURCE_EXHAUSTED — esperando {_RETRY_WAIT}s (intento {_attempt+1}/{_MAX_429_RETRIES})...", flush=True)
                    time.sleep(_RETRY_WAIT)
                else:
                    raise
        if batch_job is None:
            raise RuntimeError(f"[batch] No se pudo crear el job tras {_MAX_429_RETRIES} intentos ({_MAX_429_RETRIES * _RETRY_WAIT / 60:.0f} min de espera).")
        state_path.write_text(
            json.dumps({
                "job_name": batch_job.name,
                "model": model_name,
                "temperature": temperature,
                "variant": variant,
                "n_instances": len(pending),
                "submitted_at": datetime.now(timezone.utc).isoformat(),
                "status": "submitted",
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[batch] Job creado: {batch_job.name}. Estado guardado en {state_path.name}.")
        print(f"[batch] Reanudar con: --resume {batch_job.name}")

    # Poll hasta completar
    deadline = time.time() + args.poll_timeout * 3600
    while not batch_job.done:
        if time.time() > deadline:
            raise TimeoutError(f"[batch] Timeout ({args.poll_timeout}h). Job: {batch_job.name}")
        time.sleep(args.poll_interval)
        batch_job = client.batches.get(name=batch_job.name)
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S")
        counts = getattr(batch_job, "request_counts", None)
        if counts and getattr(counts, "total", 0):
            print(f"  [{ts}] {batch_job.state.name} — {counts.completed}/{counts.total} completados, {counts.failed} fallidos", flush=True)
        else:
            print(f"  [{ts}] {batch_job.state.name}", flush=True)

    if batch_job.state.name in ("JOB_STATE_FAILED", "JOB_STATE_CANCELLED"):
        err = getattr(batch_job, "error", None)
        print(f"[batch] Job terminó con error: {err}", file=sys.stderr)
        if state_path.exists():
            s = json.loads(state_path.read_text(encoding="utf-8"))
            s["status"] = batch_job.state.name
            state_path.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
        sys.exit(1)

    # Recolectar resultados
    print(f"[batch] Job completado. Procesando respuestas...")
    for inlined_resp in (batch_job.dest.inlined_responses or []):
        idx = int(inlined_resp.metadata["idx"])
        original = idx_map.get(idx)
        if original is None:
            continue
        if inlined_resp.error:
            append_jsonl(failed_path, {"idx": idx, "error": str(inlined_resp.error)[:500]})
            continue
        try:
            text = inlined_resp.response.candidates[0].content.parts[0].text
            parsed = _parse_json_text(text)
            normalized = normalize_response(parsed, original)
            append_jsonl(out_path, normalized)
        except Exception as e:
            append_jsonl(failed_path, {"idx": idx, "error": str(e)[:500]})

    if state_path.exists():
        s = json.loads(state_path.read_text(encoding="utf-8"))
        s["status"] = "done"
        state_path.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")

    rows = load_jsonl(out_path)
    failed = load_jsonl(failed_path) if failed_path.exists() else []
    write_report(report_path, rows, failed, config_label)
    update_global_summary(EXPERIMENTS_DIR / "experiments_summary.json", config_label, rows, failed)
    print(f"[{config_label}] OK. Outputs en {out_path}, reporte en {report_path}.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Harness de traducción XNLI ES → RP con Gemini.")
    parser.add_argument("--models", nargs="+", default=["gemini-2.5-flash"])
    parser.add_argument("--temperatures", nargs="+", type=float, default=[0.1],
                        help="Temperatura(s). Default 0.1; usar 0.3 solo para ablaciones puntuales.")
    parser.add_argument("--prompt-variants", nargs="+", default=["v2"])
    parser.add_argument("--dev_200", action="store_true",
                        help=f"Usa el dev canónico 200 como input ({DEV_200}).")
    parser.add_argument("--input", type=Path, default=None,
                        help="JSONL de input arbitrario (ej. xnli_full_7500.jsonl).")
    parser.add_argument("--offset", type=int, default=0,
                        help="Saltea las primeras N instancias.")
    parser.add_argument("--limit", type=int, default=None,
                        help="Procesa solo las primeras N instancias.")
    parser.add_argument("--include-english", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--batch-pause", type=float, default=0.0)
    parser.add_argument("--batch-mode", action="store_true",
                        help="Usa el Gemini Batch API (async, ~50%% más barato).")
    parser.add_argument("--poll-interval", type=int, default=60,
                        help="Segundos entre polls al batch job (default 60).")
    parser.add_argument("--poll-timeout", type=int, default=24,
                        help="Horas máximas de espera del batch job (default 24).")
    parser.add_argument("--resume", type=str, default=None,
                        help="Retomar batch job en curso (ej: 'batches/abc123').")
    args = parser.parse_args()

    load_dotenv(REPO_ROOT / ".env")
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY no definida en .env", file=sys.stderr)
        return 1
    client = genai.Client(api_key=api_key)

    if args.dev_200:
        instances = apply_slice(load_jsonl(DEV_200), args.offset, None)
        prefix = "xnli_combined_dev_200__"
        print(f"Modo dev_200: {len(instances)} instancias desde {DEV_200.name}.")
    elif args.input:
        instances = apply_slice(load_jsonl(args.input), args.offset, None)
        prefix = f"{args.input.stem}__"
        print(f"Input: {len(instances)} instancias desde {args.input.name}.")
    else:
        parser.error("Especificá --dev_200 o --input <path>.")

    for model_name, temp, variant in product(args.models, args.temperatures, args.prompt_variants):
        if args.batch_mode or args.resume:
            translate_batch(args, client, model_name, temp, variant, instances, prefix=prefix)
        else:
            translate_realtime(args, client, model_name, temp, variant, instances, prefix=prefix)

    return 0


if __name__ == "__main__":
    sys.exit(main())
