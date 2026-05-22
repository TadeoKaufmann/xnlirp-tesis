# Pendientes — validation_app

## UI / UX

- [ ] **Mejorar visibilidad de "Instancia X de Y"** — el contador en el header sticky en mobile todavía no se ve bien en Chrome iOS. Revisar tamaño/contraste o explorar alternativa de layout.

- [ ] **Randomizar orden de instancias** — actualmente se entregan en orden ascendente por idx, lo que hace que pares con misma premisa y distinta hipótesis aparezcan juntos. Confunde a los anotadores (creen que vieron esa instancia). Fix: shuffle client-side después de cargar `availableInstances` (1 línea JS, sin cambios en Supabase ni recarga de datos).

## Datos / pipeline post-validación

- [ ] **Workflow de descarga y re-evaluación** — una vez terminada una ronda de anotación:
  1. Exportar todas las respuestas de Supabase (`Respuestas` + join con `instancias`)
  2. Traer el JSONL acá y correr `evaluate_against_gold.py`
  3. Limpiar `reservas` (y opcionalmente `Respuestas`) para empezar nueva ronda
  Diseñar script o queries SQL para este flujo.
