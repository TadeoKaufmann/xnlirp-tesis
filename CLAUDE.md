# CLAUDE.md

## 1. Descripción del proyecto

Tesis de Maestría sobre benchmarking NLU en español rioplatense (RP) con augmentación guiada por eye-tracking. Componente actual: construir **XNLIrp** adaptando dialectalmente XNLI ES → RP usando Gemini 2.5 Flash como borrador + revisión nativa. Hipótesis: la distancia dialectal entre el corpus ET rioplatense y el benchmark afecta el rendimiento NLU; la augmentación ET ayuda especialmente en low-resource (K=200/500/1000).

## 2. Estructura de carpetas

```
Datasets-Codigo/
├── .env                                   # GOOGLE_API_KEY (Tier 1, billing activo)
├── .venv/                                 # venv local (Windows: .venv\Scripts\activate)
├── PROJECT.md                             # contexto académico, papers clave, hipótesis
├── CLAUDE.md                              # este archivo
├── requirements.txt
├── credentials/                           # service accounts (no tocar)
├── data/
│   ├── raw/xnli/
│   │   └── xnli_pilot_500.jsonl           # 500 instancias estratificadas seed 42 — INMUTABLE
│   └── processed/
│       ├── xnli_pilot_30_annotated.jsonl  # GOLD 30 (few-shots + referencia, leakage conocido)
│       ├── xnli_pilot_30_review.csv       # export para revisión
│       ├── xnli_held_out_70_raw.jsonl     # DEV SET 70 (posiciones 30-99 del 500), anotado por Opus
│       ├── xnli_held_out_70_raw.html      # vista lado a lado
│       ├── xnli_held_out_100_raw.jsonl    # DEV SET 100 (posiciones 100-199 del 500), anotado por Opus
│       ├── xnli_held_out_100_raw.html     # vista lado a lado
│       ├── xnli_combined_dev_200.jsonl    # UNIÓN gold30 + held70 + held100 (200 inst) para run y eval único
│       ├── xnli_error_cases_15.jsonl      # 15 casos problemáticos conocidos (referencia)
│       └── eval_xnli_pilot_30_annotated.md
├── notebooks/                             # exploración manual
├── scripts/
│   ├── check_env.py                       # verifica .env y credenciales
│   ├── translate_xnli_pilot.py            # harness principal: modelo × T × variante prompt
│   ├── evaluate_against_gold.py           # type accuracy + Lev delta vs cualquier gold
│   ├── validate_translations.py           # validador independiente del gold (regex)
│   ├── visualize_comparison.py            # genera HTML lado a lado
│   ├── optimize_prompt_loop.py            # meta-loop automático (no usar en este flujo)
│   ├── _annotate_held_out_70.py           # script que generó el held-out 70
│   ├── _annotate_held_out_100.py          # script que generó el held-out 100
│   └── prompts/
│       ├── prompt_v1_minimal.txt          # variante minimal — la que se está optimizando
│       └── prompt_v2_with_cultural_candidates.txt  # variante con marcaje cultural Fase 1
└── results/
    ├── review_queue.jsonl
    ├── validation_report_xnli_pilot_30_annotated.md
    └── experiments/
        ├── experiments_summary.json
        ├── <config_label>.jsonl           # outputs por config (held70__... o gemini-...)
        ├── failed_<config_label>.jsonl
        ├── report_<config_label>.md       # reporte de tipos+Lev por corrida
        └── eval_<config_label>.md         # evaluación vs gold (type acc + confusion matrix)
```

## 3. Decisiones metodológicas fijas (NO rediscutir)

### 3.1 Tipología A/B/C/D (asignar exactamente UNA letra)

- **A — Sin cambios.** La instancia funciona igual en ES y RP. `changes` debe ser `[]`.
  *Ej:* "Les dije que era de mi hermana" → idéntico en RP.

- **B — Cambios léxicos peninsulares** (incluye PPC → pretérito simple cuando aplica).
  *Ej idx 1638:* "no he hecho nada" → "no hice nada"; "he recibido" → "recibí".
  *Ej idx 1522:* "no tenía un duro" → "no tenía un mango".

- **C — Morfosintaxis rioplatense** (voseo, vosotros/os → ustedes/se, eliminación de pronombres sujeto redundantes).
  *Ej idx 910:* "ha sido un placer hablar contigo" → "fue un placer hablar con vos" (voseo dominante; PPC va como secondary).
  *Ej idx 1534:* "os lo diré" → "se lo diré" (vosotros → ustedes).

- **D — Corrección de errores de traducción** del ES respecto del EN.
  *Ej idx 2821:* "defensores" (de *defendants*) → "demandados".
  *Ej idx 3440:* "guia" → "guía" (typo, tilde faltante).
  *Ej idx 1942:* "Shrewd" sin traducir → "Astuta".

Si una instancia tiene B+C, asignar la letra del cambio dominante (la que domine el conteo de cambios) y registrar el otro en `secondary_features`.

### 3.2 Lista B completa de sustituciones obligatorias

**Léxico:**
- aquí → acá *(obligatorio en TODOS los registros: narrativa, diálogo, descriptivo, turístico, académico, periodístico, formal, coloquial. "Acá" es la forma rioplatense estándar. Conservar mayúscula inicial: "Aquí" → "Acá". Cada ocurrencia se registra como un cambio léxico tipo B.)*
- coche → auto
- autobús → colectivo
- piso (=apartamento) → departamento
- coger → agarrar/tomar
- ordenador → computadora
- móvil → celular
- conducir → manejar
- aparcar → estacionar
- enfadado → enojado
- vestíbulo → hall
- americana (=EEUU) → norteamericana
- coste → costo
- no tenía un duro → no tenía un mango

**Contextuales (no reemplazo mecánico):**
- **oye** → traducción contextual:
  - vocativo: "oye tío" → "che flaco/pibe/amigo"
  - indignación/sorpresa: "pero oye" → "pero che"
  - transición suave: "oye, fueron" → "bueno, fueron"
- **esto...** (muletilla) → "eso..." o "este..."

**PPC → pretérito simple RP** (regla con excepción crítica):
SOLO cambiar cuando se cumplen las **dos** condiciones:
1. Registro coloquial/conversacional, **Y**
2. Acción puntual concluida sin relevancia presente.

Ejemplos que **SÍ** cambian: "he hecho → hice", "ha sido → fue", "hemos añadido → añadimos", "has dicho → dijiste", "has leído → leíste".

**MANTENER el PPC** (no cambiar) cuando:
- Estado resultante vigente o relevancia presente:
  - **"se ha convertido en X"** (estado vigente, sigue siendo X hoy) → **NO cambiar** a "se convirtió".
  - **"no ha tenido en cuenta X"** (crítica académica, sigue sin considerarlo) → **NO cambiar** a "no tuvo en cuenta".
  - **Criterio rector:** si el resultado sigue vigente hoy, mantener PPC. Cambiar el aspecto puede alterar la relación lógica premisa-hipótesis.
- Registro formal, académico o literario.
- Valor experiencial o habitual ("nunca he visto", "siempre he creído").

> **Excepción crítica del PPC (recordar siempre):**
> "se ha convertido" (estado vigente) **NO** cambia.
> "se convirtió" (acción puntual pasada concluida) **SÍ** cambia.
> El criterio es si el resultado sigue vigente hoy.

### 3.3 Principio de cambio mínimo

Solo cambiar lo necesario. Si una oración ya funciona en rioplatense estándar, **no modificarla**. La adaptación es dialectal, no estilística. No reescribir, no mejorar redacción, no buscar consistencia léxica entre prem y hyp (si el ES tiene "flujo" en prem y "crecida" en hyp, ambos quedan tal cual).

### 3.4 Label NLI invariante

La etiqueta `entailment | neutral | contradiction` **nunca puede cambiar**. Si una adaptación posible podría alterar la relación lógica, no se aplica. Esto incluye conservar el aspecto verbal (PPC vs pretérito simple) cuando ese aspecto es lo que sostiene la relación.

### 3.5 Levenshtein siempre por Python, nunca por el modelo

`lev_prem`, `lev_hyp`, `lev_total` se calculan con `python-Levenshtein` en `normalize_response()` de `translate_xnli_pilot.py`. El modelo no estima distancias.

## 4. Estado actual

- **Gold 30** (`xnli_pilot_30_annotated.jsonl`): few-shots + referencia. **Leakage conocido** porque los 3 few-shots del prompt (idx 1638, 910, 2821) están dentro del gold; usar gold solo como sanity check, no como benchmark de generalización. **idx 1522 actualizado** (mayo 2026): se agregó cambio B `así lo creí → así creí` (eliminación de clítico anafórico) en `prem_rp`.
- **Held-out 70** (`xnli_held_out_70_raw.jsonl`): dev set anotado manualmente (Opus 4.7) sobre las posiciones 30-99 del pilot 500. Usar para optimizar el prompt sin contaminación.
- **Held-out 100** (`xnli_held_out_100_raw.jsonl`): dev set adicional anotado manualmente (Opus 4.7) sobre las posiciones 100-199 del pilot 500. Distribución actual: **A 72 / B 6 / C 13 / D 9** (post correcciones de gold idx 22, 1543, 1731, 4490 → A→D).
- **Combined dev 200** (`xnli_combined_dev_200.jsonl`): unión de los tres dev sets en un solo archivo, sin duplicados. Distribución total: **A 140 / B 18 / C 23 / D 19**. Cada fila lleva `source_set` ∈ {`gold30`, `held70`, `held100`}. Pensado para una sola corrida + eval únicos.
- **Test set**: pendiente, anotar al final (posiciones 200+ del pilot 500).
- **Prompt v1** actualizado en mayo 2026 con cuatro cambios:
  1. **D4 con caveat de Restricción 5**: D4 solo aplica cuando una traducción es claramente incorrecta; si ambas son sinónimos válidos, es A. Ejemplo nuevo `médico/doctor`.
  2. **`pues` con mapeo contextual**: 4 contextos (muletilla / causal / consecutivo / cierre) en lugar de reemplazo mecánico.
  3. **Caveat corto de registro arcaico para voseo**: si hay marcas de registro decimonónico/aristocrático (ej. "su señoría"), no aplicar voseo.
  4. **Regla acotada de eliminación de clítico anafórico**: `lo`/`la` se elimina solo cuando es redundante tras adverbio anafórico (`así`, `eso`); ejemplo único `así lo creí → así creí`.
- **Billing Gemini** activo, **Tier 1, 1000 RPM**.
- Eval **pre-cambios de prompt** (stale, hay que re-evaluar):
  - held-out 70 @ Gemini 2.5 Flash T=0.1 v1: type accuracy **94.3%** (A 95.7 / B 83.3 / C 100 / D 87.5).
  - gold 30 @ idem: type accuracy **93.3%** (A 91.3 / B 100 / C 100 / D 100).
  - held-out 100 @ idem (con gold corregido en sesión actual): type accuracy ≈ **95%** (5 errores reales).
- **Validación post-cambios sobre subsets puntuales (8 instancias diversas, mayo 2026)**: 8/8 OK. Confirmó que (a) los 4 fixes del held-out 100 funcionan, (b) el voseo contemporáneo sigue aplicando bien, (c) la regla de clítico no se sobre-aplica en controles relativos/predicativos. Falta correr full sets para confirmar ausencia de regresiones globales.

## 5. Lo que NO debe hacer Claude Code nunca

- **No modificar `data/raw/`** ni los gold anotados (`xnli_pilot_30_annotated.jsonl`, `xnli_held_out_70_raw.jsonl`).
- **No modificar los 3 few-shots del prompt** (idx 1638, 910, 2821).
- **No implementar Fase 2 de adaptación cultural** (los `cultural_candidates` se marcan en Fase 1; la adaptación cultural real es decisión humana posterior).
- **No escalar a 10k** sin validación previa en held-out.
- **No buscar consistencia léxica** entre premisa e hipótesis.
- **No corregir nombres propios** aunque parezcan mal transcritos (ej. "Lecretius" se queda).
- **No traducir directamente del inglés**; el EN es solo referencia para detectar errores tipo D.
- **No alterar `label`/`label_int`** ni la estructura JSON del output.

## 6. Comandos frecuentes

Activar venv: `.venv\Scripts\activate` (Windows). Todos los comandos asumen ejecución desde la raíz del proyecto.

```bash
# Sanity check del entorno
python scripts/check_env.py

# Correr el dev combinado de 200 (gold30 + held70 + held100) con T=0.1 y v1 — RECOMENDADO post-cambios de prompt
python scripts/translate_xnli_pilot.py --input data/processed/xnli_combined_dev_200.jsonl \
    --temperatures 0.1 --prompt-variants v1

# Evaluar contra el dev combinado
python scripts/evaluate_against_gold.py \
    --gold data/processed/xnli_combined_dev_200.jsonl \
    --run results/experiments/xnli_combined_dev_200__gemini-2.5-flash__T0.1__v1.jsonl

# Correr held-out 70 con T=0.1 y v1 (config principal de optimización, dev individual)
python scripts/translate_xnli_pilot.py --held-out --temperatures 0.1 --prompt-variants v1

# Correr held-out 100 con T=0.1 y v1 (segundo dev set, posiciones 100-199)
python scripts/translate_xnli_pilot.py --input data/processed/xnli_held_out_100_raw.jsonl \
    --temperatures 0.1 --prompt-variants v1

# Correr solo las 30 gold
python scripts/translate_xnli_pilot.py --limit-to-gold --temperatures 0.1 --prompt-variants v1

# Correr un input arbitrario (ej. xnli_error_cases_15.jsonl)
python scripts/translate_xnli_pilot.py --input data/processed/xnli_error_cases_15.jsonl \
    --temperatures 0.1 --prompt-variants v1

# Evaluar contra el held-out 70
python scripts/evaluate_against_gold.py \
    --gold data/processed/xnli_held_out_70_raw.jsonl \
    --run results/experiments/held70__gemini-2.5-flash__T0.1__v1.jsonl

# Evaluar contra el held-out 100
python scripts/evaluate_against_gold.py \
    --gold data/processed/xnli_held_out_100_raw.jsonl \
    --run results/experiments/<config_label>.jsonl

# Evaluar contra el gold 30 (default --gold)
python scripts/evaluate_against_gold.py \
    --run results/experiments/gemini-2.5-flash__T0.1__v1.jsonl

# Evaluar TODAS las configs (ranking global)
python scripts/evaluate_against_gold.py --summary results/experiments/experiments_summary.json

# Validador independiente (regex sobre output)
python scripts/validate_translations.py --run results/experiments/<config>.jsonl

# HTML side-by-side para revisión visual
python scripts/visualize_comparison.py --input <jsonl> --output <html>
```

**Args principales de `translate_xnli_pilot.py`:**
- `--models` (default `gemini-2.5-flash`)
- `--temperatures` (default `0.1 0.3 0.5`) — itera por todas las combinaciones
- `--prompt-variants` (default `v1 v2`) — busca `prompts/prompt_<variant>*.txt`
- `--input <path>` | `--held-out` | `--limit-to-gold` | `--skip-gold-idxs` (mutuamente excluyentes en lo aplicable)
- `--limit N` — primeras N del subset
- `--include-english` / `--no-include-english`
- `--batch-size`, `--batch-pause` — control de throughput vs rate limit

**Args de `evaluate_against_gold.py`:**
- `--run <jsonl>` | `--summary <json>`
- `--gold <jsonl>` (default gold 30)
- `--lev-threshold N` (default 10) — tolerancia para auto-aprobación

## 7. Próximos pasos

1. Loop de optimización del prompt v1 contra held-out 70 hasta maximizar type accuracy (sin tocar few-shots).
2. Validar prompt estabilizado contra gold 30 (sanity check, leakage conocido).
3. Anotar manualmente un test set adicional (~100 instancias del pilot 500, posiciones 100+).
4. Lanzar revisión nativa multi-anotador sobre el output de la mejor config.
5. Decidir Fase 2 de adaptación cultural (humano-en-el-loop sobre `cultural_candidates`).
6. Escalar a 10k solo después de pasar (1)-(5).
7. Fine-tuning BETO/XLM-R en las 4 condiciones experimentales (ES→ES, ES→RP, RP→RP, RP→ES).
8. Experimentos ET-augmentado (Deng et al. 2024 + ablación MLM aleatorio).
