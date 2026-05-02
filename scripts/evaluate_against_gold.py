"""
Compara una corrida (o todas) contra el gold de 30 instancias.
Sistema de aprobación de dos capas: type match + Levenshtein delta.
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


REPO_ROOT = Path(__file__).resolve().parent.parent
GOLD_30 = REPO_ROOT / "data" / "processed" / "xnli_pilot_30_annotated.jsonl"
EXPERIMENTS_DIR = REPO_ROOT / "results" / "experiments"


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def evaluate_run(run_path: Path, gold: list[dict], lev_threshold: int = 10) -> dict:
    if not run_path.exists():
        return {"error": f"No existe {run_path}"}
    pred = {r["idx"]: r for r in load_jsonl(run_path)}
    gold_map = {r["idx"]: r for r in gold}

    type_match = 0
    type_total = 0
    confusion = defaultdict(lambda: defaultdict(int))  # gold[t] x pred[t]
    review_items = []
    auto_approved = 0
    by_type_correct = defaultdict(int)
    by_type_total = defaultdict(int)
    lev_deltas = []

    for idx, g in gold_map.items():
        if idx not in pred:
            review_items.append({
                "idx": idx, "status": "MISSING",
                "gold_type": g["type"], "pred_type": None,
                "gold_lev": g["lev_total"], "pred_lev": None,
                "lev_delta": None,
                "detail": "No procesada por el modelo."
            })
            continue
        p = pred[idx]
        type_total += 1
        by_type_total[g["type"]] += 1
        gt = g["type"]
        pt = p.get("type", "?")
        confusion[gt][pt] += 1

        type_ok = (gt == pt)
        if type_ok:
            type_match += 1
            by_type_correct[g["type"]] += 1

        gold_lev = g["lev_total"]
        pred_lev = p.get("lev_total", 0)
        lev_delta = abs(gold_lev - pred_lev)
        lev_deltas.append(lev_delta)

        if gt == "A" and pred_lev == 0 and pt == "A":
            auto_approved += 1
            continue

        if type_ok and lev_delta <= lev_threshold:
            auto_approved += 1
            continue

        status = "⚠️ REVISAR" if type_ok else "❌ ERROR_TIPO"
        review_items.append({
            "idx": idx,
            "status": status,
            "gold_type": gt, "pred_type": pt,
            "gold_lev": gold_lev, "pred_lev": pred_lev,
            "lev_delta": lev_delta,
            "gold_changes": g.get("changes", []),
            "pred_changes": p.get("changes", []),
            "gold_prem_rp": g.get("prem_rp", ""),
            "pred_prem_rp": p.get("prem_rp", ""),
            "gold_hyp_rp": g.get("hyp_rp", ""),
            "pred_hyp_rp": p.get("hyp_rp", ""),
        })

    type_accuracy = type_match / type_total if type_total else 0.0
    by_type_acc = {
        t: (by_type_correct[t] / by_type_total[t]) if by_type_total[t] else 0.0
        for t in ["A", "B", "C", "D"]
    }
    return {
        "run": str(run_path.name),
        "n_evaluated": type_total,
        "type_accuracy": type_accuracy,
        "type_accuracy_by_gold_type": by_type_acc,
        "type_count_by_gold": dict(by_type_total),
        "auto_approved": auto_approved,
        "to_review": len(review_items),
        "lev_delta_mean": (sum(lev_deltas) / len(lev_deltas)) if lev_deltas else 0.0,
        "lev_delta_max": max(lev_deltas) if lev_deltas else 0,
        "confusion": {gt: dict(row) for gt, row in confusion.items()},
        "review_items": review_items,
    }


def render_report(eval_result: dict, out_md: Path) -> None:
    if "error" in eval_result:
        out_md.write_text(f"# Error\n\n{eval_result['error']}\n", encoding="utf-8")
        return
    lines = [
        f"# Evaluación: {eval_result['run']}",
        "",
        f"- Instancias evaluadas: **{eval_result['n_evaluated']}**",
        f"- Type accuracy global: **{eval_result['type_accuracy']*100:.1f}%**",
        f"- Aprobadas automáticamente: **{eval_result['auto_approved']}**",
        f"- Para revisión manual: **{eval_result['to_review']}**",
        f"- Levenshtein delta — mean: {eval_result['lev_delta_mean']:.2f}, max: {eval_result['lev_delta_max']}",
        "",
        "## Type accuracy por tipo (según gold)",
        "",
        "| Tipo | N gold | Accuracy |",
        "|------|--------|----------|",
    ]
    for t in ["A", "B", "C", "D"]:
        n = eval_result["type_count_by_gold"].get(t, 0)
        if n:
            acc = eval_result["type_accuracy_by_gold_type"][t] * 100
            lines.append(f"| {t} | {n} | {acc:.1f}% |")

    lines += ["", "## Confusion matrix (filas=gold, columnas=pred)", ""]
    types = ["A", "B", "C", "D"]
    lines.append("| gold\\pred | " + " | ".join(types) + " |")
    lines.append("|" + "---|" * (len(types) + 1))
    for gt in types:
        row = [eval_result["confusion"].get(gt, {}).get(pt, 0) for pt in types]
        lines.append(f"| {gt} | " + " | ".join(str(v) for v in row) + " |")

    if eval_result["review_items"]:
        lines += ["", "## Instancias para revisión", ""]
        for it in eval_result["review_items"]:
            lines.append(f"### idx {it['idx']} — {it['status']}")
            lines.append(f"- Gold type: `{it['gold_type']}` | Pred type: `{it['pred_type']}`")
            if it.get("lev_delta") is not None:
                lines.append(f"- Lev gold: {it['gold_lev']} | Lev pred: {it['pred_lev']} | Δ = {it['lev_delta']}")
            if "gold_changes" in it:
                lines.append(f"- Gold changes: {it['gold_changes']}")
                lines.append(f"- Pred changes: {it['pred_changes']}")
                lines.append(f"- Gold prem_rp: {it['gold_prem_rp']}")
                lines.append(f"- Pred prem_rp: {it['pred_prem_rp']}")
                lines.append(f"- Gold hyp_rp: {it['gold_hyp_rp']}")
                lines.append(f"- Pred hyp_rp: {it['pred_hyp_rp']}")
            lines.append("")

    out_md.write_text("\n".join(lines), encoding="utf-8")


def render_global_ranking(summary_path: Path, gold: list[dict], lev_threshold: int) -> Path:
    if not summary_path.exists():
        return None
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    rows = []
    for config_label in summary.keys():
        run_path = EXPERIMENTS_DIR / f"{config_label}.jsonl"
        if not run_path.exists():
            continue
        ev = evaluate_run(run_path, gold, lev_threshold=lev_threshold)
        if "error" in ev:
            continue
        rows.append({
            "config": config_label,
            "type_accuracy": ev["type_accuracy"],
            "auto_approved": ev["auto_approved"],
            "to_review": ev["to_review"],
            "lev_delta_mean": ev["lev_delta_mean"],
        })
    rows.sort(key=lambda r: (-r["type_accuracy"], r["lev_delta_mean"]))

    out_md = EXPERIMENTS_DIR / "ranking.md"
    lines = ["# Ranking global de configuraciones", "",
             "| Config | Type acc | Auto-aprob | A revisar | Lev Δ mean |",
             "|--------|----------|------------|-----------|------------|"]
    for r in rows:
        lines.append(f"| `{r['config']}` | {r['type_accuracy']*100:.1f}% | {r['auto_approved']} | {r['to_review']} | {r['lev_delta_mean']:.2f} |")
    out_md.write_text("\n".join(lines), encoding="utf-8")
    return out_md


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluar corrida(s) contra gold de 30 o held-out 70.")
    parser.add_argument("--run", type=Path, default=None,
                        help="Path al .jsonl de una corrida específica.")
    parser.add_argument("--summary", type=Path, default=None,
                        help="Path a experiments_summary.json para evaluar TODAS las configs.")
    parser.add_argument("--gold", type=Path, default=GOLD_30,
                        help="Path al gold JSONL (default: xnli_pilot_30_annotated.jsonl).")
    parser.add_argument("--lev-threshold", type=int, default=10,
                        help="Umbral de tolerancia en delta de Levenshtein (default 10).")
    parser.add_argument("--out-md", type=Path, default=None,
                        help="Path al markdown de salida (solo en modo --run).")
    args = parser.parse_args()

    gold = load_jsonl(args.gold)

    if args.run:
        ev = evaluate_run(args.run, gold, lev_threshold=args.lev_threshold)
        out_md = args.out_md or (args.run.parent / f"eval_{args.run.stem}.md")
        render_report(ev, out_md)
        # imprimir json compacto a stdout
        public = {k: v for k, v in ev.items() if k != "review_items"}
        print(json.dumps(public, indent=2, ensure_ascii=False))
        print(f"\nReporte: {out_md}")

    if args.summary:
        ranking_path = render_global_ranking(args.summary, gold, args.lev_threshold)
        if ranking_path:
            print(f"Ranking: {ranking_path}")

    if not args.run and not args.summary:
        parser.error("Especificá --run o --summary.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
