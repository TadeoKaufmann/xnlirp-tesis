# References — anclas para el review

Este skill no copia los archivos de referencia; los lee desde el repo principal.

## Archivos de referencia

- **Gold dialectal anotado a mano**: `data/processed/xnli_combined_dev_200.jsonl`
  200 instancias con type A/B/C/D/E + changes + notes. Es la fuente de verdad
  sobre qué cambios son obligatorios y cuáles son opcionales en RP. Distribución:
  A 120, B 28, C 23, D 24, E 5 (post fixes 2026-05-14).

- **Adaptaciones culturales**: `data/processed/cultural_adaptations.jsonl`
  387 instancias culturales (clusters 911_alqaeda, indiana, texas, california,
  fbi_cia, pak_afg) procesadas por Opus. Referencia para tipo E.3 / E.4.

- **Prompt v2**: `scripts/prompts/prompt_v2_cultural_inline.txt`
  Las reglas mismas. Si dudás de si una regla aplica, leelo. Tiene principio
  rector "cambio mínimo + flageo ante la duda".

- **CLAUDE.md**: decisiones de alto nivel, tipología A/B/C/D/E, historia
  de revisiones de prompt.

- **Bitácora de decisiones (archivada)**: `scripts/_archive/_ejemplos_xnli.txt`
  Razonamiento histórico sobre cada palabra/regla. Útil si dudás del "por qué"
  detrás de una regla específica.

## Cómo usarlas en review

1. Si el run aplica un cambio léxico y dudás de si es B o A:
   - Buscar en el gold un caso con la misma palabra/construcción.
   - Si el gold la cambia → el run hizo bien (APROBAR).
   - Si el gold la mantiene → el run posiblemente sobreaplica (REVISAR).

2. Si el run propone una transposición cultural (Captain Blood→Bouchard, 9/11→AMIA):
   - Verificar que sea CONSISTENTE prem y hyp.
   - Verificar contra `cultural_adaptations.jsonl` que ya tenga ese mapeo.
   - Si es mapeo nuevo no documentado → REVISAR.

3. Si el run propone D:
   - Verificar que el ES tenga error OBJETIVO (no sinonimia válida).
   - Si la hyp usa una palabra distinta pero ambas son traducciones válidas → A,
     no D. Eso es armonización (RECHAZAR si el run hizo D).
