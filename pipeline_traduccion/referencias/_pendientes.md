# Pendientes: vocabulario XNLI a resolver

Palabras identificadas en análisis de vocabulario completo (7 500 instancias). Ordenadas por CNT descendente dentro de cada categoría. Contador de ocurrencias = suma de apariciones en prem_es + hyp_es. Ir resolviendo de a una: verificar ejemplos, decidir regla de prompt y marcar con ✓.

Leyenda columna ACCIÓN: **mantener** = dejar sin tocar (nombre propio, técnico, NLI-crítico); **regla** = agregar instrucción al prompt; **resuelto** = ya cubre el prompt actual.

## 8.1 Inglés / lugares / nombres propios

| ☐ | PALABRA | CNT | CONTEXTO / EJEMPLOS | ACCIÓN PROPUESTA |
|---|---------|-----|---------------------|-----------------|
| ☐ | blood | 131 | Personaje de novela *Captain Blood* (Rafael Sabatini). "el Capitán Blood ordenó..." | mantener (nombre propio literario) |
| ☐ | bishop | 96 | Personaje *Captain Blood*. "el coronel Bishop amenazó..." | mantener (nombre propio) |
| ☐ | wolverstone | 78 | Personaje *Captain Blood*. "Wolverstone respondió..." | mantener (nombre propio) |
| ☐ | lord | 76 | Título nobiliario inglés en texto original. "Lord Sunderland firmó..." | mantener (título en contexto histórico inglés) |
| ☐ | ogle | 67 | Personaje *Captain Blood*. "Ogle tomó el mando..." | mantener (nombre propio) |
| ☐ | indiana | 63 | Estado EEUU o referente geográfico. "en Indiana encontraron..." | mantener (topónimo) |
| ☐ | texas | 82 | Estado EEUU. "en Texas hay..." | mantener (topónimo) |
| ☐ | california | 38 | Estado EEUU. | mantener (topónimo) |
| ☐ | james | 43 | Nombre propio anglosajón. "James dijo que..." | v2: adaptar si ficción no célebre; v1: mantener |
| ☐ | john | 46 | Nombre propio anglosajón. "John respondió..." | v2: adaptar si ficción no célebre; v1: mantener |
| ☐ | pitt | 41 | Nombre propio / topónimo (Pittsburgh, William Pitt). "Pitt declaró..." | mantener (figura histórica o topónimo) |
| ☐ | augusta | 35 | Topónimo (Augusta, Georgia) o nombre propio. "en Augusta se realizó..." | mantener |
| ☐ | william | 24 | Nombre propio anglosajón / figura histórica. | mantener (histórico frecuente) |
| ☐ | ramona | 28 | Nombre propio femenino. "Ramona dijo que..." | v2: mantener si es personaje establecido; revisar contexto |
| ☐ | wade | 23 | Nombre propio / término jurídico (Roe v. Wade). "Wade argumentó..." | mantener |
| ☐ | clarke | 27 | Nombre propio anglosajón. | mantener |
| ☐ | of | 36 | Preposición inglesa embebida en nombre propio o sigla. "Bank of America..." | mantener (parte de nombre compuesto) |
| ☐ | center | 35 | Parte de nombre propio ("World Trade Center"). "en el Center se..." | mantener (parte de nombre propio) |
| ☐ | world | 28 | Parte de nombre propio ("World Trade Center"). | mantener |
| ☐ | city | 26 | Parte de nombre propio ("New York City", "Kansas City"). | mantener |
| ☐ | lsc | 32 | Sigla (contexto *Captain Blood*: LSC = ?). Revisar ejemplos. | mantener (sigla / nombre propio) |
| ☐ | scr | 23 | Sigla. Revisar contexto exacto. | mantener (sigla) |
| ☐ | cio | 42 | Sigla o nombre propio. "el CIO informó..." | mantener (sigla) |
| ☐ | fdny | 37 | Fire Department of New York (contexto 9/11). | mantener (sigla institución extranjera) |
| ☐ | newsweek | 24 | Publicación norteamericana. "según Newsweek..." | mantener (nombre propio de medio) |
| ☐ | ed | 30 | Nombre propio (Edward) abreviado o sigla. Revisar. | mantener o ver si es nombre ficción |
| ☐ | m | 37 | Inicial de nombre propio o sigla. | mantener |
| ☐ | p | 29 | Inicial de nombre propio. | mantener |
| ☐ | indianápolis | 33 | Topónimo. | mantener |
| ☐ | indianapolis | 8 | Variante sin tilde del mismo topónimo. Posible error tipográfico. | **regla D**: normalizar tilde → "indianápolis" si corresponde |

## 8.2 Peninsularismos léxicos

| ☐ | PALABRA | CNT | CONTEXTO / EJEMPLOS | ACCIÓN PROPUESTA |
|---|---------|-----|---------------------|-----------------|
| ✓ | dinero | 149 | Usado genéricamente. "tenía mucho dinero..." | **resuelto**: `dinero → plata` por defecto; MANTENER solo en terrorismo/compuestos lexicalizados/jerga técnica extranjera/donación institucional. Regla revisada por hablante nativo RP, mayo 2026. |
| ✓ | escuela | 115 | "fue a la escuela..." | **mantener**: "escuela" es natural en RP y más frecuente que "colegio" en corpus AR (1,645 vs 903). Usar "colegio" solo cuando el contexto indique secundaria explícitamente (raro en XNLI). |
| ☐ | he | 113 | PPC auxiliar. "he dicho / he ido..." | **resuelto**: regla PPC ya en prompt (cambiar si coloquial + acción puntual) |
| ✓ | eh | 93 | Muletilla / marcador discursivo. "¿eh? / pero eh..." | **resuelto**: MANTENER. "Eh" como muletilla de hesitación es idéntico en RP y en español neutro. Verificado en 15 ejemplos XNLI, todos usan "eh" exactamente como lo usaríamos en RP. Cero cambios. |
| ✓ | oh | 90 | Interjección anglicismo en transcripciones de habla. "Oh, pasé buena parte..." | **resuelto**: regla contextual `oh → ah/uy/ay Dios/etc` agregada al prompt. |
| ☐ | hemos | 70 | PPC primera persona plural. "hemos dicho / hemos ido..." | **resuelto**: regla PPC ya en prompt |
| ✓ | habían | 70 | Pluscuamperfecto. "habían dicho..." | **resuelto**: MAYORITARIAMENTE MANTENER (pluscuamperfecto idéntico en RP). Excepción: caso "habían piratas/algo" (haber existencial impersonal) → corregir a "había" como tipo D. D2 ya cubre el caso, no requiere nueva regla. |
| ✓ | millas | 65 (50 plural + 15 singular) | Unidad imperial. "a cinco millas de distancia..." | **resuelto**: `millas → kilómetros` con conversión numérica real. MANTENER en contexto náutico/marítimo. |
| ✓ | ti | 47 | Pronombre tónico. "a ti te dije..." | **resuelto**: regla `ti → vos` en voseo (sección A). |
| ✓ | señoría | 45 | Título nobiliario inglés (His Lordship) en Captain Blood. "su señoría ordenó..." | **resuelto**: MANTENER. Cubierto por caveat de voseo arcaico. |
| ☐ | eres | 43 | Forma tuteo "tú eres". "¿tú eres...?" | **resuelto**: regla C voseo → "sos" |
| ☐ | españoles | 26 | Gentilicio. "los españoles dijeron..." | mantener (referente geográfico correcto) |
| ☐ | rey | 47 | Título o apellido. "el rey ordenó..." | mantener (referente real o título histórico) |
| ✓ | tonto | 29 | Adjetivo/insulto. "eres un tonto..." | **resuelto**: regla contextual `tonto → boludo/tarado/iluso` agregada al prompt. |
| ✓ | niño | 35 | Sustantivo. "el niño jugó..." | **mantener** por defecto. En coloquial/familiar puede ir nene/nena o chico/a. En la duda, mantener. |
| ✓ | pronto | 27 | Adverbio temporal. "lo hará pronto..." | **resuelto**: MANTENER por defecto. |
| ✓ | bote | 28 | "bote de basura" (ES) vs "tacho" (RP). "tiró en el bote..." | **resuelto**: embarcación chica → mantener "bote"; "bote de basura" → "tacho de basura". |
| ☐ | cabo | 27 | Grado militar o topónimo. "el cabo dijo..." | mantener (grado militar = igual en RP) |
| ✓ | mmm | 60 | Muletilla reflexiva. "mmm, no sé..." | **resuelto**: MANTENER, idéntico en RP. |
| ✓ | uh / hum / um | 54+24+15 | Muletillas de hesitación anglófonas. "hum, no sé..." | **resuelto**: `uh/hum/um → este.../mmm/emm`; "uh-huh" → "ajá". |
| ☐ | chica | 29 | Sustantivo / adjetivo femenino. "la chica dijo..." | **resuelto**: `joven/jóvenes → chico/a` ya en prompt; "chica" como sustantivo directo ya es RP |
| ☐ | tío | 28 | Familiar o coloquial. "mi tío / oye tío..." | **resuelto**: regla `tío→che/tipo` ya agregada en Fase 1d |

## 8.3 Medio Oriente / geopolítica / 9-11

| ☐ | PALABRA | CNT | CONTEXTO / EJEMPLOS | ACCIÓN PROPUESTA |
|---|---------|-----|---------------------|-----------------|
| ☐ | qaeda | 92 | Organización terrorista. "Al-Qaeda planeó..." | mantener (nombre propio de organización) |
| ☐ | fbi | 72 | Sigla agencia norteamericana. | mantener (sigla institución extranjera) |
| ☐ | cia | 50 | Sigla agencia norteamericana. | mantener (sigla institución extranjera) |
| ☐ | clinton | 55 | Figura política (Bill/Hillary Clinton). | mantener (persona pública real) |
| ☐ | bin | 48 | Parte del nombre "Bin Laden". | mantener (nombre propio) |
| ☐ | hazmi | 45 | Nawaf al-Hazmi, secuestrador 9/11. | mantener (persona real histórica) |
| ☐ | laden | 26 | Osama bin Laden. | mantener (persona real histórica) |
| ☐ | ksm | 73 | Khalid Sheikh Mohammed (KSM). Sigla en inglés. | mantener (sigla persona real) |
| ☐ | yousef | 19 | Ramzi Yousef, terrorista WTC 1993. | mantener (persona real histórica) |
| ☐ | terrorismo | 39 | Sustantivo. "el terrorismo en EEUU..." | mantener (término técnico igual en RP) |
| ☐ | mihdar | 61 | Khalid al-Mihdhar, secuestrador 9/11. | mantener (persona real histórica) |

## 8.4 Otras

| ☐ | PALABRA | CNT | CONTEXTO / EJEMPLOS | ACCIÓN PROPUESTA |
|---|---------|-----|---------------------|-----------------|
| ☐ | mundo | 135 | Sustantivo genérico. "en todo el mundo..." | mantener (igual en RP) |
| ☐ | estadounidenses | 54 | Gentilicio. "los estadounidenses..." | mantener (gentilicio correcto) |
| ☐ | federales | 53 | Policía federal o adjetivo. "los federales llegaron..." | mantener (igual en RP; "federales" es habitual en RP coloquial) |
| ☐ | postal | 36 | Adjetivo o sustantivo. "servicio postal / una postal..." | mantener (igual en RP) |
| ☐ | méxico | 29 | Topónimo. | mantener (topónimo) |
| ☐ | europa | 25 | Topónimo. | mantener (topónimo) |
| ☐ | francia | 30 | Topónimo. | mantener (topónimo) |
| ☐ | pákistan | 33 | Topónimo con tilde inusual. "en Pákistan..." | **revisar**: forma estándar en RP es "Pakistán" — posible error tipográfico tipo D |
| ☐ | pakistan | — | Variante sin tilde. | igual que arriba — normalizar ortografía |
| ☐ | newsweek | 24 | Ver cat. 8.1 | (duplicado, ver arriba) |

## 9. Traducción del train set MultiNLI ES → RP (pendiente decisión con tutor)

**Contexto.** HuggingFace tiene `load_dataset("xnli", "es", split="train")` con ~392k instancias del MultiNLI traducidas al español por traductores profesionales (LILT, EN→ES con post-edición humana). Es el único train set disponible para XNLI ES — no hay datos de entrenamiento NLI nativos en RP.

**Por qué importa.** Para las 4 condiciones experimentales (ES→ES, ES→RP, RP→RP, RP→ES) las condiciones RP→RP y RP→ES necesitan instancias de entrenamiento en RP. Eso requiere traducir K instancias del train ES → RP con el pipeline.

**Dos niveles de ambición:**

- **Nivel tesis (mínimo necesario):** 5k instancias bien traducidas con Gemini + Sonnet validation son más que suficientes para K=200/500/1000. Un día de pipeline.
- **Nivel contribución (discutir con tutor):** Traducir el full 392k crearía el corpus de entrenamiento NLI en RP más grande existente — comparable a AmericasNLI. Costo estimado ~$45 con Gemini Batch API + Haiku para validación automática.

**Consideración metodológica.** El train ES ya tiene translationese EN→ES de la traducción original. Agregar ES→RP crea un doble layer. Para entrenamiento es aceptable (los modelos son robustos al ruido), pero vale mencionarlo como limitación y como argumento adicional de por qué los resultados RP→RP probablemente subestiman el potencial de datos RP nativos.

**Estrategia de validación propuesta.** Gemini Batch traduce todo → Haiku valida todo automáticamente → Sonnet valida muestra estratificada del 5% para reportar calidad en la tesis.

☐ **Decisión pendiente con tutor**: ¿cuántas instancias traducir (5k vs 392k)?

> **Nota de trabajo:** las palabras marcadas como "resuelto" o "mantener" pueden cerrarse rápidamente (cambiar ☐ a ✓). Las que dicen "revisar" necesitan ver 2-3 ejemplos del XNLI antes de decidir. Usar `scripts/_lookup_pendientes.py` para extraer ejemplos de cualquier palabra.
