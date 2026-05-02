# Tesis de Maestría — Benchmarking NLU en Español Rioplatense con Eye-Tracking

## Hipótesis central
La distancia dialectal entre el corpus de eye-tracking rioplatense y el benchmark de evaluación afecta el rendimiento de los modelos NLU, y el augmentado con eye-tracking (ET) ayuda especialmente en low-resource (K=200/500/1000).

## Componentes
- Corpus ET: Cuentos (Travi et al. 2026) — 30 cuentos, 113 participantes nativos
- Método: augmentación MLM guiada por fixation duration. Ablación con MLM aleatorio. Base: Deng et al. ACL 2024.
- Benchmark 3 tareas: (1) Hate speech RP — Pérez et al. NAACL 2025, BETO F1=63.5. (2) XNLIrp — en construcción. (3) QA Cuentos — NLI binario sobre los cuentos del corpus ET.

## Decisiones metodológicas
- Ruta de traducción: ES estándar → RP (no EN → RP)
- Pipeline: Gemini 2.5 Flash como borrador + revisión nativa multi-anotador
- Tipología: A (común), B (léxico), C (morfosintáctico/voseo), D (corrección error traducción)
- Cultural candidates: marcados en Fase 1, adaptados en Fase 2
- Levenshtein normalizado ES↔RP como control de calidad y variable de análisis
- 4 condiciones experimentales: ES→ES, ES→RP, RP→RP, RP→ES
- Modelos a evaluar: BETO, XLM-RoBERTa

## Stack técnico
- Python local Windows
- Gemini 2.5 Flash (Google AI Studio, free tier)
- JSONL como formato principal
- Google Sheets para revisión visual ocasional
- API key en .env

## Estructura de archivos
[REEMPLAZAR CON OUTPUT DE tree /F DESDE LA RAÍZ DEL PROYECTO]

## Papers clave
| Paper | Venue | Aporte |
|-------|-------|--------|
| Conneau et al. 2018 | EMNLP | XNLI original |
| Artetxe et al. 2020 | ACL | Translation artifacts, translationese |
| Ebrahimi et al. 2022 | ACL | AmericasNLI, precedente ES→lengua objetivo |
| Heredia et al. 2024 | NAACL | XNLIeu, arquitectura traducción + capa nativa |
| Bengoetxea et al. 2025 | CoNLL | XNLIvar, gap rioplatense explícito |
| Lopetegui et al. 2025 | VarDial | DSL-TL, 38% ejemplos comunes ES ibérico vs RP |
| Lopetegui et al. 2025 | CMCL | Corpus Cuentos ET, base directa de la tesis |
| Pérez et al. 2025 | NAACL | Hate speech RP, baseline BETO F1=63.5 |
| Deng et al. 2024 | ACL | Gaze supervision, método base ET-augmentado |
| Faisal et al. 2024 | ACL | DialectBench, rioplatense ausente |
| Ebing & Glavaš 2024 | ACL | Translationese mínimo para variedades mismo idioma |

## Estado actual
- ✅ xnli_pilot_500.jsonl — 500 instancias estratificadas seed 42
- ✅ xnli_pilot_30_annotated.jsonl — 30 instancias gold revisadas manualmente
- ✅ Decisión ES→RP fundamentada en literatura
- ✅ Protocolo de traducción definido
- ✅ Entorno virtual y .env configurados
- ✅ Scripts del pipeline generados por Claude Code
- 🔄 Loop de optimización de prompt — en ejecución
- ⏳ Revisión nativa multi-anotador — pendiente
- ⏳ Fine-tuning BETO/XLM-R — pendiente
- ⏳ Experimentos ET-augmentado — pendiente