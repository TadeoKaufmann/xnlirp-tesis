# CLAUDE.md

## 1. Descripción del proyecto

Tesis de Grado (carrera de 5 años y medio, equivalente internacional a maestría) sobre benchmarking NLU en español rioplatense (RP) con augmentación guiada por eye-tracking. Tres tareas: (1) **XNLIrp** — adaptación dialectal XNLI ES→RP; (2) **Hate speech RP** — Pérez et al. NAACL 2025, baseline BETO F1=63.5; (3) **QA Cuentos** — NLI binario sobre los cuentos del corpus ET. Pipeline XNLIrp: Gemini 2.5 Flash como traductor automático + revisión nativa. Hipótesis: la distancia dialectal entre el corpus ET rioplatense y el benchmark afecta el rendimiento NLU; la augmentación ET ayuda especialmente en low-resource (K=200/500/1000).

## 2. Estructura de carpetas

```
Datasets-Codigo/
├── .env                                        # GOOGLE_API_KEY (Tier 1, billing activo)
├── .venv/                                      # venv local (Windows: .venv\Scripts\activate)
├── PROJECT.md                                  # contexto académico, papers clave, hipótesis
│
├── data/
│   ├── raw/xnli/
│   │   └── xnli_full_7500.jsonl               # 7500 inst (5010 test + 2490 val/dev de XNLI — no hay train ES) — INMUTABLE
│   ├── dev/                                    # datasets activos del proyecto
│   │   ├── xnli_combined_dev_200.jsonl         # DEV CANÓNICO: gold30+held70+held100, revisado manualmente
│   │   ├── xnli_sample_300_v2_test.jsonl       # nueva muestra 300 (Gemini v2 + validación Sonnet)
│   │   ├── cultural_adaptations.jsonl          # ~394 instancias culturalmente complejas (Opus)
│   │   ├── processed_idxs.json                 # tracker de índices ya procesados del full 7500 (por output file)
│   │   └── processed_idx_set.json              # set GLOBAL de idx procesados (to_upload + to_fix de todos los batches)
│   └── qa/                                     # QA dataset (tarea 3 de la tesis)
│       ├── scripts/
│       │   ├── generate_qa_dataset.py
│       │   └── validate_qa_dataset.py
│       ├── qa_stories_dataset.jsonl
│       ├── qa_stories_{dev,train,test}.jsonl
│       ├── qa_validation_results.jsonl
│       └── qa_validation_report.md
│
├── pipeline_traduccion/
│   ├── scripts/
│   │   ├── translate_xnli.py                   # harness principal: modelo × T × variante prompt
│   │   ├── validate_translations.py            # validador regex independiente
│   │   ├── visualize_comparison.py             # genera HTML lado a lado
│   │   └── optimize_prompt_loop.py             # loop de optimización de prompt
│   ├── prompts/
│   │   ├── prompt_v2_cultural_inline.txt       # PROMPT ACTIVO: A/B/C/D + E cultural inline
│   │   └── _archive/
│   │       ├── prompt_v1_minimal.txt           # dialectal puro A/B/C/D (base histórica)
│   │       ├── prompt_opus_cultural.txt        # variante Opus (ya cumplió su función)
│   │       └── pre_prompt_v2_cultural_candidates_marker_only.txt  # pre-v2: solo marcaba, no aplicaba
│   └── referencias/
│       ├── historial_prompts.md               # evolución cronológica del prompt
│       ├── cronologia_datos.md                # historial de fases de construcción del dataset
│       └── _pendientes.md                     # vocabulario XNLI pendiente de resolver
│
├── pipeline_evaluacion/
│   ├── scripts/
│   │   └── evaluate_against_gold.py           # type accuracy + Lev delta vs cualquier gold
│   ├── error_cases/
│   │   └── xnli_error_cases_15.jsonl          # casos problemáticos conocidos (crece con el tiempo)
│   ├── respuestas_anotadores/                 # respuestas CSV de validación nativa
│   │   ├── Anotadores_prompt_viejo.csv
│   │   └── Respuestas_6_batch_test.csv
│   └── referencias/
│       ├── _review_gemini.txt                 # revisión 15 casos sample_300 (reglas candidatas)
│       ├── _review_gold_200.txt               # discrepancias v2 vs gold 200 (correcciones al gold)
│       └── _review_opus_anglos.txt            # 58 instancias anglos — decisión: mantener figuras públicas
│
├── results/
│   ├── experiments/                           # outputs JSONL + report_*.md + eval_*.md por config
│   ├── analisis_v1_vs_v2.ipynb
│   ├── {acc,confusion,delta_errores}_v1_vs_v2.png
│   ├── ranking_vocab_xnli.tsv
│   └── review_queue.jsonl
│
├── validation_app/                            # encuesta web (Supabase + vanilla JS)
│   └── index.html                             # deploy a Vercel — push a main = redeploy automático
├── Referencias/                               # todos los documentos de referencia
│   ├── Papers/                                # papers académicos organizados por tema
│   ├── Tesis_compañeros/                      # tesis de referencia (Schmidt, Bolaños, etc.)
│   └── texts/                                 # corpus Cuentos ET (30 cuentos RP)
└── .claude/
    └── skills/                                # skills de Claude Code (supabase-upload, review-format, etc.)
```

## 3. Decisiones metodológicas fijas (NO rediscutir)

### 3.0 APIs y costos — decisión fija

- **Traducción:** Gemini 2.5 Flash via Gemini Batch API (async, billing activo en `.env` como `GOOGLE_API_KEY`)
- **Grading/evaluación:** OpenAI gpt-4o-mini via **OpenAI Batch API** (async, 50% descuento, `OPENAI_API_KEY` en `.env`)
- **NUNCA usar llamadas sincrónicas** para tareas de traducción o evaluación en lote — nada de lo que hacemos requiere respuesta inmediata. Siempre Batch API.
- El Batch API de OpenAI acepta hasta 50K requests por batch, archivo hasta 200MB, y completa en ≤24h (generalmente mucho menos).
- `grade_translations.py` implementa el flujo Batch API: upload → create batch → poll → download → parse.

**Flujo de processed_idx_set.json:**
Después de cada batch: las instancias ok van a `validation_app/to_upload/`, las no-ok a `pipeline_evaluacion/error_cases/to_fix_*.jsonl`. Inmediatamente después del split, correr:
```
python pipeline_traduccion/scripts/mark_processed.py <to_upload.jsonl> <to_fix.jsonl>
```
Esto registra todos los idx procesados en `data/dev/processed_idx_set.json`. Las futuras corridas de `translate_xnli.py` leen ese set y saltean esas instancias automáticamente, independientemente del archivo de salida usado.


### 3.1 Tipología A/B/C/D/E

- **A** — Sin cambios. La instancia funciona igual en ES y RP.
- **B** — Cambios léxicos peninsulares (incluye PPC → pretérito simple cuando aplica).
- **C** — Morfosintaxis rioplatense (voseo, vosotros/os → ustedes/se).
- **D** — Corrección de errores de traducción del ES respecto del EN.
- **E** — Adaptación cultural rioplatense pura (sin cambios B/C/D adicionales). Solo v2.

Si una instancia tiene múltiples tipos, la letra es la del cambio dominante (mayor conteo); el resto va en `secondary_features`.

### 3.2 Principios fijos

- **Cambio mínimo:** solo cambiar lo necesario. La adaptación es dialectal, no estilística.
- **Label NLI invariante:** la etiqueta `entailment | neutral | contradiction` nunca puede cambiar. Si una adaptación posible podría alterar la relación lógica, no se aplica.
- **Levenshtein siempre por Python:** `lev_prem`, `lev_hyp`, `lev_total` se calculan con `python-Levenshtein` en `normalize_response()` de `pipeline_traduccion/scripts/translate_xnli.py`. El modelo no estima distancias.

### 3.3 Archivos de referencia

- **Prompt activo:** `pipeline_traduccion/prompts/prompt_v2_cultural_inline.txt`
- **Historial de prompts:** `pipeline_traduccion/referencias/historial_prompts.md`
- **Cronología de datos:** `pipeline_traduccion/referencias/cronologia_datos.md`
- **Vocabulario pendiente:** `pipeline_traduccion/referencias/_pendientes.md`
- **Casos problemáticos:** `pipeline_evaluacion/error_cases/xnli_error_cases_15.jsonl`
- **Reviews de sesión:** `pipeline_evaluacion/referencias/`

## 4. Pipeline de construcción del dataset XNLIrp

```
Gemini traduce
    └─► Grader Sonnet/Haiku (xnli-grader skill)
           ├─ OK ──────────────────────────────► App (validación nativa, escala 1-5)
           │                                          ├─ score 3-5 + sin palabra marcada ──► DATASET
           │                                          └─ score 1-2 o con palabra marcada ──► to_fix
           │                                                  └─► arreglar manualmente
           │                                                          └─► Sonnet simula score 1-5
           │                                                                  └─ 3-5 sin palabra ──► DATASET
           └─ No OK ──────────────────────────► to_fix
                                                       └─► arreglar manualmente
                                                               └─► Sonnet simula score 1-5
                                                                       └─ 3-5 sin palabra ──► DATASET
```

**Archivos del pipeline de evaluación:**
- `pipeline_evaluacion/error_cases/to_fix_error_cases.jsonl` — casos a corregir (fuentes: grader + app score 1-2 + palabra marcada)
- `pipeline_evaluacion/error_cases/xnli_error_cases_15.jsonl` — casos problemáticos históricos de referencia
- `pipeline_evaluacion/respuestas_anotadores/respuestas_validadas.csv` — respuestas nativas validadas (app + útiles de sesiones contaminadas)
- `pipeline_evaluacion/scripts/grade_translations.py` — wrapper Python para batches grandes via API (ANTHROPIC_API_KEY)
- Skill `/xnli-grader` — grader interactivo en chat (quota diaria de Claude, sin costo extra)

**Escala de rating (app y Sonnet-juez):** 1-2 = problemático → to_fix; 3-5 sin marca = dataset; 1-2 o con palabra marcada = to_fix.

## 5. Estado actual

- **Dev canónico** (`data/dev/xnli_combined_dev_200.jsonl`): 200 inst, revisadas manualmente. Distribución: **A 139 / B 19 / C 23 / D 19**. Los few-shots idx 1638, 910, 2821 tienen leakage conocido — usar solo como sanity check para esas instancias. Grader accuracy: **94.0%** (188/200) con prompt v2 expandido (mayo 2026).
- **Sample 300** (`data/dev/xnli_sample_300_v2_test.jsonl`): 300 inst del full 7500, Gemini v2 + validación Sonnet. **Son las que están actualmente en la validation app (Vercel).** Respuestas nativas consolidadas en `respuestas_validadas.csv` (contaminados útiles ya mergeados).
- **Cultural adaptations** (`data/dev/cultural_adaptations.jsonl`): ~394 inst del full 7500 con adaptaciones culturales tipo E, procesadas por Opus.
- **Total procesado:** ~600-900 instancias del full 7500 (ver `pipeline_traduccion/referencias/cronologia_datos.md`).
- **Billing Gemini**: activo, Tier 1, 1000 RPM.
- **Eval (stale — re-evaluar con prompt actualizado):**
  - held-out 70 @ Gemini 2.5 Flash T=0.1 v1: type accuracy **94.3%** (A 95.7 / B 83.3 / C 100 / D 87.5)
  - gold 30 @ idem: **93.3%**
  - held-out 100 @ idem: **≈95%**
- **validation_app**: deploy en Vercel (https://tadeo-tesis.vercel.app/), vinculado al repo GitHub. Push a `main` → redeploy automático. Raíz de publicación: `validation_app/`. Features implementadas (mayo 2026): batch siempre 20 (Fisher-Yates), catch trial idx 9999 (texto peninsular + hipótesis con nombres anglos inventados, hardcoded fuera del sistema de reservas), animación cursor 👆 sobre "chaval" al entrar, ranking top 10, validador de nombre duplicado, barra de progreso meta 5000 en screen-thanks, ranking_cap en tabla anotadores (Pablete cap=26). Ver `validation_app/_pendientes.md` para schema Supabase completo.
- **datasets-codigo-data/** (`C:/Users/tadeo/Desktop/Tesis/datasets-codigo-data/`): 4 JSONL para experimentos BETO: `rp_train.jsonl` (1256), `rp_test.jsonl` (1257), `paired_train.jsonl` (1256), `paired_test.jsonl` (1257). Incluye flag `is_cultural`. Ver `README.md` en esa carpeta para instrucciones de fine-tuning.

## 6. Lo que NO debe hacer Claude Code nunca

- **No modificar `data/raw/`** ni el dev canónico sin justificación explícita.
- **No modificar los 3 few-shots del prompt** (idx 1638, 910, 2821).
- **No escalar a todo el full 7500** sin validación previa en dev + test set.
- **No buscar consistencia léxica** entre premisa e hipótesis (excepción única v2: referente cultural adaptado E.1/E.2).
- **No corregir nombres propios** aunque parezcan mal transcritos (excepción controlada v2: nombres anglo no-célebres según E.1 del prompt).
- **No adaptar figuras públicas reales** (McKim, Gehry, Pickard, Ashcroft, Pynchon, Skeat, Boswell, Lewinsky, etc.) — decisión documentada en `pipeline_evaluacion/referencias/_review_opus_anglos.txt`.
- **No traducir directamente del inglés**; el EN es solo referencia para detectar errores tipo D.
- **No alterar `label`/`label_int`** ni la estructura JSON del output.

## 7. Comandos frecuentes

Activar venv: `.venv\Scripts\activate` (Windows). Todos los comandos asumen ejecución desde la raíz del proyecto.

```bash
# Correr el dev_200 con T=0.1 y v2 (prompt activo)
python pipeline_traduccion/scripts/translate_xnli.py --dev_200

# Evaluar contra el dev combinado
python pipeline_evaluacion/scripts/evaluate_against_gold.py \
    --gold data/dev/xnli_combined_dev_200.jsonl \
    --run results/experiments/xnli_combined_dev_200__gemini-2.5-flash__T0.1__v2.jsonl

# Traducir nuevo batch del full 7500 (usa processed_idxs.json para evitar repetir)
python pipeline_traduccion/scripts/translate_xnli.py \
    --input data/raw/xnli/xnli_full_7500.jsonl \
    --temperatures 0.1 --prompt-variants v2

# Evaluar TODAS las configs (ranking global)
python pipeline_evaluacion/scripts/evaluate_against_gold.py \
    --summary results/experiments/experiments_summary.json

# HTML side-by-side para revisión visual
python pipeline_traduccion/scripts/visualize_comparison.py --input <jsonl> --output <html>
```

**Args principales de `translate_xnli.py`:**
- `--dev_200` — shortcut para correr contra el dev canónico 200
- `--input <path>` — JSONL de entrada arbitrario (ej. full 7500)
- `--models` (default `gemini-2.5-flash`)
- `--temperatures` (default `0.1` — siempre 0.1; 0.3 solo para ablaciones puntuales)
- `--prompt-variants` (default `v2`)
- `--offset N`, `--limit N` — para batches parciales
- `--batch-size`, `--batch-pause` — control de throughput vs rate limit

**Args de `evaluate_against_gold.py`:**
- `--run <jsonl>` | `--summary <json>`
- `--gold <jsonl>` (default: `data/dev/xnli_combined_dev_200.jsonl` — el dev_200)
- `--lev-threshold N` (default 10)

## 8. Próximos pasos

1. **Pipeline de evaluación automática**: implementado — xnli-grader skill (Sonnet/Haiku) + grade_translations.py (API). Accuracy dev_200: 94.0%.
2. Re-evaluar con prompt v2 actualizado contra dev_200 (stale — ver sección 4).
3. Validar con cuentos: que el pipeline no traduzca los textos del corpus ET.
4. Continuar traducción del full 7500 en batches + revisión nativa multi-anotador (ver `pipeline_traduccion/referencias/cronologia_datos.md`).
5. Traducción del train set ~392k ES→RP con Gemini Batch + validación Haiku (pendiente decisión con tutor — ver `pipeline_traduccion/referencias/_pendientes.md` §9).
6. Fine-tuning BETO/XLM-R en las 4 condiciones (ES→ES, ES→RP, RP→RP, RP→ES).
7. Experimentos ET-augmentado (Deng et al. 2024 + ablación MLM aleatorio).
