# XNLIrp

Primera adaptación de [XNLI](https://github.com/facebookresearch/XNLI) al español rioplatense (RP). Parte de las 7.500 instancias de evaluación de XNLI (5.010 de test + 2.490 de validation, ya traducidas profesionalmente al español peninsular por los autores originales) y las adapta al rioplatense preservando la etiqueta de inferencia (`entailment` / `neutral` / `contradiction`) y la correspondencia exacta entre ambas versiones.

Esto permite evaluar el mismo modelo, sobre las mismas instancias, en las dos variedades del español, aislando el efecto puramente dialectal.

## Dataset

`dataset/dataset_final.jsonl` — 7.500 instancias. Cada línea tiene, entre otros, estos campos:

| Campo | Descripción |
|---|---|
| `idx` | índice original de XNLI |
| `label`, `label_int` | etiqueta NLI (`entailment` / `neutral` / `contradiction`) |
| `prem_en`, `hyp_en` | premisa e hipótesis en inglés (XNLI original) |
| `prem_es`, `hyp_es` | premisa e hipótesis en español peninsular (XNLI original) |
| `prem_rp`, `hyp_rp` | premisa e hipótesis adaptadas al español rioplatense |
| `type` | tipo de adaptación: `A` (sin cambio), `B` (léxico), `C` (morfosintaxis/voseo), `D` (corrección de un error de traducción del ES original), `E` (adaptación cultural) |
| `secondary_features` | tipos secundarios cuando la instancia combina más de un cambio |
| `lev_total` | distancia de Levenshtein normalizada entre la versión ES y RP |
| `split` | `test` o `validation` (partición original de XNLI) |
| `provenance.*` | veredicto del evaluador automático y de la validación nativa (score 1-5, cantidad de anotadores) |

**Distribución de tipos:** A 50,8% / B 16,0% / C 7,0% / D 14,9% / E 11,2%. El 49,2% de las instancias requirió al menos un cambio; el 34,3% tiene cambio dialectal puro (B+C+E). La proporción varía fuertemente por género textual de XNLI (60,8% en conversaciones telefónicas, 14,7% en documentos gubernamentales).

**Validación:** evaluador automático (gpt-4o-mini) con 98,5% de acuerdo contra un gold de 200 instancias revisado manualmente, más una campaña de validación nativa con 340 hablantes rioplatenses (7.120 respuestas, rating promedio 3,73/5, 84,2% de instancias con score ≥3). Ver `respuestas_anotadores_anonimizado.csv` (nombres reemplazados por IDs secuenciales).

## Pipeline

```
Gemini 2.5 Flash traduce ES→RP (prompt v2)
    └─► Evaluador automático (gpt-4o-mini, Batch API)
           ├─ OK ──► Validación nativa (app web, escala 1-5)
           │            ├─ score ≥3 ──► dataset final
           │            └─ score <3 ──► corrección manual + re-traducción
           └─ no OK ──► corrección manual + re-traducción
```

- **`prompts/prompt_v2_cultural_inline.txt`** — prompt final usado para adaptar las 7.500 instancias (tipología A/B/C/D/E, reglas léxicas, subreglas de adaptación cultural).
- **`prompts/grader_prompt.txt`** — prompt del evaluador automático.
- **`scripts/translate_xnli.py`** — harness de traducción vía Gemini Batch API.
- **`scripts/grade_translations.py`** — evaluación automática vía OpenAI Batch API.
- **`scripts/evaluate_against_gold.py`** — comparación de una corrida contra un gold set.
- **`scripts/build_dataset_final.py`** — ensamblado del dataset final a partir de las traducciones y correcciones.

Decisión metodológica clave: se tradujo **ES→RP** (no EN→RP directamente) para no mezclar dos tipos de *translationese* distintos al comparar peninsular vs. rioplatense, y se adaptó siempre el **triplete completo** (premisa + hipótesis + etiqueta) en una sola llamada, para mantener la consistencia de nombres/referentes entre ambos textos.

## Requisitos

Variables de entorno esperadas por los scripts (`.env`, no incluido): `GOOGLE_API_KEY` (Gemini Batch API), `OPENAI_API_KEY` (grading).
