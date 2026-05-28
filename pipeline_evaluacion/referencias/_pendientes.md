# Pendientes: pipeline de evaluación

---

## Indiana / Indianapolis — revisar adaptaciones culturales

**Estado:** aplazado (mayo 2026) — prioridad: continuar traducción.

Indiana e Indianapolis fueron **cambiados a provincias argentinas** en `cultural_adaptations.jsonl`,
no mantenidos como topónimos EEUU (a diferencia de lo que el plan inicial asumía).

**Qué revisar cuando haya tiempo:**

1. Ver qué provincia se usó para cada cluster (`data/dev/cultural_adaptations.jsonl`, filtrar por prem_es que contiene "Indiana" o "Indianapolis").
2. Verificar que la adaptación preserva el label NLI (entailment/neutral/contradiction) en todas las instancias afectadas.
3. Verificar que las ~42 instancias Indiana y ~27 instancias Indianapolis son internamente consistentes (misma provincia usada para el mismo referente).
4. Si hay instancias donde la adaptación a provincia AR rompe la lógica (ej. "Universidad de Indiana" no tiene equivalente directo), considerar si conviene mantener como topónimo o usar generalización.

**Referencia:** plan `tingly-sleeping-clock.md`, clusters Indiana e Indianapolis.
