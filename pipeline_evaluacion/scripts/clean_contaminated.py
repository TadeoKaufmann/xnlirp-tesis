"""
clean_contaminated.py
Lee Respuestas_contaminadas_testeos.csv y genera:
  1. Un reporte de anotaciones útiles (palabras_marcadas + comentarios)
  2. SQL para borrar los rows de Respuestas + reservas contaminados
"""

import csv
import json
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent
CSV_PATH = ROOT / "respuestas_anotadores" / "Respuestas_contaminadas_testeos.csv"
OUT_DIR  = ROOT / "respuestas_anotadores"

with open(CSV_PATH, encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

print(f"Total rows: {len(rows)}")

# ── 1. Extraer datos útiles ───────────────────────────────────────────────────

useful = []
for row in rows:
    try:
        palabras = json.loads(row.get("palabras_marcadas") or "[]")
    except Exception:
        palabras = []

    comentario_prem = (row.get("comentario_prem") or "").strip()
    comentario_hyp  = (row.get("comentario_hyp")  or "").strip()

    if palabras or comentario_prem or comentario_hyp:
        useful.append({
            "csv_id":        row["id"],
            "idx":           int(row["idx"]),
            "respuesta":     row.get("respuesta", ""),
            "palabras_marcadas": palabras,
            "comentario_prem":   comentario_prem,
            "comentario_hyp":    comentario_hyp,
            "anotador_id":       row["anotador_id"],
            "created_at":        row["created_at"],
        })

useful.sort(key=lambda x: x["idx"])

# Guardar reporte legible
report_lines = [
    "# Anotaciones útiles extraídas de Respuestas_contaminadas_testeos.csv",
    f"# Total rows contaminados: {len(rows)}",
    f"# Rows con datos útiles: {len(useful)}",
    "",
]
for u in useful:
    report_lines.append(f"## idx={u['idx']}  (csv_id={u['csv_id']}, respuesta={u['respuesta']})")
    if u["palabras_marcadas"]:
        palabras_str = ", ".join(
            f"{p['palabra']} [{p['source']}]"
            for p in u["palabras_marcadas"]
            if isinstance(p, dict)
        )
        report_lines.append(f"  palabras_marcadas: {palabras_str}")
    if u["comentario_prem"]:
        report_lines.append(f"  comentario_prem:   {u['comentario_prem']}")
    if u["comentario_hyp"]:
        report_lines.append(f"  comentario_hyp:    {u['comentario_hyp']}")
    report_lines.append("")

report_path = OUT_DIR / "anotaciones_utiles_de_contaminados.md"
with open(report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines))
print(f"Reporte guardado: {report_path}")

# ── 2. Generar SQL de limpieza ────────────────────────────────────────────────

all_ids        = sorted(int(r["id"]) for r in rows)
all_anotador   = sorted(set(r["anotador_id"] for r in rows))
idxs_afectados = sorted(set(int(r["idx"]) for r in rows))

ids_sql        = ", ".join(str(i) for i in all_ids)
anotadores_sql = ", ".join(f"'{a}'" for a in all_anotador)

sql = f"""-- =============================================================
-- Limpieza de Respuestas y reservas contaminadas por testeos
-- Generado por clean_contaminated.py
-- Filas afectadas en Respuestas: {len(all_ids)}
-- Anotadores contaminados: {len(all_anotador)}
-- Instancias que quedan libres: {len(idxs_afectados)}
-- =============================================================

-- 1. Borrar respuestas contaminadas
DELETE FROM "Respuestas"
WHERE id IN ({ids_sql});

-- 2. Liberar reservas de anotadores contaminados
DELETE FROM reservas
WHERE anotador_id IN ({anotadores_sql});

-- Verificación (debería devolver 0 para ambas):
SELECT COUNT(*) AS respuestas_contaminadas_restantes
FROM "Respuestas" WHERE id IN ({ids_sql});

SELECT COUNT(*) AS reservas_contaminadas_restantes
FROM reservas WHERE anotador_id IN ({anotadores_sql});
"""

sql_path = OUT_DIR / "cleanup_contaminados.sql"
with open(sql_path, "w", encoding="utf-8") as f:
    f.write(sql)
print(f"SQL guardado: {sql_path}")

# ── 3. Resumen ────────────────────────────────────────────────────────────────
print(f"\nResumen:")
print(f"  Rows a borrar de Respuestas: {len(all_ids)}")
print(f"  Anotadores a limpiar de reservas: {len(all_anotador)}")
print(f"  Instancias que quedan libres para re-anotación: {len(idxs_afectados)}")
print(f"  Rows con palabras_marcadas o comentarios útiles: {len(useful)}")
print(f"\nPróximos pasos:")
print(f"  1. Revisar {report_path.name}")
print(f"  2. Ejecutar {sql_path.name} en Supabase SQL Editor")
print(f"  3. Las instancias quedan disponibles automáticamente en la app")
