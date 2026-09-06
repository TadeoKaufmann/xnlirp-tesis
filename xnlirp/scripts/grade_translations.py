"""
grade_translations.py — Evalúa traducciones XNLI ES→RP.

OpenAI (default): usa Batch API async (50% descuento).
Anthropic: usa API sincrónica (solo para pruebas rápidas).

Uso:
    python pipeline_evaluacion/scripts/grade_translations.py \
        --input results/experiments/mi_batch.jsonl \
        --model gpt-4o-mini --provider openai \
        --batch 10 --output results/experiments/grader_output

    # Reanudar un batch job interrumpido:
    python ... --resume-batch-id batch_abc123

Requiere: OPENAI_API_KEY o ANTHROPIC_API_KEY en .env
"""

import argparse
import io
import json
import os
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import anthropic
try:
    import openai as openai_lib
except ImportError:
    openai_lib = None
from dotenv import load_dotenv

load_dotenv()

PROMPT_PATH = Path(__file__).parent / "prompts" / "grader_prompt.txt"
DEFAULT_GOLD = Path("data/dev/xnli_combined_dev_200.jsonl")
DEFAULT_OUTPUT_DIR = Path("results/experiments/grader_output")
POLL_INTERVAL = 30  # segundos entre polls

VALID_VERDICTS = {"ok", "missing_change", "wrong_type", "nli_broken", "bad_rp", "wrong_flag", "multiple"}


def load_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def build_gold_index(gold_path: Path | None) -> dict[int, dict]:
    if gold_path is None or not gold_path.exists():
        return {}
    return {obj["idx"]: obj for obj in load_jsonl(gold_path)}


def build_prompt(grader_template: str, instances: list[dict], gold_index: dict) -> str:
    gold_items = [gold_index[inst["idx"]] for inst in instances if inst.get("idx") in gold_index]
    gold_block = "\n".join(json.dumps(g, ensure_ascii=False) for g in gold_items) if gold_items else "(no gold disponible)"
    modelo_block = "\n".join(json.dumps(m, ensure_ascii=False) for m in instances)
    return grader_template.replace("{{GOLD}}", gold_block).replace("{{MODELO}}", modelo_block)


def parse_verdicts(response_text: str) -> list[dict]:
    verdicts = []
    i = 0
    while i < len(response_text):
        if response_text[i] == "{":
            depth, j = 0, i
            while j < len(response_text):
                if response_text[j] == "{":
                    depth += 1
                elif response_text[j] == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            obj = json.loads(response_text[i:j+1])
                            if "verdict" in obj and "idx" in obj:
                                verdicts.append(obj)
                        except json.JSONDecodeError:
                            pass
                        i = j + 1
                        break
                j += 1
            else:
                i += 1
        else:
            i += 1
    return verdicts


def aggregate_report(all_verdicts: list[dict], batch_name: str) -> str:
    total = len(all_verdicts)
    if total == 0:
        return "No se procesaron instancias."
    counts = Counter(v.get("verdict", "unknown") for v in all_verdicts)
    accuracy = counts.get("ok", 0) / total * 100
    vs_gold = Counter(v.get("vs_gold", "no_gold") for v in all_verdicts)
    div_type = Counter(
        v.get("gold_divergence_type") for v in all_verdicts
        if v.get("gold_divergence_type") and v.get("gold_divergence_type") != "null"
    )
    all_issues: list[str] = []
    for v in all_verdicts:
        all_issues.extend(v.get("issues", []))
    issue_counts = Counter(all_issues).most_common(5)
    lines = [
        f"# Reporte grader — {batch_name}",
        f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Resumen",
        f"- Total evaluado: {total}",
        f"- ok: {counts.get('ok',0)} | missing_change: {counts.get('missing_change',0)} | wrong_type: {counts.get('wrong_type',0)} | nli_broken: {counts.get('nli_broken',0)} | bad_rp: {counts.get('bad_rp',0)} | other: {sum(v for k,v in counts.items() if k not in VALID_VERDICTS)}",
        f"- Accuracy (ok/total): {accuracy:.1f}%",
        "",
        "## Divergencias vs gold",
        f"- matches: {vs_gold.get('matches',0)} | differs: {vs_gold.get('differs',0)} | no_gold: {vs_gold.get('no_gold',0)}",
        f"- gold_outdated: {div_type.get('gold_outdated',0)} | model_wrong: {div_type.get('model_wrong',0)} | ambiguous: {div_type.get('ambiguous',0)}",
        "",
        "## Issues más frecuentes",
    ]
    for issue, cnt in issue_counts:
        lines.append(f"- ({cnt}x) {issue}")
    return "\n".join(lines)


# ── OpenAI Batch API ──────────────────────────────────────────────────────────

def build_openai_batch_jsonl(grader_template: str, instances: list[dict], gold_index: dict,
                              batch_size: int, model: str) -> bytes:
    lines = []
    for i in range(0, len(instances), batch_size):
        group = instances[i:i+batch_size]
        prompt = build_prompt(grader_template, group, gold_index)
        request = {
            "custom_id": f"grader-{i}-{i+len(group)-1}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": model,
                "max_tokens": 4096,
                "temperature": 0,
                "messages": [{"role": "user", "content": prompt}],
            },
        }
        lines.append(json.dumps(request, ensure_ascii=False))
    return "\n".join(lines).encode("utf-8")


def submit_openai_batch(client, batch_jsonl: bytes, batch_name: str) -> str:
    print("[batch] Subiendo archivo de requests...")
    file_obj = client.files.create(
        file=(f"{batch_name}.jsonl", io.BytesIO(batch_jsonl), "application/jsonl"),
        purpose="batch",
    )
    print(f"[batch] Archivo subido: {file_obj.id}")
    batch = client.batches.create(
        input_file_id=file_obj.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
        metadata={"description": batch_name},
    )
    print(f"[batch] Job creado: {batch.id} — estado: {batch.status}")
    return batch.id


def poll_openai_batch(client, batch_id: str):
    terminal = {"completed", "failed", "expired", "cancelled"}
    while True:
        batch = client.batches.retrieve(batch_id)
        counts = batch.request_counts
        print(f"  [{datetime.now().strftime('%H:%M:%S')}] {batch.status} — "
              f"{counts.completed}/{counts.total} completados, {counts.failed} fallidos", flush=True)
        if batch.status in terminal:
            return batch
        time.sleep(POLL_INTERVAL)


def run_openai_batch(client, grader_template: str, instances: list[dict], gold_index: dict,
                     batch_size: int, model: str, batch_name: str, state_path: Path,
                     resume_batch_id: str | None) -> list[dict]:
    if resume_batch_id:
        batch_id = resume_batch_id
        print(f"[batch] Retomando job: {batch_id}")
    else:
        batch_jsonl = build_openai_batch_jsonl(grader_template, instances, gold_index, batch_size, model)
        n_requests = batch_jsonl.count(b"\n") + 1
        print(f"[batch] {n_requests} requests — {len(batch_jsonl)/1024:.1f} KB")
        batch_id = submit_openai_batch(client, batch_jsonl, batch_name)
        state_path.write_text(json.dumps({
            "batch_id": batch_id,
            "model": model,
            "n_instances": len(instances),
            "submitted_at": datetime.now().isoformat(),
        }, indent=2), encoding="utf-8")
        print(f"[batch] Estado en {state_path.name}. Reanudar con: --resume-batch-id {batch_id}")

    print("[batch] Esperando resultados (polling cada 30s)...")
    batch = poll_openai_batch(client, batch_id)

    if batch.status != "completed":
        print(f"ERROR: batch terminó con estado '{batch.status}'", file=sys.stderr)
        return []

    content = client.files.content(batch.output_file_id).text
    all_verdicts = []
    for line in content.splitlines():
        if not line.strip():
            continue
        try:
            result = json.loads(line)
            text = result["response"]["body"]["choices"][0]["message"]["content"]
            all_verdicts.extend(parse_verdicts(text))
        except (KeyError, IndexError, json.JSONDecodeError):
            pass

    print(f"[batch] {len(all_verdicts)} veredictos parseados.")
    return all_verdicts


# ── Anthropic sync (solo pruebas) ─────────────────────────────────────────────

def run_anthropic_sync(client, grader_template: str, instances: list[dict], gold_index: dict,
                       batch_size: int, model: str) -> list[dict]:
    all_verdicts = []
    print(f"Evaluando {len(instances)} instancias con {model} (sync, batch={batch_size})...")
    for i in range(0, len(instances), batch_size):
        group = instances[i:i+batch_size]
        prompt = build_prompt(grader_template, group, gold_index)
        print(f"  {i}–{min(i+batch_size, len(instances))-1}", end=" ", flush=True)
        msg = client.messages.create(model=model, max_tokens=4096,
                                     messages=[{"role": "user", "content": prompt}],
                                     temperature=0)
        verdicts = parse_verdicts(msg.content[0].text)
        all_verdicts.extend(verdicts)
        print(f"→ {len(verdicts)}")
    return all_verdicts


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Grader XNLI ES→RP")
    parser.add_argument("--input", required=True, help="JSONL de Gemini a evaluar")
    parser.add_argument("--gold", default=str(DEFAULT_GOLD))
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--provider", default="openai", choices=["anthropic", "openai"])
    parser.add_argument("--batch", type=int, default=10, help="Instancias por request")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--resume-batch-id", default=None, help="Reanudar batch job existente")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not PROMPT_PATH.exists():
        print(f"ERROR: prompt no encontrado en {PROMPT_PATH}", file=sys.stderr)
        sys.exit(1)

    grader_template = PROMPT_PATH.read_text(encoding="utf-8")
    instances = load_jsonl(input_path)
    gold_index = build_gold_index(Path(args.gold) if args.gold else None)

    if args.offset:
        instances = instances[args.offset:]
    if args.limit:
        instances = instances[:args.limit]

    batch_name = input_path.stem
    output_jsonl = output_dir / f"{batch_name}_graded.jsonl"
    output_report = output_dir / f"{batch_name}_grader_report.md"
    state_path = output_dir / f"{batch_name}_batch_state.json"

    if args.provider == "openai":
        if openai_lib is None:
            print("ERROR: pip install openai", file=sys.stderr)
            sys.exit(1)
        client = openai_lib.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        all_verdicts = run_openai_batch(
            client, grader_template, instances, gold_index,
            args.batch, args.model, batch_name, state_path, args.resume_batch_id,
        )
    else:
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        all_verdicts = run_anthropic_sync(
            client, grader_template, instances, gold_index, args.batch, args.model,
        )

    all_verdicts.sort(key=lambda x: x.get("idx", 0))

    with open(output_jsonl, "w", encoding="utf-8") as f:
        for v in all_verdicts:
            f.write(json.dumps(v, ensure_ascii=False) + "\n")

    report = aggregate_report(all_verdicts, batch_name)
    output_report.write_text(report, encoding="utf-8")

    print(f"\nSalida:")
    print(f"  Veredictos: {output_jsonl}")
    print(f"  Reporte:    {output_report}")
    print(f"\n{report}")


if __name__ == "__main__":
    main()
