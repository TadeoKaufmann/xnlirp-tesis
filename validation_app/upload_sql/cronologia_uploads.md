# Cronología de uploads a Supabase — tabla instancias

Los SQLs de cada upload se borran tras ejecutarse (son regenerables desde los JSONL
en `validation_app/to_upload/`). Este archivo es el registro permanente.

Para regenerar un SQL: usar el skill `supabase-instance-upload` o el script
`validation_app/scripts/upload_to_supabase.py`.

---

## 2026-05-14 — Sample 300 (primera carga)

- **Batch:** `sample_300_v2_test_2026-05-14`
- **Instancias:** 300 (idx del full 7500, Gemini v2 + validación Sonnet)
- **Fuente:** `data/dev/xnli_sample_300_v2_test.jsonl`
- **SQL:** archivado en `_archive/replace_all_sample_300_2026-05-14.sql`
- **Modo:** replace_all (primera carga, tabla vacía)

## 2026-05-26 — Carga completa 6739 instancias

- **Batch:** `full_6739_2026-05-26`
- **Instancias:** 6739 (combinación de todos los batches ok de `to_upload/`)
- **Fuente:** `validation_app/to_upload/combined_6884_full.jsonl`
- **SQL:** generado como `replace_all_6739_2026-05-26.sql`, ejecutado en 4 chunks
  por límite del SQL editor de Supabase (~500KB por chunk)
- **Modo:** replace_all (reemplazó las 300 anteriores)
- **Resultado:** tabla instancias con 6739 filas, batch_name = `full_6739_2026-05-26`
