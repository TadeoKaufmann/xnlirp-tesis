# Historial de decisiones técnicas — Pipeline QA

## Pendientes

- **Cuentos de Casciari**: evaluar agregar cuentos de Hernán Casciari al corpus. Son texto rioplatense contemporáneo, podrían enriquecer el dataset especialmente para el split train. Pendiente: seleccionar cuentos, verificar derechos/disponibilidad, correr pipeline de generación en un round nuevo.


## Cronología

**Fase 1 — Rounds 001 y 002 (prompt v2, Axolotl + Ahora debería reírme)**
Primeras dos pruebas del pipeline. Validación Haiku: 91-95% clean. Formato viejo (`qa_stories_dataset.jsonl`). Sirvieron para validar el concepto.

**Fase 2 — Rounds 003 y 004 (prompt v2, cuentos TRAIN)**
Se generaron ~2700 instancias de 18 cuentos de train en batch único. Validación: 13-24% clean. Diagnóstico: la regla 5 del prompt v2 ("no repetir palabras") hacía que Gemini reformulase tan agresivamente que Haiku no podía conectar la pregunta a ninguna oración sin contexto.

**Fase 3 — Rounds 005 y 006 (prompt v2, DEV y TEST)**
Cuentos más simples y cortos. Validaron al 93%+ sin cambios al prompt — el problema de v2 no se manifestó en cuentos auto-contenidos.

**Fase 4 — Creación del prompt v3**
Reescritura de la regla 5: de "no repetir palabras" a "máximo 2 palabras exactas como referencia blanda, preferir vocabulario que aparezca en negativas, ancla única por pregunta". Se agregó regla 8 (test mental antes de responder) y manejo explícito de pronombres. Calibración iterativa en 15 muestras de round_003: primera versión demasiado fácil (overlap excesivo), versión final con balance correcto.

**Fase 5 — Regeneración con v3 (script _regen_questions.py)**
En vez de tirar las oraciones, se regeneran solo las preguntas manteniendo las 5 oraciones del grupo. Tres bugs encontrados y corregidos durante esta fase:
1. Bug de batch ordering de Gemini (resultados desordenados): fix via lookup por ID embebido en prompt.
2. Bug de fuente incorrecta en re-runs: script leía `generated.jsonl` aunque existía `generated_v3.jsonl`.
3. Pérdida de `validation_haiku.jsonl`: el archivo fue sobreescrito por una validación sobre el archivo truncado. Se creó `_recover_validation.py` para reconstruir el estado sin gastar API.

**Fase 6 — Round_003 regenerado y validado**
494 → 485 grupos (10 SKIP/FAIL). Validación Haiku: **94% clean**. Cuentos antes con 5% clean (Sombras, El origen) pasaron a 93-96%.

**Fase 7 — Round_004 regenerado y validado**
1293 grupos originales → 1276 grupos con v3. Validación Haiku: **92.2% clean**. Mismos cuentos problemáticos (El espejo 82%, Embarrar 82%) — dificultad del texto, no del prompt.

**Fase 8 — Build dataset final**
`build_qa_final.py`: deduplica por (story, answer_unit_idx) prefiriendo round más reciente, agrega campos `is_et` y `round`, escribe splits. Resultado: **1788 preguntas / 8940 instancias** — 1382 train, 185 dev, 221 test.

---

## Decisión fija: Gemini genera, Haiku evalúa

El pipeline de construcción del dataset QA sigue siempre este esquema:
- **Generación de preguntas:** Gemini 2.5 Flash via Gemini Batch API
- **Validación de calidad:** Claude Haiku 4.5 via Anthropic Batch API

Esta separación es intencional y metodológicamente importante: el evaluador no conoce el generador, lo que evita sesgo de auto-evaluación. Los resultados de validación son comparables entre rounds porque el evaluador es siempre el mismo modelo. No usar OpenAI para validación aunque esté disponible, para mantener la referencia consistente.

---

## Cronología

### Rounds 001–002 — prompt v2 (Axolotl + Ahora debería reírme)

- Prompt v2 con regla "no repetir palabras exactas de la oración target".
- Validación Haiku: **91–95% clean**. Estos dos cuentos son narrativamente simples y auto-contenidos.
- Conclusión: pipeline funcionando, prompt v2 viable para cuentos cortos/simples.

### Rounds 003–004 — prompt v2 (18 cuentos TRAIN + DEV)

- Mismo prompt v2, mismos parámetros. Generados en batch único (~2700 instancias de una sola vez).
- Validación Haiku round_003: **24.3% clean** (490 grupos). Round_004: ~13% clean.
- Cuentos problemáticos: Sombras sobre vidrio esmerilado (5–10%), El origen de las especies (4.8%), Carta a una señorita en París (10%), Rebeca (7.9%).
- Cuentos bien: El loco cansino (66%), El negro de París (76%).

**Causa raíz diagnosticada:** la regla "no repetir palabras" hacía que Gemini reformulase tan agresivamente que Haiku, viendo 5 oraciones sin contexto, no podía conectar la pregunta a ninguna. La pregunta era correcta conceptualmente pero léxicamente desconectada de la positiva. Los cuentos simples y cortos (El loco cansino, El negro de París) funcionaron porque sus oraciones son más auto-contenidas y concretas. Los cuentos literarios complejos (Sombras, El origen, Carta) tienen oraciones que dependen de contexto narrativo y Gemini usaba ese contexto para generar la pregunta, violando la regla 1 del prompt.

### Rounds 005–006 — prompt v2 (DEV + TEST)

- DEV: **93% clean**. TEST: estimado similar.
- Estos cuentos son también más simples/cortos → el problema no se manifestó.

---

## Prompt v2 → v3 (2026-06-05)

**Problema central de v2:** regla 5 decía "no repetir palabras exactas". Gemini obedecía reformulando con sinónimos, pero Haiku no podía matchear pregunta↔oración sin vocabulario compartido.

**Cambios en v3 (`qa/prompts/generation/v3.txt`):**

1. **Regla 5 reescrita:** de "no repetir" a "máximo 2 palabras exactas como referencia blanda; preferir palabras que también aparezcan en las negativas". Objetivo: la pregunta debe sentirse como reformulación pero compartir suficiente vocabulario para que sea identificable.

2. **Regla de ancla única:** si la oración tiene muchos detalles, elegir UNO como ancla. Evitar preguntas tipo "¿qué X y qué Y?" que preguntan sobre dos cosas a la vez — hacen la tarea demasiado obvia por la combinación de detalles.

3. **Regla de vocabulario en negativas:** preferir palabras que aparezcan en alguna negativa, para que el solapamiento léxico no sea suficiente para resolver la tarea (BERT no puede ganar solo con keyword matching).

4. **Test explícito (regla 8):** antes de devolver la pregunta, verificar mentalmente: "si alguien ve SOLO la oración target sin contexto, ¿puede responder?". Si no, SKIP.

5. **Manejo de pronombres (regla 2):** si la oración solo tiene pronombres, identificar el personaje con el contexto y nombrarlo en la pregunta. Si no se puede identificar con certeza, SKIP.

**Iteraciones de calibración de v3 (sesión 2026-06-05):**
- Primera versión: "al menos 1-2 palabras exactas" → preguntas que repiten demasiado ("¿cuántos ejemplares había y qué hacía la mayoría?") — demasiado fácil, BERT resuelve por overlap.
- Segunda versión: "máximo 2 palabras, suave" + ancla única + preferir vocabulario de negativas → balance correcto. Preguntas más difíciles y discriminativas.
- Evaluación en 15 muestras de round_003: cualitativamente mejores, más difíciles pero respondibles.

---

## Script _regen_questions.py — regeneración de no-clean

En vez de tirar los grupos no-clean y regenerar desde cero (perdiendo las oraciones ya alineadas), se decidió regenerar SOLO la pregunta manteniendo las 5 oraciones intactas.

El script lee los grupos no-clean de `validation_haiku.jsonl` y envía a Gemini: oración positiva + 4 negativas + pool de reemplazos. Gemini devuelve una nueva pregunta (y opcionalmente un swap de negativa problemática). La salida se guarda en `generated_v3.jsonl`.

**Bug 1 — fuente incorrecta en re-runs (corregido 2026-06-05):**  
Al correr el script por segunda vez, `validation_haiku.jsonl` ya tenía las preguntas nuevas de `generated_v3.jsonl`, pero el script seguía leyendo `generated.jsonl` (preguntas viejas). El matching por `(story, question)` fallaba porque las preguntas habían cambiado → 485 aparecían como "clean" y solo 10 como a regenerar (debían ser ~371).  
Fix: el script ahora prefiere `generated_v3.jsonl` si existe, y matchea no-clean por `(story, answer_unit_idx)` en vez de por pregunta (el índice es estable entre pasadas).

**Bug 2 — batch ordering (corregido 2026-06-04):**  
Al procesar round_003 (377 prompts), 5 requests fallaron en el batch de Gemini. Como el código asumía que `inlined_responses[i]` corresponde a la request `i`, todos los resultados posteriores al fallo quedaban desplazados. Resultado: preguntas sobre "Leopoldo" (Sombras) asignadas al grupo de "El espejo", etc.  
Fix: se embebe `[ID:{task_id}]` en cada prompt y se le pide a Gemini que devuelva el ID en el JSON (`{"id": 42, "question": "..."}`). Al parsear, se verifica que el ID coincide.

**Bug 3 — Gemini Batch no garantiza orden (corregido 2026-06-05):**  
Aunque el Bug 2 agregó verificación de ID, el código seguía haciendo `zip(tasks, raw_results)` por posición. En la corrida de 371 prompts, 263 resultaron MISMATCH porque `inlined_responses` llegó en orden distinto al de `inlined_requests`.  
Fix: en vez de `zip` por posición, se parsea TODOS los resultados para extraer el ID devuelto, se construye un mapa `{id → respuesta}`, y cada tarea busca su resultado por ID. Esto es robusto independientemente del orden en que Gemini devuelva las respuestas.

---

## Decisión: no mezclar evaluadores entre rounds

Al agotarse los créditos de Haiku en la sesión del 2026-06-05, surgió la pregunta de si usar Gemini o OpenAI para validación. Decisión: esperar a tener Haiku disponible. Razones:
- Consistencia: todos los rounds evaluados con el mismo modelo → resultados comparables.
- Trazabilidad para la tesis: "generado con Gemini, evaluado con Haiku" es una afirmación limpia.
- Gemini como auto-evaluador introduce sesgo (mismo modelo que genera y evalúa).
- OpenAI requeriría agregar soporte al código y rompe la uniformidad sin beneficio claro.
