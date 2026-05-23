# Pendientes — validation_app

## UI / UX

- [x] **Mejorar visibilidad de "Instancia X de Y"** — resuelto: sticky sin wrapper, fondo hex explícito para iOS Chrome.

- [x] **Randomizar orden de instancias** — resuelto: Fisher-Yates shuffle client-side después de confirmar reservas.

## Datos / pipeline post-validación

- [ ] **Workflow de descarga y re-evaluación** — una vez terminada una ronda de anotación:
  1. Exportar todas las respuestas de Supabase (`Respuestas` + join con `instancias`)
  2. Traer el JSONL acá y correr `evaluate_against_gold.py`
  3. Limpiar `reservas` (y opcionalmente `Respuestas`) para empezar nueva ronda
  Diseñar script o queries SQL para este flujo.
