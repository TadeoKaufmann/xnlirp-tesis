# Historial de cambios al prompt

Registro cronológico de evolución del prompt v1 y v2. Útil para analizar cómo fue cambiando la estrategia de adaptación dialectal a lo largo del proyecto.

---

## Prompt v1 — actualización base (mayo 2026)

Cuatro cambios al prompt v1:

1. **D4 con caveat de Restricción 5**: D4 solo aplica cuando una traducción es claramente incorrecta; si ambas son sinónimos válidos, es A. Ejemplo nuevo `médico/doctor`.
2. **`pues` con mapeo contextual**: 4 contextos (muletilla / causal / consecutivo / cierre) en lugar de reemplazo mecánico.
3. **Caveat corto de registro arcaico para voseo**: si hay marcas de registro decimonónico/aristocrático (ej. "su señoría"), no aplicar voseo.
4. **Regla acotada de eliminación de clítico anafórico**: `lo`/`la` se elimina solo cuando es redundante tras adverbio anafórico (`así`, `eso`); ejemplo único `así lo creí → así creí`.

---

## Prompt v1 — Fase 1 (mayo 2026, post validación nativa batch 200-260)

Ampliación del léxico B con seis sustituciones contextuales adicionales surgidas del feedback nativo:

- `allí → ahí/allá` (paralelo a aquí→acá, contextual).
- `padre/madre → papá/mamá` (registro coloquial 1ª persona, propios padres).
- `recoger → reemplazar siempre según sentido` (levantar/juntar/cosechar/pasar a buscar según contexto; "recoger" no es natural en RP en ningún uso).
- `enviar → mandar` (registro coloquial / agente impersonal).
- `recordar X → acordarse de X` (coloquial 1ª persona, requiere ajuste de preposición).
- `pequeño/a → chico/a` (edad informal de persona/animal).

---

## Prompt v1 — Fase 1b (mayo 2026, post análisis 60 anotaciones nativas)

Cuatro reglas léxicas B adicionales emergentes del feedback (alta confianza, sin riesgo NLI):

- ~~`chaqueta → campera`~~ (eliminada mayo 2026: 0 ocurrencias en XNLI full 7.5k, sin impacto práctico).
- `ello → eso` (pronombre neutro en registro no estrictamente formal).
- `bachillerato → secundario` (nivel educativo medio en AR/UY; mantener para orientación específica del plan de estudios o sistema extranjero referido como tal).
- `repleto/a → lleno/a` (forma neutral RP; mantener solo en registro literario explícito).

v2 hereda estas cuatro reglas. v2 además aclara que **Acción de Gracias / Thanksgiving** no se adapta inline (no hay equivalente 1:1 en RP) y se MARCA en `cultural_candidates` con `category="evento_historico_especifico"` y `suggestion=null` para Fase 3.

---

## Prompt v1 — Fase 1c (mayo 2026, post análisis 60 anotaciones nativas — continuación)

Una regla léxica B adicional emergente del feedback (alta confianza):

- `joven/jóvenes → chico/a o adolescente` (sustantivo de personas en contexto informal; diminutivo/cachorro para animales; mantener como adjetivo emocional/narrativo o en registro académico). *Regla escrita por Claude Sonnet 4.6, revisada por Claude Opus 4.7.*

v2 hereda esta regla.

---

## Prompt v1/v2 — Fase 1d (mayo 2026, análisis EsPal/corpus Cuentos + frecuencias XNLI full 7.5k)

Cuatro reglas nuevas surgidas de análisis cuantitativo. Todas pendientes revisión Opus:

- `vale → dale/bueno` (27 ocurrencias XNLI, EsPal ratio 4.4x).
- `carretera → ruta/autopista` (16 ocurrencias XNLI; "autopista" si acceso controlado; nunca "calle"/"avenida").
- `jersey → buzo/pulóver` (10 ocurrencias XNLI).
- `tío → che/tipo según uso` (28 ocurrencias XNLI; mantener si es familiar; "che" si vocativo coloquial; "tipo/hombre" si referencia de género).

*Reglas escritas por Claude Sonnet 4.6.* **Todas pendientes revisión Opus.**

v1 y v2 incluyen estas reglas con tag `[Pendiente revisión Opus]`.

Dataset descargado en este período: `data/raw/xnli/xnli_full_7500.jsonl` (5010 test + 2490 val, balanceado 2500/label).

---

## Prompt v1/v2 — `dinero → plata` revisado (mayo 2026, validación nativa RP)

La regla original (plata solo en registro coloquial/personal) fue **invertida** tras validación directa con hablante nativo RP sobre 20 instancias XNLI. Plata pasa a ser el **default** en casi todos los contextos; dinero se mantiene solo cuando genuinamente suena mal en RP:

- (a) terrorismo/violencia organizada ("Al Qaeda recaudaba dinero", "talibanes querían dinero y armas").
- (b) jerga técnica extranjera (hawaladar, rupias).
- (c) compuestos lexicalizados (lavado de dinero, blanqueo de dinero, ruta del dinero).
- (d) donación institucional formal explícita.

Fondos cuando organización recauda/asigna fondos presupuestarios.

Evidencia: validación nativa + corpus comentarios AR (plata:dinero 2.4x).

---

## Pre-prompt v2 — "marker only" (mayo 2026, fase intermedia)

Archivo: `pipeline_traduccion/prompts/_archive/pre_prompt_v2_cultural_candidates_marker_only.txt`

Versión intermedia de v2 que **solo marcaba candidatos culturales** en el campo `cultural_candidates` sin aplicarlos en `prem_rp`/`hyp_rp`. Era el primer intento de separar la adaptación lingüística (A/B/C/D) de la cultural (E). Se usó para explorar qué referentes aparecían con frecuencia antes de decidir qué adaptar automáticamente y qué dejar para revisión humana (Fase 3). Fue reemplazado por el prompt v2 cultural inline que sí aplica E.1/E.2/E.3 directamente.

---

## Prompt v2 cultural inline (mayo 2026, Fase 2)

Nuevo archivo `prompt_v2_cultural_inline.txt` que reemplaza al pre-prompt "marker only". Hereda todo el v1 (Fase 1 incluida) y agrega sección E con adaptación cultural conservadora:

- Tabla escalable de nombres anglo comunes (E.1: regla de género/registro, no tabla fija).
- Festividades universales con equivalente directo (E.2: Santa Claus→Papá Noel, Easter Bunny→conejo de Pascua).
- Transposición Captain Blood → Bouchard (E.3): mapeo completo de personajes y lugares.

Topónimos, marcas, unidades imperiales y eventos históricos se MARCAN en `cultural_candidates` pero NO se modifican (Fase 3 humano-en-el-loop).

---

## Sesiones de revisión que mejoraron el prompt (mayo 2026)

Documentadas en `pipeline_evaluacion/referencias/`:

**`_review_gold_200.txt`** (2026-05-14) — Discrepancias entre salida v2 y gold combined_dev_200 (88% type acc). Dos categorías:
- *Gold incorrecto*: 10 instancias donde el modelo acertó pero el gold estaba desactualizado respecto de reglas E.3 (Captain Blood→Bouchard), pequeña→chica, muletillas (hum→mmm, uh→este...). Gold corregido en esas posiciones.
- *Errores reales del modelo*: 7 instancias de armonización prohibida (D4), D dudosos sin verificación EN, fixes de tipología dominante (B vs D). Mejoras incorporadas al prompt.

**`_review_gemini.txt`** (2026-05-14) — 15 casos del sample_300 (89.4% aprobados). Reglas candidatas surgidas:
- `monitorizar → monitorear` (regla B nueva)
- `de derechas → de derecha` (regla B nueva)
- `empollones → nerds/cerebritos` (regla B nueva)
- `amablemente → por favor` en calco formal (regla B nueva)
- `no ser loco/a por X → no entusiasmar a X` (calco anglo)
- Fix ortográfico: `Daselo → Dáselo` (esdrújula con clítico mantiene tilde)
- Política de millas en paréntesis de conversión explícita (pendiente)

**`_review_opus_anglos.txt`** (2026-05-15) — 58 instancias con nombres anglos que Opus mantuvo como type=A. Decisión final: **mantener todas las figuras públicas reales** (McKim, Gehry, Pickard, Ashcroft, Pynchon, Skeat, Boswell, Lewinsky, etc.). Resultado: regla E.1 no aplica a personas reales históricas ni científicas. Pachuco/pachuca y yiddish también se mantienen (sin equivalente RP directo).

---

## Gold — correcciones puntuales (mayo 2026)

- **idx 1522**: se agregó cambio B `así lo creí → así creí` (eliminación de clítico anafórico) en `prem_rp`.
- **Held-out 100**: correcciones de gold idx 22, 1543, 1731, 4490 → A→D (distribución final: A 72 / B 6 / C 13 / D 9).
- **Combined dev 200**: idx 3121 corregido A→B en mayo 2026 (distribución total: A 139 / B 19 / C 23 / D 19).
