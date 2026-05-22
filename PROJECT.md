# Tesis de Maestría — Benchmarking NLU en Español Rioplatense con Eye-Tracking

## Hipótesis central
La distancia dialectal entre el corpus de eye-tracking rioplatense y el benchmark de evaluación afecta el rendimiento de los modelos NLU, y el augmentado con eye-tracking (ET) ayuda especialmente en low-resource (K=200/500/1000).

## Componentes
- Corpus ET: Cuentos (Lopetegui et al. 2025/2026) — 30 cuentos, 113 participantes nativos. Ver `Referencias/texts/`
- Método: augmentación MLM guiada por fixation duration. Ablación con MLM aleatorio. Base: Deng et al. ACL 2024.
- Benchmark 3 tareas: (1) Hate speech RP — Pérez et al. NAACL 2025, BETO F1=63.5. (2) XNLIrp — en construcción. (3) QA Cuentos — NLI binario sobre los cuentos del corpus ET.

## Decisiones metodológicas
- Ruta de traducción: ES estándar → RP (no EN → RP)
- Pipeline: Gemini 2.5 Flash como borrador + revisión nativa multi-anotador
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
├── data/
│   ├── raw/xnli/xnli_full_7500.jsonl         # fuente completa (5010 test + 2490 val)
│   ├── dev/                                   # datasets activos
│   │   ├── xnli_combined_dev_200.jsonl        # gold canónico (A139/B19/C23/D19)
│   │   ├── xnli_sample_300_v2_test.jsonl      # muestra 300 (en validation app)
│   │   ├── cultural_adaptations.jsonl         # ~394 inst culturalmente complejas (Opus)
│   │   ├── xnli_native_validated_60.jsonl     # 60 inst con validación nativa
│   │   └── processed_idxs.json               # tracker de índices procesados
│   └── qa/                                    # QA dataset — tarea 3
│       ├── scripts/{generate,validate}_qa_dataset.py
│       └── qa_stories_{dataset,dev,train,test}.jsonl
├── pipeline_traduccion/
│   ├── scripts/                               # translate, validate, visualize, optimize, sample
│   ├── prompts/                               # prompt_v2_cultural_inline.txt (activo) + _archive/
│   └── referencias/                           # historial_prompts.md, cronologia_datos.md, _pendientes.md
├── pipeline_evaluacion/
│   ├── scripts/evaluate_against_gold.py
│   ├── error_cases/xnli_error_cases_15.jsonl  # crece con el tiempo
│   ├── respuestas_anotadores/                 # CSVs de validación nativa
│   └── referencias/                           # _review_gemini/gold_200/opus_anglos
├── results/
│   ├── experiments/                           # outputs JSONL + report + eval por config
│   └── analisis_v1_vs_v2.ipynb + *.png + ranking_vocab_xnli.tsv
├── validation_app/                            # encuesta Supabase + vanilla JS (Vercel)
├── Referencias/
│   ├── Papers/                                # papers académicos
│   ├── Tesis_compañeros/                      # Schmidt, Bolaños, GutterTeo, LouysSanso
│   └── texts/                                 # corpus Cuentos ET (30 cuentos RP)
├── scripts/check_env.py
├── .claude/skills/                            # skills de Claude Code
├── CLAUDE.md                                  # instrucciones del repo para Claude Code
└── learning_claude.md                         # guía personal de Claude Code
```

## Papers clave
| Paper | Venue | Aporte |
|-------|-------|--------|
| Conneau et al. 2018 | EMNLP | XNLI original |
| Artetxe et al. 2020 | ACL | Translation artifacts, translationese — justifica ES→RP |
| Ebrahimi et al. 2022 | ACL | AmericasNLI, precedente ES→lengua objetivo |
| Heredia et al. 2024 | NAACL | XNLIeu, arquitectura traducción + capa nativa |
| Bengoetxea et al. 2025 | CoNLL | XNLIvar, gap rioplatense explícito |
| Lopetegui et al. 2025 | VarDial | DSL-TL, 38% ejemplos comunes ES ibérico vs RP |
| Lopetegui et al. 2025 | CMCL | Corpus Cuentos ET, base directa de la tesis |
| Pérez et al. 2025 | NAACL | Hate speech RP, baseline BETO F1=63.5 |
| Deng et al. 2024 | ACL | Gaze supervision, método base ET-augmentado |
| Faisal et al. 2024 | ACL | DialectBench, rioplatense ausente |
| Ebing & Glavaš 2024 | ACL | Translationese mínimo para variedades mismo idioma |

## Estado actual (mayo 2026)

### Completado ✅
- Decisión ES→RP fundamentada en literatura
- Tipología A/B/C/D/E definida y estabilizada
- Pipeline de traducción: Gemini 2.5 Flash + prompt v2_cultural_inline
- **Combined dev 200** (`data/dev/xnli_combined_dev_200.jsonl`): gold canónico revisado manualmente. Distribución: A 139 / B 19 / C 23 / D 19
- **Cultural adaptations** (`data/dev/cultural_adaptations.jsonl`): ~394 instancias del full 7500 con candidatos culturales, procesadas por Opus
- **Sample 300** (`data/dev/xnli_sample_300_v2_test.jsonl`): 300 instancias del full 7500, Gemini v2 + validación Sonnet, 89.4% aprobadas
- Validation app deployada en Vercel (Supabase backend); sample 300 cargado
- Repo reorganizado: `pipeline_traduccion/` + `pipeline_evaluacion/` + `data/dev/`
- Cronología de datos documentada en `pipeline_traduccion/referencias/cronologia_datos.md`

### En progreso 🔄
- Prompt v2 con reglas candidatas de sesiones de revisión pendientes de incorporar (ver `pipeline_evaluacion/referencias/_review_gemini.txt`)
- Revisión nativa multi-anotador: app lista, anotadores pendiente de convocar

### Pendiente ⏳
- Pipeline de evaluación automática (Sonnet/Haiku como jueces sobre output Gemini)
- Continuar traducción del full 7500 en batches de 300
- Test set: anotar instancias adicionales del full 7500
- Fine-tuning BETO/XLM-R en las 4 condiciones (ES→ES, ES→RP, RP→RP, RP→ES)
- Experimentos ET-augmentado (Deng et al. 2024 + ablación MLM aleatorio)
