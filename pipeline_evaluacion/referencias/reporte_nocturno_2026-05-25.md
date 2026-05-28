# Reporte nocturno — 2026-05-25

## Resumen ejecutivo

- **Traducción:** 1960 instancias nuevas procesadas esta noche (de 836 → 2360 en el JSONL)
- **Grading:** 1832 evaluadas por GPT-4o-mini, **89.8% accuracy**
- **Split:** 1646 ok → `validation_app/to_upload/batch_1960_ok.jsonl` | 186 to_fix → `pipeline_evaluacion/error_cases/to_fix_batch_1960.jsonl`
- **processed_idx_set.json:** 2331 idx totales registrados

---

## Estado del full 7500

| Estado | Instancias |
|--------|-----------|
| JSONL de resultados | 2360 |
| processed_idx_set.json | 2331 |
| **Total único procesado (unión)** | **~2696** |
| Pendientes de traducir | **~4804** |

La quota de Gemini Batch API (~19 batches exitosos por ventana) cortó el loop dos veces esta noche. El segundo loop de 50 batches sigue corriendo pero también está en 429. **Necesita otro loop mañana.**

---

## Resultados del grader (1832 instancias)

| Veredicto | N | % |
|-----------|---|---|
| ok | 1646 | 89.8% |
| missing_change | 84 | 4.6% |
| wrong_type | 56 | 3.1% |
| nli_broken | 21 | 1.1% |
| other/multiple | 6 | 0.3% |
| bad_rp | 0 | 0.0% |
| Sin veredicto (128) | — | — |

**Consistency con batch anterior:** 89.4% (500 inst) → 89.8% (1832 inst). Estable.

---

## Issues nuevos detectados — REVISAR

### 1. "Levántala" → "Parala" en contexto náutico (6 ocurrencias)
El grader flagea que `heave her to` se traduce como "Levántala" en vez de "Parala" (detener el barco, virar en redondo). Si el contexto es Captain Blood / E.3, puede ser un error sistemático en instancias náuticas. **Verificar si aplica E.3 o es una regla B faltante.**

### 2. "esto..." → "este..." como muletilla de hesitación (3 ocurrencias)
El grader dice que en RP la muletilla oral de hesitación es "este..." (no "esto..."). No está en el prompt actual. **Posible regla B a agregar si confirmás que es sistemática.**

### 3. Error de agrupación de festividades (3 ocurrencias)
El grader detecta que Gemini agrupa distintas festividades bajo un solo nombre. Relacionado con E.2. **Revisar si el prompt E.2 es ambiguo.**

### 4. wrong_type D→A / D→B (7 ocurrencias combinadas)
Gemini asigna tipo D cuando en realidad es A (sin cambios) o B (cambio léxico legítimo, no error). El grader detecta esto para "eh eh" y otros casos. El issue 4x "tipo D pero debería ser A" es el más claro — Gemini marca correcciones que no hizo.

---

## Divergencias vs gold (591 instancias con gold disponible)

- matches: 515 (87.1%)
- model_wrong: 76 (12.9%)
- gold_outdated: 0
- ambiguous: 0

76 casos donde el grader confirma que el modelo está mal (no es gold desactualizado). Estos están en to_fix_batch_1960.

---

## Acciones para mañana

1. **Traducción:** Correr otro loop de 70 batches × 98 para avanzar en las ~4804 pendientes. Recomendado a la mañana cuando la quota esté limpia.

2. **Revisar issues nuevos** (secciones 1-4 arriba) y decidir si agregar reglas al prompt. Son potencialmente sistemáticos.

3. **to_fix_batch_1960.jsonl** (186 inst): revisar muestra de ~20 para calibrar si el grader está siendo muy estricto o los errores son reales. Prioridad: los 21 nli_broken.

4. **batch_1960_ok.jsonl** (1646 inst): subir a Supabase para validación nativa cuando estés listo.

5. **Sin veredicto (128 inst):** El grader procesó 1960 pero parseó 1832 veredictos — 128 instancias no tienen veredicto. Están en el JSONL de resultados pero no en ninguno de los dos archivos de split. Correr el grader nuevamente sobre esas instancias o revisar manualmente.

---

## Patrón de quota Gemini Batch

Ventana observada: ~19 batches exitosos de 98 inst antes del bloqueo. Luego ~15 iteraciones fallidas rápidas y se desbloquea solo. Ciclo estimado: ~45 min de trabajo + ~20 min de espera. Para traducir las ~4804 restantes necesitamos ~50 batches = ~3 ciclos = ~3-4 horas de runtime mañana.

**Fix pendiente en translate_xnli.py:** agregar retry con backoff en batch creation para manejar 429 automáticamente en vez de fallar hard.
