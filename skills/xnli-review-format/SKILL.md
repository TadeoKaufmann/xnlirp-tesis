---
name: xnli-review-format
description: Formato consistente para imprimir casos XNLI que necesitan revisión humana (discrepancias gold-vs-modelo, edge cases, propuestas de reglas nuevas, ejemplos para discusión).
---

# XNLI Review Format

## Cuándo usar este skill

Cualquier vez que muestres ejemplos de instancias XNLI al usuario para revisión: discrepancias entre gold y modelo, casos límite, propuestas de reglas nuevas, ejemplos de errores tipo D armonizados, etc.

NO usar para:
- Output programático/eval (reportes JSON, métricas).
- Listados rápidos en línea sin contexto narrativo.

## Organización de archivos

**Un archivo .txt por tarea.** El nombre describe la tarea, no la fecha:

- `scripts/_ejemplos_xnli.txt` → review de instancias culturales en XNLI full 7500.
- `scripts/_review_gold_200.txt` → discrepancias del combined_dev_200 vs runs sucesivos.
- `scripts/_review_<task>.txt` → para tareas nuevas, slug corto y descriptivo.

Dentro de cada archivo: **secciones por fecha**, con separador de líneas bajas:

```
____________________________________________________________________________
2026-05-14 | <descripción corta de qué se está revisando hoy>
____________________________________________________________________________
```

Si la sesión continúa el mismo día y agregás casos nuevos, **NO repetir el header** — agregalos bajo la sección activa.

## Formato de cada caso

Cada instancia va en este bloque:

```
 N. [idx <idx> | <label> | gold=<X> pred=<Y>]
    PREM ES: <texto original ES>
    PREM RP: <texto adaptado RP>  (si difiere; si no, omitir)
    HYP  ES: <texto original ES>
    HYP  RP: <texto adaptado RP>  (si difiere; si no, omitir)

    DIFERENCIAS: <listado breve de spans/palabras que cambiaron, separadas con ";">
    DECISIÓN PROPUESTA: <acción concreta: "cambiar X → Y", "agregar regla B: ...", "mantener A", "actualizar gold a E", etc.>
    CONTEXTO: <una o dos líneas: por qué este caso es interesante, qué regla activa/falta, evidencia>
```

Donde:
- `idx`, `label`, `gold`, `pred` van en la primera línea entre corchetes.
- `prem/hyp RP` se omite si es idéntica a ES (no inflar el archivo).
- `DIFERENCIAS` es una lista corta. Si hay muchas, separar con `;`.
- `DECISIÓN PROPUESTA` es lo más importante: qué se propone hacer con este caso.
- `CONTEXTO` da el "por qué" (regla activa, evidencia de corpus, comparación con otra instancia, etc.).

## Agrupación dentro de una sección

Cuando hay muchos casos en una misma sesión, agrupar por **decisión/categoría** con un sub-header:

```
CATEGORÍA: Errores del gold (modelo correcto, gold desactualizado)
============================================================================

 1. [idx ...] ...
 2. [idx ...] ...

CATEGORÍA: Errores reales del modelo (armonización, reglas inventadas)
============================================================================

 3. [idx ...] ...
```

Numeración corrida dentro de la fecha, atravesando categorías.

## Script auxiliar

`scripts/print_review.py` recibe una lista de casos en JSON y los formatea según este SKILL.md. Útil cuando el conjunto es grande y querés ahorrar tipeo manual.

```bash
python skills/xnli-review-format/scripts/print_review.py \
    --output scripts/_review_gold_200.txt \
    --task "Discrepancias v2 vs gold 200 (post Fase 1d + Bouchard)" \
    --cases cases.json
```

Donde `cases.json` es una lista de objetos con los campos `idx`, `label`, `gold_type`, `pred_type`, `prem_es`, `prem_rp`, `hyp_es`, `hyp_rp`, `diferencias`, `decision`, `contexto`, `categoria` (opcional).

Si `--output` ya existe y la fecha de hoy ya tiene su header, los casos se agregan a la sección activa. Si la fecha cambió o el archivo es nuevo, se crea un header nuevo.
