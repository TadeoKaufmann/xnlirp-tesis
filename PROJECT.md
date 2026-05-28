# Tesis de Grado — Benchmarking NLU en Español Rioplatense con Eye-Tracking

## Hipótesis central

La distancia dialectal entre el corpus de eye-tracking rioplatense y el benchmark de evaluación **afecta** el rendimiento de los modelos NLU; y la augmentación con eye-tracking (ET) **mejora** especialmente en escenarios low-resource (K=200/500/1000).

## Componentes

- **Corpus ET:** Cuentos (Travi et al. 2026, Scientific Data) — 30 cuentos, narrativa en español, lectura con eye-tracking. Ver `Referencias/texts/`
- **Método:** augmentación MLM guiada por fixation duration. Ablación con MLM aleatorio. Base: Deng et al. 2024 (ACL).
- **Tres tareas:**
  1. **XNLIrp** — adaptación dialectal ES→RP de XNLI. Pipeline: Gemini 2.5 Flash como traductor automático + revisión nativa multi-anotador.
  2. **Hate speech RP** — Pérez et al. 2025 (NAACL). Baseline BETO F1=63.5.
  3. **QA Cuentos** — NLI binario sobre los cuentos del corpus ET.

## Decisiones metodológicas

- Ruta de traducción: ES estándar → RP (no EN → RP), justificado por Artetxe et al. 2020 y Ebing & Glavaš 2024
- Pipeline: Gemini 2.5 Flash como traductor automático + revisión nativa multi-anotador
- Tipología: A (sin cambio), B (léxico), C (morfosintaxis/voseo), D (error de traducción), E (cultural)
- Levenshtein normalizado ES↔RP como control de calidad y variable de análisis
- 4 condiciones experimentales: ES→ES, ES→RP, RP→RP, RP→ES
- Modelos a evaluar: BETO, XLM-RoBERTa

## Stack técnico

- Python local Windows
- Gemini 2.5 Flash (Google AI Studio, Tier 1, billing activo)
- JSONL como formato principal
- Supabase + Vercel para validation app
- API key en .env

## Estructura de archivos

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
│   │   ├── xnli_sample_300_v2_test.jsonl       # muestra 300 (Gemini v2 + validación Sonnet) — actualmente en la app
│   │   ├── cultural_adaptations.jsonl          # ~394 instancias culturalmente complejas (Opus)
│   │   └── processed_idxs.json                 # tracker de índices ya procesados del full 7500
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
│   │       ├── prompt_v1_minimal.txt
│   │       ├── prompt_opus_cultural.txt
│   │       └── pre_prompt_v2_cultural_candidates_marker_only.txt
│   └── referencias/
│       ├── historial_prompts.md               # evolución cronológica del prompt
│       ├── cronologia_datos.md                # historial de fases de construcción del dataset
│       └── _pendientes.md                     # vocabulario XNLI + decisiones pendientes
│
├── pipeline_evaluacion/
│   ├── scripts/
│   │   └── evaluate_against_gold.py
│   ├── error_cases/
│   │   └── xnli_error_cases_15.jsonl
│   ├── respuestas_anotadores/
│   │   ├── Anotadores_prompt_viejo.csv
│   │   └── Respuestas_6_batch_test.csv
│   └── referencias/
│       ├── _review_gemini.txt
│       ├── _review_gold_200.txt
│       └── _review_opus_anglos.txt
│
├── results/
│   ├── experiments/                           # outputs JSONL + report_*.md + eval_*.md por config
│   ├── analisis_v1_vs_v2.ipynb
│   ├── ranking_vocab_xnli.tsv
│   └── review_queue.jsonl
│
├── validation_app/                            # encuesta web (Supabase + vanilla JS — deploy Vercel)
├── Referencias/
│   ├── Papers/
│   │   ├── Datasets/                          # XNLI, GLUE, XTREME, Cuentos, hate speech
│   │   ├── Modelo/                            # Deng, Travi, Zhang&Hollenstein, Yang&Hollenstein
│   │   └── Justificaciones/                   # Bengoetxea, Lopetegui, Hershcovich, Baldissin, etc.
│   ├── Tesis_compañeros/                      # Schmidt, Bolaños, GutterTeo, LouysSanso, Cantini
│   └── texts/                                 # corpus Cuentos ET (30 cuentos RP)
└── .claude/
    └── skills/
```

## Papers clave

### Corpus ET y método de augmentación

| Paper | Venue | Rol en la tesis |
|-------|-------|----------------|
| Travi et al. 2026 | Scientific Data | **Corpus Cuentos ET** — 30 cuentos narrativos en español, lectura con ET. Base directa de la tesis. `Referencias/Papers/Datasets/Cuentos - Travi_2026_ScientificData.pdf` |
| Travi et al. 2025 | CMCL | **Integración ET en word embeddings** — mismo grupo (UBA/Kamienkowski). Antecedente metodológico directo. `Referencias/Papers/Modelo/Fermin - modelo.pdf` |
| Deng et al. 2024 | ACL | **Fine-Tuning Pre-Trained LMs with Gaze Supervision** — método principal de ET-augmentado que implementamos. Los compañeros de maestría también lo usan → comparación directa. `Referencias/Papers/Modelo/Deng_2024_ACL_GazeSupervision.pdf` |
| Zhang & Hollenstein 2024 | LREC-COLING | ET features masking transformer attention en QA — trabajo relacionado, no central a la tesis. `Referencias/Papers/Modelo/Zhang_2024_LREC_ETMaskingTransformers.pdf` |
| Yang & Hollenstein | — | PLM-AS: Pre-trained LMs augmented with scanpaths (sentiment) — trabajo relacionado, no central a la tesis. `Referencias/Papers/Modelo/Yang_PLMAS_ScanpathsLMs.pdf` |

### Benchmarks y datasets

| Paper | Venue | Rol en la tesis |
|-------|-------|----------------|
| Conneau et al. 2018 | EMNLP | **XNLI original** — fuente del dataset que adaptamos. `Referencias/Papers/Datasets/XNLI - Conneau_2018_EMNLP.pdf` |
| Wang et al. 2019 | ICLR | **GLUE** — benchmark multi-tarea NLU, contexto general. `Referencias/Papers/Datasets/GLUE - Wang_2019_ICLR.pdf` |
| Hu et al. 2020 | ICML | **XTREME** — benchmark multilingüe masivo, antecedente. `Referencias/Papers/Datasets/XTREME - Hu_2020_ICML.pdf` |
| Pérez et al. 2025 | NAACL | **Hate speech RP** — tarea 2, baseline BETO F1=63.5. `Referencias/Papers/Datasets/HateSpeech_modelo - Perez_2025_NAACL.pdf` |
| Pérez et al. 2023 | IEEE Access | Assessing contextual info en hate speech — contexto de la tarea 2. `Referencias/Papers/Datasets/HateSpeech_dataset - Perez_2023_IEEEAccess.pdf` |

### Variación dialectal / adaptación XNLI

| Paper | Venue | Rol en la tesis |
|-------|-------|----------------|
| Artetxe et al. 2020 | ACL | Translation artifacts y translationese — **justifica ES→RP** sobre EN→RP |
| Ebrahimi et al. 2022 | ACL | **AmericasNLI** — precedente de XNLI para lenguas de baja frecuencia (ES→lengua objetivo) |
| Heredia et al. 2024 | NAACL | **XNLIeu** — arquitectura traducción + revisión nativa, modelo de pipeline más cercano al nuestro |
| Bengoetxea et al. 2025 | CoNLL | **XNLIvar / Lost in Variation** — gap rioplatense explícito en variedades del español y euskera. `Referencias/Papers/Justificaciones/Lost in variation - XNLIvar.pdf` |
| Lopetegui et al. 2025 | VarDial | **DSL-TL / Common Ground, Diverse Roots** — 38% ejemplos comunes ES ibérico vs RP, cuantifica distancia dialectal. `Referencias/Papers/Justificaciones/VarDial - Lopetegui_2025.pdf` |
| Ebing & Glavaš 2024 | ACL | Translationese mínimo para variedades del mismo idioma — refuerza elección ES→RP |
| Faisal et al. 2024 | ACL | DialectBench — rioplatense ausente de benchmarks dialectales, motiva el trabajo |

### Marco teórico y justificaciones

| Paper | Venue | Rol en la tesis |
|-------|-------|----------------|
| Hershcovich et al. 2022 | ACL | Challenges and Strategies in Cross-Cultural NLP — marco teórico. `Referencias/Papers/Justificaciones/Cross-Cultural NLP, marco teorico.pdf` |
| Baldissin et al. 2022 | LREC | **DiaWUG** — dataset de variación léxica diatópica en español (antecedente de recursos dialectales). `Referencias/Papers/Justificaciones/A Dataset for Diatopic Lexical Semantic Variation in Spanish.pdf` |
| Srirag et al. 2025 | ACL | BESSTIE — benchmark sentimiento/sarcasmo en variedades del inglés (trabajo análogo en EN). `Referencias/Papers/Justificaciones/A Benchmark for Sentiment and Sarcasm Classification for.pdf` |
| Goldfarb-Tarrant et al. 2023 | EMNLP | Cross-lingual transfer puede empeorar sesgo en sentiment — contextualiza riesgos de transfer. `Referencias/Papers/Justificaciones/Cross-lingual Transfer Can Worsen Bias in Sentiment Analysis.pdf` |
| Cahyawijaya et al. 2025 | NAACL | Multilingual LLMs no pueden (aún) disambiguar word senses cross-linguals — límites actuales de LLMs multilingües. `Referencias/Papers/Justificaciones/Multilingual Large Language Models Can Not (Yet)...pdf` |

## Tesis de referencia

Ubicadas en `Referencias/Tesis_compañeros/`:

| Tesis | Archivo | Por qué es relevante |
|-------|---------|---------------------|
| Schmidt, Tomás | `Indice_Comentado_TomásSchdmidt.pdf` | Índice comentado de referencia — formato y estructura |
| Bolaños, Cecilia | `Tesis-final-Cecilia-Bolannos.pdf` | Tesis completa del programa — metodología comparable |
| GutterTeo | `GutterTeoTesis.pdf` | Tesis completa del programa |
| LouysSanso, Catherine Sophie | `LouysSansoCatherineSophie-Tesis_compressed.pdf` | Tesis completa del programa |
| Cantini, Sebastián | `Tesis_Sebas_Cantini_eye_tracking.pdf` | **Tesis con eye-tracking ya completa** — referencia directa para estructura y metodología ET |

## Estado actual (mayo 2026)

### Completado ✅
- Decisión ES→RP fundamentada en literatura
- Tipología A/B/C/D/E definida y estabilizada
- Pipeline de traducción: Gemini 2.5 Flash + prompt v2_cultural_inline
- **Dev canónico 200** (`data/dev/xnli_combined_dev_200.jsonl`): gold anotado manualmente. Distribución: A 139 / B 19 / C 23 / D 19
- **Cultural adaptations** (`data/dev/cultural_adaptations.jsonl`): ~394 instancias del full 7500 con adaptaciones culturales tipo E, procesadas por Opus
- **Sample 300** (`data/dev/xnli_sample_300_v2_test.jsonl`): 300 instancias del full 7500, Gemini v2 + validación Sonnet (89.4% aprobadas)
- Validation app deployada en Vercel (Supabase backend); sample 300 cargado
- Repo reorganizado: `pipeline_traduccion/` + `pipeline_evaluacion/` + `data/dev/`
- Cronología de datos documentada en `pipeline_traduccion/referencias/cronologia_datos.md`
- **Primera ronda de anotación completada y limpiada**: 62 respuestas válidas de 7 anotadores reales (Andrea 19, Pedro 13, Ulises 15, Manu 10, Cristian 2, Jorge 2, Nancy 1) guardadas en `pipeline_evaluacion/respuestas_anotadores/respuestas_validadas.csv`. Respuestas contaminadas (tests de UI + tutor) descartadas. 27 instancias con problemas documentados en `pipeline_evaluacion/error_cases/to_fix_error_cases.jsonl`.

### En progreso 🔄
- Prompt v2 con reglas candidatas de sesiones de revisión pendientes de incorporar (ver `pipeline_evaluacion/referencias/_review_gemini.txt`, `_review_gold_200.txt`, `_review_opus_anglos.txt`)
- Revisión nativa multi-anotador: primera ronda terminada (62 resp. válidas); instancias libres disponibles en la app para segunda ronda
- 27 instancias marcadas como `[TO FIX]` en `to_fix_error_cases.jsonl` pendientes de corrección en el dataset

### Pendiente ⏳
- Continuar traducción del full 7500 en batches + revisión nativa multi-anotador
- Traducción del train set ~392k ES→RP con Gemini Batch + validación Haiku (pendiente decisión con tutor — ver `pipeline_traduccion/referencias/_pendientes.md` §9)
- Pipeline de evaluación automática (Sonnet/Haiku como jueces sobre output Gemini)
- Fine-tuning BETO/XLM-R en las 4 condiciones (ES→ES, ES→RP, RP→RP, RP→ES)
- Experimentos ET-augmentado (Deng et al. 2024): MLM continuo sobre corpus Cuentos → fine-tune sobre XNLIrp
- Comparación con compañeros que usan Deng et al. 2024 como base

### Experimentos BETO planeados (mayo 2026) 🧪

Dataset en `C:/Users/tadeo/Desktop/Tesis/datasets-codigo-data/` (1256 train / 1257 test, ~256 instancias culturales por split, flag `is_cultural`).
Modelo: `dccuchile/bert-base-spanish-wwm-cased` (BETO). K={200, 500, 1000}, 3 seeds, accuracy ± std.

| exp | train | test | objetivo |
|---|---|---|---|
| RP→RP | `rp_train` (cols RP) | `rp_test` (cols RP) | upper bound |
| ES→RP | `paired_train` (cols ES) | `paired_test` (cols RP) | **gap dialectal** |
| ES→ES | `paired_train` (cols ES) | `paired_test` (cols ES) | baseline limpio |

Análisis adicional: accuracy `is_cultural=True` vs `is_cultural=False` en test.
Siguiente fase: augmentación ET via MLM continuo sobre Cuentos RP → fine-tune sobre XNLIrp (análogo a Deng et al. 2024 pero con scanpaths reales de lectores RP).
