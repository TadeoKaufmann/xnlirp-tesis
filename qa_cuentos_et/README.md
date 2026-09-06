# QA-Cuentos ET

Primer dataset de selección de oraciones respuesta (comprensión lectora) en español rioplatense, construido sobre el corpus **Cuentos ET** (Travi et al., 2026, *Scientific Data*): 30 cuentos de ficción breve en español rioplatense, 20 de ellos leídos con eye-tracking por 113 lectores nativos.

La tarea es clasificación binaria: dado un par (pregunta, oración candidata del cuento), predecir si esa oración responde la pregunta.

## Dataset

`dataset/qa_{train,dev,test}.jsonl` — 1.788 preguntas, 8.940 instancias (1 positiva + 4 negativas por pregunta). Splits asignados **a nivel de cuento** (ningún cuento aparece en más de una partición, evita filtración narrativa):

| Split | Cuentos | Preguntas | Instancias |
|---|---|---|---|
| train | 11 | 668 | 3.340 |
| dev | 10 | 639 | 3.195 |
| test | 9 | 481 | 2.405 |

El split de test está balanceado ~50/50 entre cuentos con señal de eye-tracking real y cuentos sin ella, para poder comparar directamente el efecto de esa señal.

Campos principales: `id`, `story` (nombre del cuento), `unit_idx`/`unit` (oración candidata), `question`, `label` (1 si la oración responde la pregunta), `question_type` (`factual` o `inferencial`), `answer_unit_idx`, `split`.

## Pipeline

1. **Selección de oración target**: se filtran oraciones de 8-80 palabras dentro de cada cuento.
2. **Pool de negativas duras**: en vez de negativas aleatorias (que saturaban F1 en ~90-93%), se seleccionan las 4 oraciones del mismo cuento más *semánticamente* parecidas a la target vía embeddings (`text-embedding-3-small` de OpenAI, techo de similitud coseno 0,55) — esto obliga al modelo a distinguir por contenido, no por solapamiento léxico superficial.
3. **Generación de la pregunta**: Gemini 2.5 Flash genera una pregunta cuya única respuesta correcta entre las 5 candidatas es la oración target. Mitad de las preguntas son inferenciales (exigen sinonimia o sentido común, sin solapamiento léxico directo) y mitad son literales reformuladas.
4. **Validación**: Claude Haiku (modelo distinto del generador) recibe la pregunta y las 5 oraciones sin etiquetar, y debe elegir exactamente la target para que la instancia se considere válida.

- **`prompts/generation/{v1,v2,v3}.txt`** — evolución del prompt de generación de preguntas.
- **`prompts/hardening_v1.txt`** — prompt usado para regenerar preguntas demasiado fáciles.
- **`prompts/grader_v1.txt`** — prompt del validador (Claude Haiku).
- **`scripts/generate_batch.py`** — generación de preguntas en batch con Gemini.
- **`scripts/build_hard_negatives_embeddings.py`** — selección de negativas duras vía embeddings (método final).
- **`scripts/build_hard_negatives.py`** — variante anterior vía TF-IDF (referencia, superada por embeddings).
- **`scripts/validate_consistency.py`** — validación con Claude Haiku.
- **`scripts/harden_dataset.py`** — regeneración de preguntas/negativas que no pasaron la validación.
- **`scripts/build_qa_final.py`** — ensamblado del dataset final con deduplicación y asignación de splits.

## Requisitos

Variables de entorno esperadas (`.env`, no incluido): `GOOGLE_API_KEY` (Gemini), `ANTHROPIC_API_KEY` (validación con Claude Haiku), `OPENAI_API_KEY` (embeddings).
