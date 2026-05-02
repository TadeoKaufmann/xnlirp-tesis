"""
Loop de optimización automática del prompt.
Itera: traducir 30 gold → evaluar → meta-prompt para Gemini reescriba el prompt → repetir.
Early stopping si dos iteraciones consecutivas no mejoran.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
import google.generativeai as genai


REPO_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = REPO_ROOT / "scripts" / "prompts"
EXPERIMENTS_DIR = REPO_ROOT / "results" / "experiments"
EVOLUTION_LOG = EXPERIMENTS_DIR / "prompt_evolution.md"


META_PROMPT_TEMPLATE = """Sos un ingeniero de prompts experto. Te paso un prompt de adaptación dialectal ES→rioplatense que está siendo usado por gemini-2.5-flash, junto con el reporte de errores actual contra un gold anotado manualmente. Tu tarea es generar una VERSIÓN MEJORADA del prompt que reduzca los errores observados, manteniendo:

- La estructura general (principio rector, restricciones, reglas, tipología, ejemplos, output)
- Los 3 few-shots existentes (idx 1638, 910, 2821) — NO los modifiques ni los elimines
- El formato de output JSON estricto
- Las restricciones duras

Podés:
- Aclarar reglas que el modelo no sigue bien
- Agregar contraejemplos breves dentro de las reglas (ej. "NO hagas X porque Y")
- Mejorar redacción de la tipología si hay confusión sistemática entre tipos
- Reordenar prioridades si conviene
- Agregar advertencias explícitas para errores frecuentes

PROMPT ACTUAL:
================================================================
{CURRENT_PROMPT}
================================================================

REPORTE DE ERRORES (evaluación contra gold):
================================================================
{EVAL_REPORT}
================================================================

PATRONES DE ERROR DETECTADOS:
{PATTERNS}

DEVOLVÉ EL PROMPT MEJORADO COMPLETO. Antes del prompt, agregá UN BLOQUE DELIMITADO así:

<<<CHANGELOG>>>
- Cambio 1: descripción breve de qué cambió y por qué
- Cambio 2: ...
<<<END_CHANGELOG>>>

Y después de ese bloque, el prompt completo (sin el changelog adentro).
"""


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def detect_patterns(eval_result: dict) -> str:
    """Heurística simple para detectar patrones de error."""
    patterns = []
    confusion = eval_result.get("confusion", {})
    by_type_acc = eval_result.get("type_accuracy_by_gold_type", {})

    # Errores frecuentes de tipo
    for gt, preds in confusion.items():
        for pt, count in preds.items():
            if gt != pt and count >= 2:
                patterns.append(f"- El modelo confunde gold tipo {gt} con pred tipo {pt} ({count} casos)")

    for t, acc in by_type_acc.items():
        n = eval_result.get("type_count_by_gold", {}).get(t, 0)
        if n > 0 and acc < 0.7:
            patterns.append(f"- Baja accuracy en tipo {t}: {acc*100:.0f}% sobre {n} instancias")

    if eval_result.get("lev_delta_mean", 0) > 5:
        patterns.append(f"- Levenshtein delta promedio alto: {eval_result['lev_delta_mean']:.2f} — el modelo está sobre/sub-editando")

    return "\n".join(patterns) if patterns else "- No se detectaron patrones sistemáticos claros."


def parse_meta_response(text: str) -> tuple[str, str]:
    """Extrae changelog y nuevo prompt."""
    start = text.find("<<<CHANGELOG>>>")
    end = text.find("<<<END_CHANGELOG>>>")
    if start == -1 or end == -1:
        return "", text
    changelog = text[start + len("<<<CHANGELOG>>>"):end].strip()
    new_prompt = text[end + len("<<<END_CHANGELOG>>>"):].strip()
    return changelog, new_prompt


def append_evolution_log(version: int, parent_variant: str, metric_value: float, changelog: str) -> None:
    EVOLUTION_LOG.parent.mkdir(parents=True, exist_ok=True)
    if not EVOLUTION_LOG.exists():
        EVOLUTION_LOG.write_text("# Evolución del prompt\n\n", encoding="utf-8")
    block = (
        f"## v{version} (derivado de {parent_variant}) — {datetime.now().isoformat(timespec='seconds')}\n\n"
        f"Métrica observada: {metric_value:.4f}\n\n"
        f"**Cambios introducidos:**\n{changelog}\n\n"
        f"---\n\n"
    )
    with EVOLUTION_LOG.open("a", encoding="utf-8") as f:
        f.write(block)


def run_translate(variant: str, temperature: float, model_name: str) -> Path:
    cmd = [
        sys.executable, str(REPO_ROOT / "scripts" / "translate_xnli_pilot.py"),
        "--limit-to-gold",
        "--models", model_name,
        "--temperatures", str(temperature),
        "--prompt-variants", variant,
    ]
    print(">>", " ".join(cmd))
    subprocess.check_call(cmd)
    return EXPERIMENTS_DIR / f"{model_name}__T{temperature}__{variant}.jsonl"


def run_eval(run_path: Path) -> dict:
    from scripts.evaluate_against_gold import evaluate_run, GOLD_30, load_jsonl as _ljsonl  # type: ignore
    # Import-by-path workaround:
    sys.path.insert(0, str(REPO_ROOT))
    from scripts.evaluate_against_gold import evaluate_run as _eval, GOLD_30 as _GOLD  # type: ignore
    gold = _ljsonl(_GOLD)
    return _eval(run_path, gold)


def metric_value(eval_result: dict, metric: str) -> float:
    if metric == "type_accuracy":
        return eval_result.get("type_accuracy", 0.0)
    elif metric == "lev_delta":
        # Para "lev_delta" queremos minimizar → invertimos signo para tener "más es mejor"
        return -eval_result.get("lev_delta_mean", 0.0)
    raise ValueError(f"Métrica desconocida: {metric}")


def call_meta_prompt(model: genai.GenerativeModel, current_prompt: str, eval_md: str, patterns: str) -> tuple[str, str]:
    payload = META_PROMPT_TEMPLATE.format(
        CURRENT_PROMPT=current_prompt,
        EVAL_REPORT=eval_md,
        PATTERNS=patterns,
    )
    resp = model.generate_content(payload)
    return parse_meta_response(resp.text)


def main() -> int:
    parser = argparse.ArgumentParser(description="Loop de optimización del prompt.")
    parser.add_argument("--prompt-variant", default="v1_minimal")
    parser.add_argument("--temperature", type=float, default=0.3)
    parser.add_argument("--model", default="gemini-2.5-flash")
    parser.add_argument("--max-iterations", type=int, default=5)
    parser.add_argument("--metric", choices=["type_accuracy", "lev_delta"], default="type_accuracy")
    args = parser.parse_args()

    load_dotenv(REPO_ROOT / ".env")
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY no definida.", file=sys.stderr)
        return 1
    genai.configure(api_key=api_key)
    meta_model = genai.GenerativeModel(args.model, generation_config={"temperature": 0.4})

    EVOLUTION_LOG.parent.mkdir(parents=True, exist_ok=True)
    current_variant = args.prompt_variant
    history = []  # list of metric values
    no_improve_streak = 0
    best_metric = -float("inf")
    best_variant = current_variant

    sys.path.insert(0, str(REPO_ROOT))
    from scripts.evaluate_against_gold import evaluate_run, GOLD_30, load_jsonl as _ljsonl, render_report  # type: ignore
    gold = _ljsonl(GOLD_30)

    for iteration in range(args.max_iterations):
        print(f"\n========== Iteración {iteration + 1}/{args.max_iterations} (variante: {current_variant}) ==========")
        run_path = run_translate(current_variant, args.temperature, args.model)
        ev = evaluate_run(run_path, gold)
        eval_md_path = EXPERIMENTS_DIR / f"eval_{run_path.stem}.md"
        render_report(ev, eval_md_path)
        m = metric_value(ev, args.metric)
        history.append(m)
        print(f"Métrica ({args.metric}): {m:.4f}")

        if m > best_metric + 1e-6:
            best_metric = m
            best_variant = current_variant
            no_improve_streak = 0
        else:
            no_improve_streak += 1
            if no_improve_streak >= 2:
                print(f"Early stopping: 2 iteraciones sin mejora. Mejor variante: {best_variant} con {best_metric:.4f}")
                break

        if iteration == args.max_iterations - 1:
            break

        current_prompt_path = PROMPTS_DIR / f"prompt_{current_variant}.txt"
        if not current_prompt_path.exists():
            cands = sorted(PROMPTS_DIR.glob(f"prompt_{current_variant}*.txt"))
            if not cands:
                print(f"No se encontró el prompt {current_variant}. Abortando.")
                return 1
            current_prompt_path = cands[0]
        current_prompt = current_prompt_path.read_text(encoding="utf-8")
        eval_md = eval_md_path.read_text(encoding="utf-8")
        patterns = detect_patterns(ev)

        print("Llamando a meta-prompt para generar nueva versión del prompt...")
        changelog, new_prompt = call_meta_prompt(meta_model, current_prompt, eval_md, patterns)
        if not new_prompt:
            print("Meta-prompt no devolvió un prompt válido. Abortando.")
            break

        # Asignar nueva versión: prompt_v3, v4, ...
        existing_versions = [p.stem for p in PROMPTS_DIR.glob("prompt_v*.txt")]
        version_numbers = []
        for s in existing_versions:
            try:
                # Extraer número después de "prompt_v"
                num_str = s.replace("prompt_v", "").split("_")[0]
                version_numbers.append(int(num_str))
            except ValueError:
                pass
        next_version = (max(version_numbers) if version_numbers else 2) + 1
        new_variant = f"v{next_version}_auto"
        new_path = PROMPTS_DIR / f"prompt_{new_variant}.txt"
        new_path.write_text(new_prompt, encoding="utf-8")
        append_evolution_log(next_version, current_variant, m, changelog)
        print(f"Nuevo prompt guardado: {new_path}")
        current_variant = new_variant
        time.sleep(1)

    print(f"\n✅ Loop terminado. Mejor variante: {best_variant} (métrica={best_metric:.4f})")
    print(f"Historial de métricas: {history}")
    print(f"Log de evolución: {EVOLUTION_LOG}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
