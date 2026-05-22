# Cronología de datos — XNLIrp

Historial de cómo se construyó el dataset anotado. Cada fase referencia los archivos activos o archivados que la documentan.

---

## Fase 1 — Muestreo del pilot 500 (mayo 2026)

De `data/raw/xnli/xnli_full_7500.jsonl` (5010 test + 2490 val) se extrajo una muestra estratificada de **500 instancias** con seed 42 → `data/raw/xnli/xnli_pilot_500.jsonl`.

Criterio de estratificación: igual proporción de entailment/neutral/contradiction, igual proporción test/val. El archivo se mantiene en `raw/` como marco muestral de referencia.

**Archivos:** `@data/raw/xnli/xnli_pilot_500.jsonl`

---

## Fase 2 — Gold 30: anotación manual (mayo 2026)

De las primeras 30 posiciones del pilot 500 se generó el **gold 30** anotado manualmente por el equipo.

- 3 instancias (idx 1638, 910, 2821) se usaron como few-shots del prompt → conocido leakage del gold.
- El gold 30 es válido solo como sanity check, no como test set.
- Prompt activo en este período: `prompt_v1_minimal.txt`.

*Archivo eliminado* (subsumo en combined dev 200): `xnli_pilot_30_annotated.jsonl`

---

## Fase 3 — Held-out 70 y 100: anotación por Opus 4.7 (mayo 2026)

De las posiciones 30-99 y 100-199 del pilot 500 se generaron dos dev sets anotados por Claude Opus 4.7:

- **Held-out 70** (pos. 30-99): dev set primario para optimización del prompt.
- **Held-out 100** (pos. 100-199): dev set adicional. Distribución final: A 72 / B 6 / C 13 / D 9.

Scripts de anotación: `_annotate_held_out_70.py` / `_annotate_held_out_100.py` (archivados y eliminados).

*Archivos eliminados* (subsumo en combined dev 200): `xnli_held_out_70_raw.jsonl`, `xnli_held_out_100_raw.jsonl`

---

## Fase 4 — Combined dev 200: revisión manual (mayo 2026)

Unión de gold30 + held70 + held100, **revisada y corregida manualmente** por el usuario.

- Correcciones al gold post-facto por reglas E.3 (Captain Blood→Bouchard), pequeña→chica, muletillas (hum→mmm, uh→este…).
- Distribución final: **A 139 / B 19 / C 23 / D 19**.
- Este es el dev set canónico del proyecto. Todo lo anterior (gold30, held70, held100 individuales) queda subsumo aquí.

**Archivos activos:**
- `@data/dev/xnli_combined_dev_200.jsonl`
- Evaluaciones históricas: `@results/experiments/xnli_combined_dev_200__*`

---

## Fase 5 — Iteración de prompts con dev 200 (mayo 2026)

Usando el combined dev 200 como referencia se iteró el prompt en múltiples fases (ver `@pipeline_traduccion/referencias/historial_prompts.md`).

Resultados obtenidos (stale — re-evaluar con prompt actualizado):
- held-out 70: **94.3%** type accuracy (A 95.7 / B 83.3 / C 100 / D 87.5)
- held-out 100: **≈95%**
- gold 30: **93.3%**

Evaluaciones documentadas: `@results/experiments/`

---

## Fase 6 — Análisis léxico del full 7500 (mayo 2026)

Se analizó el vocabulario completo de las 7500 instancias del XNLI full para identificar palabras problemáticas (peninsularismos, nombres anglos, siglas, topónimos).

Resultado: `@results/ranking_vocab_xnli.tsv` (ranking de palabras por frecuencia y categoría).
Pendientes documentados: `@pipeline_traduccion/referencias/_pendientes.md`.

Script usado: `analisis_vocab_xnli.py` (eliminado, trabajo completado).

---

## Fase 7 — Batch cultural por Opus: ~126 instancias (2026-05-14)

Del análisis léxico se identificaron instancias con alta densidad de candidatos culturales (vocativos peninsulares, referentes anglos, eventos específicos, etc.). Estas instancias se extrajeron del full 7500 y se enviaron a Claude Opus para traducción con el **pre-prompt v2 marker-only**.

- Input: 126 instancias → `opus_batch_2026-05-14.jsonl` *(eliminado — trabajo completado y subsumo en cultural_adaptations.jsonl)*
- Output: 126 instancias traducidas → `opus_batch_2026-05-14_translated.jsonl` *(eliminado — subsumo en cultural_adaptations.jsonl)*

Script de extracción: `_scan_cultural_candidates.py` (eliminado).
Script de traducción: `_run_opus_batch_2026-05-14.py` (eliminado).

---

## Fase 8 — Review y decisión sobre nombres anglos (2026-05-15)

Del batch anterior, 51 instancias tenían nombres anglos que Opus mantuvo como type=A (figuras públicas reales: McKim, Gehry, Pickard, Ashcroft, Pynchon, Skeat, Boswell, Lewinsky, etc.).

Se abrió un segundo batch para revisar estas 51 instancias:
- Input: `opus_anglos_batch_2026-05-15.jsonl` *(eliminado)*
- Output: `opus_anglos_batch_2026-05-15_translated.jsonl` *(eliminado — todas salieron type=E)*

**Decisión final** (documentada en `@pipeline_evaluacion/referencias/_review_opus_anglos.txt`):
Mantener todas las figuras públicas reales tal como están. La regla E.1 aplica solo a personajes de ficción no célebres, NO a personas históricas/científicas/políticas reales. Pachuco/pachuca y yiddish: sin equivalente RP directo, mantener.

Script de re-anotación: `_run_opus_anglos_2026-05-15.py` (eliminado).

---

## Fase 9 — Consolidación cultural: 394 instancias (mayo 2026)

Todas las instancias culturalmente complejas procesadas por Opus (batches de las Fases 7 y 8 más otros pases) se consolidaron en:

**`@data/dev/cultural_adaptations.jsonl`** — 394 instancias, todas del full 7500, con adaptaciones culturales tipo E aplicadas o marcadas por Opus.

Este archivo representa el trabajo cultural completo previo a la escala total del pipeline Gemini.

---

## Fase 10 — Sample 300: Gemini v2 + validación Sonnet (2026-05-14)

Se tomó una muestra de 300 instancias del full 7500 (distintas al pilot 500) y se tradujeron con **Gemini 2.5 Flash + prompt v2_cultural_inline** a T=0.1.

- Traducción automática: Gemini 2.5 Flash
- Validación: Claude Sonnet como juez de calidad (89.4% aprobadas → 15 casos rechazados/revisados, ver `@pipeline_evaluacion/referencias/_review_gemini.txt`)
- SQL de carga: `@validation_app/upload_sql/replace_all_sample_300_2026-05-14.sql`

**Estas 300 instancias son las que están actualmente cargadas en la validation app (Vercel).**

**Archivos activos:**
- `@data/dev/xnli_sample_300_v2_test.jsonl`
- `@results/experiments/xnli_sample_300_v2_test__gemini-2.5-flash__T0.1__v2.jsonl`
- `@results/experiments/report_xnli_sample_300_v2_test__*`

---

## Estado de las posiciones 200-499 del pilot 500

Las 300 instancias restantes del pilot 500 (posiciones 200-499) fueron traducidas en batches experimentales (`xnli_batch_261_320`, `xnli_batch_321_350`, `xnli_batch_350_499`) durante la fase de prueba del pipeline. Esos resultados **no fueron validados** y los archivos fueron eliminados al reorganizar el repo (mayo 2026). El trabajo sobre el full 7500 se retomó con el sample_300 (Fase 10) que usa un muestreo nuevo y sistemático.

---

## Resumen contable (mayo 2026)

| Fuente | Instancias | Método | Estado |
|--------|-----------|--------|--------|
| Combined dev 200 | ~200 | Manual + Opus | Gold — en `data/dev/` |
| Cultural adaptations | ~394 | Opus 4.7 | Consolidado — en `data/dev/` |
| Sample 300 | ~300 | Gemini v2 + Sonnet | En app — en `data/dev/` |
| **Total procesado** | **~894** | | |
| Full 7500 restante | **~6600** | Pendiente | Pipeline Gemini v2 |

> Nota: el usuario estima ~600 instancias procesadas contando dev200 + cultural394. La diferencia con los 894 aquí depende de si el sample300 fue contado. El punto de partida para el siguiente batch es el `processed_idxs.json` (`@data/dev/processed_idxs.json`) que trackea qué índices del full 7500 ya fueron procesados.

---

## Próximo paso

Continuar la traducción del full 7500 en batches de 300 usando `pipeline_traduccion/scripts/translate_xnli_pilot.py`, validando cada batch con Claude Sonnet/Haiku como juez antes de cargar a la app. Instancias problemáticas van a `@pipeline_evaluacion/error_cases/`.
