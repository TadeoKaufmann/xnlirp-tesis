# CLAUDE.md

## 1. Descripción del proyecto

Tesis de Maestría sobre benchmarking NLU en español rioplatense (RP) con augmentación guiada por eye-tracking. Componente actual: construir **XNLIrp** adaptando dialectalmente XNLI ES → RP usando Gemini 2.5 Flash como borrador + revisión nativa. Hipótesis: la distancia dialectal entre el corpus ET rioplatense y el benchmark afecta el rendimiento NLU; la augmentación ET ayuda especialmente en low-resource (K=200/500/1000).

## 2. Estructura de carpetas

```
Datasets-Codigo/
├── .env                                   # GOOGLE_API_KEY (Tier 1, billing activo)
├── .venv/                                 # venv local (Windows: .venv\Scripts\activate)
├── PROJECT.md                             # contexto académico, papers clave, hipótesis
├── CLAUDE.md                              # este archivo
├── requirements.txt
├── credentials/                           # service accounts (no tocar)
├── data/
│   ├── raw/xnli/
│   │   ├── xnli_pilot_500.jsonl           # 500 instancias estratificadas seed 42 — INMUTABLE
│   │   └── xnli_full_7500.jsonl           # 7500 instancias completas (5010 test + 2490 val)
│   └── processed/
│       ├── xnli_pilot_30_annotated.jsonl  # GOLD 30 (few-shots + referencia, leakage conocido)
│       ├── xnli_pilot_30_review.csv       # export para revisión
│       ├── xnli_held_out_70_raw.jsonl     # DEV SET 70 (posiciones 30-99 del 500), anotado por Opus
│       ├── xnli_held_out_70_raw.html      # vista lado a lado
│       ├── xnli_held_out_100_raw.jsonl    # DEV SET 100 (posiciones 100-199 del 500), anotado por Opus
│       ├── xnli_held_out_100_raw.html     # vista lado a lado
│       ├── xnli_combined_dev_200.jsonl    # UNIÓN gold30 + held70 + held100 (200 inst) para run y eval único
│       ├── xnli_error_cases_15.jsonl      # 15 casos problemáticos conocidos (referencia)
│       ├── cultural_adaptations.jsonl     # 394 instancias con clusters culturales adaptadas por Opus (mayo 2026)
│       ├── qa_stories_dataset.jsonl       # Dataset QA sobre cuentos RP (en construcción)
│       ├── qa_stories_{train,dev,test}.jsonl  # Splits del QA dataset
│       └── eval_xnli_pilot_30_annotated.md
├── notebooks/                             # exploración manual
├── validation_app/                        # encuesta web standalone para validación nativa
│   └── index.html                         # single-page app (Supabase + vanilla JS), deploy a Netlify desde esta subcarpeta
├── scripts/
│   ├── check_env.py                       # verifica .env y credenciales
│   ├── translate_xnli_pilot.py            # harness principal: modelo × T × variante prompt
│   ├── evaluate_against_gold.py           # type accuracy + Lev delta vs cualquier gold
│   ├── validate_translations.py           # validador independiente del gold (regex)
│   ├── visualize_comparison.py            # genera HTML lado a lado
│   ├── optimize_prompt_loop.py            # meta-loop automático (no usar en este flujo)
│   ├── _annotate_held_out_70.py           # script que generó el held-out 70
│   ├── _annotate_held_out_100.py          # script que generó el held-out 100
│   ├── _ejemplos_xnli.txt                 # ejemplos anotados de decisiones por palabra/caso (referencia)
│   ├── _extract_cluster.py                # extrae instancias por cluster cultural del XNLI full
│   ├── generate_qa_dataset.py             # genera QA dataset desde textos RP
│   ├── validate_qa_dataset.py             # valida QA dataset generado
│   ├── analisis_peninsulares_xnli.py      # análisis de peninsularismos en XNLI full
│   ├── analisis_vocab_xnli.py             # análisis de vocabulario XNLI
│   ├── add_english_to_xnli_full.py        # agrega EN a instancias del XNLI full
│   ├── download_xnli_full.py              # descarga XNLI full desde HuggingFace
│   ├── sample_xnli_1000.py               # muestrea N instancias del XNLI full
│   └── prompts/
│       ├── prompt_v1_minimal.txt           # dialectal puro (A/B/C/D); base de comparación
│       ├── prompt_v2_cultural_inline.txt   # v1 + adaptación cultural conservadora (tipo E)
│       ├── prompt_opus_cultural.txt        # v2 + E.4 transposición de clusters culturales (para Opus)
│       └── _archive/
│           └── prompt_v2_with_cultural_candidates_LEGACY_marker_only.txt  # v2 viejo (solo marcaba); reemplazado en mayo 2026
└── results/
    ├── review_queue.jsonl
    ├── validation_report_xnli_pilot_30_annotated.md
    └── experiments/
        ├── experiments_summary.json
        ├── <config_label>.jsonl           # outputs por config (held70__... o gemini-...)
        ├── failed_<config_label>.jsonl
        ├── report_<config_label>.md       # reporte de tipos+Lev por corrida
        └── eval_<config_label>.md         # evaluación vs gold (type acc + confusion matrix)
```

## 3. Decisiones metodológicas fijas (NO rediscutir)

### 3.1 Tipología A/B/C/D (asignar exactamente UNA letra)

- **A — Sin cambios.** La instancia funciona igual en ES y RP. `changes` debe ser `[]`.
  *Ej:* "Les dije que era de mi hermana" → idéntico en RP.

- **B — Cambios léxicos peninsulares** (incluye PPC → pretérito simple cuando aplica).
  *Ej idx 1638:* "no he hecho nada" → "no hice nada"; "he recibido" → "recibí".
  *Ej idx 1522:* "no tenía un duro" → "no tenía un mango".

- **C — Morfosintaxis rioplatense** (voseo, vosotros/os → ustedes/se, eliminación de pronombres sujeto redundantes).
  *Ej idx 910:* "ha sido un placer hablar contigo" → "fue un placer hablar con vos" (voseo dominante; PPC va como secondary).
  *Ej idx 1534:* "os lo diré" → "se lo diré" (vosotros → ustedes).

- **D — Corrección de errores de traducción** del ES respecto del EN.
  *Ej idx 2821:* "defensores" (de *defendants*) → "demandados".
  *Ej idx 3440:* "guia" → "guía" (typo, tilde faltante).
  *Ej idx 1942:* "Shrewd" sin traducir → "Astuta".

Si una instancia tiene B+C, asignar la letra del cambio dominante (la que domine el conteo de cambios) y registrar el otro en `secondary_features`.

### 3.2 Lista B completa de sustituciones obligatorias

**Léxico — sustitución directa:**
- aquí → acá *(obligatorio en TODOS los registros: narrativa, diálogo, descriptivo, turístico, académico, periodístico, formal, coloquial. "Acá" es la forma rioplatense estándar. Conservar mayúscula inicial: "Aquí" → "Acá". Cada ocurrencia se registra como un cambio léxico tipo B.)*
- allí → ahí *(paralelo a aquí→acá: "Acá/ahí/allá" es la triada RP estándar. "Allí" → "ahí" para referente contextual identificado; "allí" → "allá" para referente distante/abstracto. Excepción: registro decimonónico/literario explícito puede mantener "allí". Conservar mayúscula. Cada ocurrencia es un cambio B.)*
- coche → auto
- autobús → traducción contextual *(no hay palabra única en RP): urbano de línea → "colectivo"; escolar → "combi escolar" o "transporte escolar"; larga distancia/interurbano → "micro" u "ómnibus". Default si no se especifica: "colectivo".*
- piso (=apartamento) → departamento
- coger → agarrar/tomar
- ordenador → computadora
- móvil → celular
- conducir → manejar
- enfadado → enojado
- vestíbulo → hall
- americana (=EEUU) → norteamericana
- coste → costo
- no tenía un duro → no tenía un mango
- ello → eso *(pronombre neutro: "por ello" → "por eso", "con todo ello" → "con todo eso". Mantener solo en registro jurídico-institucional explícito.)*
- bachillerato → secundario *(nivel educativo medio en sistema AR/UY. Mantener si es orientación de plan de estudios o sistema educativo extranjero referido como tal.)*
- repleto/a → lleno/a *("Lleno" es la forma neutral en RP; "repleto" suena literario/peninsular. Mantener solo en registro literario explícito o si el matiz "hasta el tope" es relevante.)*
- joven/jóvenes → chico/a o adolescente *(sustantivo o adjetivo de personas en contexto informal: "los jóvenes de la zona" → "los chicos de la zona", "niños y jóvenes" → "niños y adolescentes". Para animales: diminutivo afectivo ("perro joven" → "perrito") o "cachorro" para perros. MANTENER como adjetivo en contexto narrativo/emocional ("eran tan jóvenes cuando pasó") y en registro académico/estadístico/formal. Regla emergente de validación nativa batch 200-260; escrita por Claude Sonnet 4.6, revisada por Claude Opus 4.7.)*

**Léxico — sustitución contextual (no mecánica, solo cuando se cumple la condición de uso):**
- padre/madre → papá/mamá *(solo en registro coloquial/familiar 1ª persona referido a propios padres del hablante: "casa de mi padre" → "casa de mi papá". MANTENER en registro formal/literario, referente terceros, plural genérico, usos no familiares.)*
- recoger → reemplazar siempre según sentido *(en RP "recoger" no es natural en ningún contexto: "del piso" → levantar; "juntar/recopilar" → juntar/cosechar; "pasar a buscar" → pasar a buscar/ir a buscar; expresiones figuradas → alternativa RP más natural.)*
- enviar → mandar *(preferir "mandar" en registro coloquial o agente impersonal. MANTENER "enviar" en registro formal/escrito.)*
- recordar X → acordarse de X *(coloquial 1ª persona: "recuerdo a mis abuelos" → "me acuerdo de mis abuelos". MANTENER en registro formal/literario, sentido transitivo "hacer recordar" e imperativos institucionales.)*
- pequeño/a → chico/a *(por defecto en casi todos los contextos. Evidencia: corpus AR muestra "chico/a" ~16x más frecuente que "pequeño/a" (3,360 vs 205 en 30k artículos de medios argentinos), tanto para tamaño físico como para edad y sentidos figurados. Tamaño físico: "una mesa pequeña" → "una mesa chica", "un país pequeño" → "un país chico". Comparativo: "el más pequeño" → "el más chico". Edad standalone: preferir diminutivo del sustantivo ("mi hijita", "el perrito") o agregar "más" ("mi hija más chica"); "mi hija chica" solo suena raro. Cantidad/abstracto: "una pequeña diferencia" → "una diferencia chica". MANTENER "pequeño/a" solo en: (a) registro literario/formal explícito; (b) compuestos lexicalizados ("pequeña y mediana empresa"/"PyME", "pequeño productor"); (c) matiz de "ínfimo/insignificante" donde "chico" lo neutralizaría. En la duda, cambiar a chico. Regla revisada mayo 2026 tras análisis de corpus AR.)*
- uh / hum / um → este.../mmm/emm *(muletillas de hesitación anglófonas, no naturales en RP. Reemplazar por "este...", "mmm" o "emm" según ritmo; si ya hay "eh" en la oración, preferir "este..." para no duplicar. "uh-huh" → "ajá" o "sí, sí" (huh solo aparece en ese compuesto en XNLI). 54+24+15=93 ocurrencias XNLI.)*
- arrojar → tirar *(en RP coloquial "arrojar" no se usa: "la gente nunca arroja dinero" → "la gente nunca tira dinero". 4 ocurrencias XNLI.)*
- vale → dale/bueno *(afirmación/acuerdo en registro coloquial: "vale, nos vemos" → "dale, nos vemos"; "vale, entendido" → "bueno, entendido"; "¿vale?" → "¿dale?" / "¿sí?". MANTENER cuando es verbo "valer" conjugado ("no vale mentir", "¿cuánto vale?"), nombre propio, o registro formal escrito. En la duda, cambiar. — **Pendiente revisión Opus.** EsPal latinoamericana: `bueno` 924k vs `vale` 212k, ratio 4.4x. Agregado mayo 2026 a partir de análisis de frecuencias EsPal sobre corpus Cuentos/Fermín.)*
- carretera → ruta *(vía interurbana/rural. En RP "carretera" no se usa: "por la carretera" → "por la ruta". Usar "autopista" si hay acceso controlado/peaje. NUNCA reemplazar por "calle" o "avenida". 16 ocurrencias en XNLI full. **Pendiente revisión Opus.**)*
- jersey → buzo *(prenda de punto/abrigo informal. "llevaba un jersey" → "llevaba un buzo"; si es tejido/pulóver formal, preferir "pulóver". 10 ocurrencias en XNLI full. **Pendiente revisión Opus.**)*
- tío → che/tipo según uso *(MANTENER cuando es pariente ("mi tío", "la casa de tu tío"). Vocativo coloquial peninsular ("¿ves, tío?") → "che" o eliminar. Referencia de género ("todo el mundo la trata como un tío") → "tipo"/"hombre". En la duda, mantener. 28 ocurrencias XNLI: ~21 familiares, ~7 coloquiales/género. **Pendiente revisión Opus.**)*
- dinero → plata *(por defecto en casi todos los contextos. Cuidar concordancia de género: "mucho dinero" → "mucha plata", "ese dinero" → "esa plata", "el dinero" → "la plata". MANTENER "dinero" solo cuando genuinamente suena mal en RP: (a) contextos de violencia o terrorismo organizado ("Al Qaeda recaudaba dinero", "los talibanes querían dinero y armas") — "plata" resulta inapropiado en esos registros; (b) transferencias financieras con jerga muy técnica o extranjera ("el hawaladar recibiría el dinero en rupias"); (c) compuestos lexicalizados: "lavado de dinero", "blanqueo de dinero", "ruta del dinero", "desvío de dinero"; (d) donación formal explícita como acto institucional ("dar dinero a la campaña"). Usar "fondos" cuando una organización o agencia recauda, asigna o administra fondos presupuestarios. En la duda, cambiar a plata. Evidencia: validación nativa RP sobre 20 instancias XNLI (mayo 2026) + corpus comentarios AR (plata:dinero 2.4x). 149 ocurrencias XNLI. Regla revisada por hablante nativo RP, mayo 2026.)*

**Reglas pendientes — no agregar al prompt hasta tener N≥3 casos del corpus:**
- **diminutivo -ito/-ita** *(regla general diferida)*: en RP coloquial, cuando un sustantivo refiere a algo pequeño en tamaño o joven en edad, se prefiere el diminutivo lexicalizado del sustantivo por sobre la construcción adjetivo+sustantivo ("gato pequeño → gatito", "casa pequeña → casita"). No se agrega ahora porque XNLI tiene registro predominantemente formal y agregar diminutivos generativamente introduciría ruido en instancias que no lo requieren. Si en futuras rondas de validación nativa aparecen N≥3 casos donde el -ito resuelve un "parcialmente/no" que ninguna regla B vigente cubre, agregar al prompt como regla contextual acotada a sustantivos domésticos/familiares en registro coloquial. — *Claude Sonnet 4.6*

**Contextuales (no reemplazo mecánico):**
- **tonto/a/s** → traducción contextual *("tonto" suena formal/suave en RP, cambiar por defecto):
  - insulto vocativo/predicativo a persona ("eres un tonto", "sos tan tonto", "es la verdad, tonto") → **boludo/a** (neutro coloquial) o **tarado/a** (más fuerte); **iluso/a** si la nota es ingenuidad sin agresión ("fue un tonto al creer en Santa Claus" → "fue un iluso al creer...")
  - adjetivo de cosa abstracta (idea, gasto, palabras, juegos, escepticismo) → **boludo/a** ("una idea tonta" → "una idea boluda", "palabras tontas" → "palabras boludas")
  - "hacerse el tonto" → "hacerse el boludo" (locución fija RP de "fingir desconocimiento / no darse por enterado"). "Hacerse el gil" NO sirve: significa "actuar como tonto", no "fingir que no se sabe"
  - predicativo impersonal ("parece tonto separar X") → "parece boludo separar X" o "es al pedo separar X"
  - MANTENER en: (a) narrativa literaria pura (no diálogo): "el tonto quijotesco corre hacia el peligro"; (b) compuestos lexicalizados ("el tonto del pueblo"); (c) registro académico/formal escrito. En obras con diálogos transcriptos (Captain Blood), el diálogo SÍ cambia, solo la voz narrativa mantiene.)*
- **oye** → traducción contextual:
  - vocativo: "oye tío" → "che flaco/pibe/amigo"
  - indignación/sorpresa: "pero oye" → "pero che"
  - transición suave: "oye, fueron" → "bueno, fueron"
- **oh** → traducción contextual *(en RP "oh" suena extranjero/literario; 90 ocurrencias XNLI, mayoría diálogo transcripto):
  - apertura suave de turno: "oh, pasé buena parte..." / "oh, chico, acá tenés..." → "ah" o "uy"; o eliminar si queda redundante
  - afirmación/reconocimiento: "oh, sí" / "oh claro" / "oh, ya veo" → "ah, sí" / "ah, claro" / "ah, ya veo"
  - sorpresa con Dios: "oh Dios" → "ay Dios" o "Dios mío"
  - doblada: "oh, oh" → "uy, uy" o "ay, ay"
  - MANTENER solo en registro literario explícito ("¡Oh, qué desdicha!") o nombre propio.)*
- **esto...** (muletilla) → "eso..." o "este..."

**PPC → pretérito simple RP** (regla con excepción crítica):
SOLO cambiar cuando se cumplen las **dos** condiciones:
1. Registro coloquial/conversacional, **Y**
2. Acción puntual concluida sin relevancia presente.

Ejemplos que **SÍ** cambian: "he hecho → hice", "ha sido → fue", "hemos añadido → añadimos", "has dicho → dijiste", "has leído → leíste".

**MANTENER el PPC** (no cambiar) cuando:
- Estado resultante vigente o relevancia presente:
  - **"se ha convertido en X"** (estado vigente, sigue siendo X hoy) → **NO cambiar** a "se convirtió".
  - **"no ha tenido en cuenta X"** (crítica académica, sigue sin considerarlo) → **NO cambiar** a "no tuvo en cuenta".
  - **Criterio rector:** si el resultado sigue vigente hoy, mantener PPC. Cambiar el aspecto puede alterar la relación lógica premisa-hipótesis.
- Registro formal, académico o literario.
- Valor experiencial o habitual ("nunca he visto", "siempre he creído").

> **Excepción crítica del PPC (recordar siempre):**
> "se ha convertido" (estado vigente) **NO** cambia.
> "se convirtió" (acción puntual pasada concluida) **SÍ** cambia.
> El criterio es si el resultado sigue vigente hoy.

### 3.3 Principio de cambio mínimo

Solo cambiar lo necesario. Si una oración ya funciona en rioplatense estándar, **no modificarla**. La adaptación es dialectal, no estilística. No reescribir, no mejorar redacción, no buscar consistencia léxica entre prem y hyp (si el ES tiene "flujo" en prem y "crecida" en hyp, ambos quedan tal cual).

### 3.4 Label NLI invariante

La etiqueta `entailment | neutral | contradiction` **nunca puede cambiar**. Si una adaptación posible podría alterar la relación lógica, no se aplica. Esto incluye conservar el aspecto verbal (PPC vs pretérito simple) cuando ese aspecto es lo que sostiene la relación.

### 3.5 Levenshtein siempre por Python, nunca por el modelo

`lev_prem`, `lev_hyp`, `lev_total` se calculan con `python-Levenshtein` en `normalize_response()` de `translate_xnli_pilot.py`. El modelo no estima distancias.

### 3.6 Adaptación cultural — Fase 2 conservadora (tipo E)

A partir de mayo 2026, el prompt v2 (`prompt_v2_cultural_inline.txt`) habilita **adaptación cultural inline** sobre un subconjunto cerrado de referentes. Esto es excepción controlada a la Restricción 2 ("no modificar nombres propios"), válida SOLO para v2 y SOLO en estas dos categorías:

- **E.1 Nombres anglo de persona — regla escalable, NO tabla fija.** DEFAULT: adaptar a un nombre RP plausible del mismo género, registro y juego lingüístico. EXCEPCIONES (no adaptar): (1) figura histórica/celebridad/persona pública real; (2) personaje universalmente reconocible (Sherlock, Hamlet, Don Quijote); (3) autor citado dentro del texto; (4) antropónimo nominado en contexto jurídico-institucional con apellido específico; (5) nombre que es parte de un juego semántico que no se puede preservar en RP. Si el nombre es de ficción puntual no canónica (ej. Ogle), SÍ se adapta. Si forma parte de un juego de género/apócope (ej. Sam/Samantha), se adapta a un par RP que preserve el juego (ej. Valen/Valentina). El prompt incluye sugerencias heurísticas pero ningún mapeo es obligatorio: dos anotadores pueden elegir equivalentes distintos y ambas adaptaciones son válidas si respetan género/registro/consistencia prem-hyp.
- **E.2 Festividades/referentes universales con equivalente directo**: Santa Claus / Father Christmas → Papá Noel; Easter Bunny → conejo de Pascua. NO incluye Halloween, Thanksgiving, 4th of July, Super Bowl ni feriados nacionales específicos.

**Restricción 6 (consistencia cultural):** si una adaptación E.1/E.2 se aplica y el referente aparece en prem y hyp, debe usarse la MISMA equivalencia en ambos. Esta es la única excepción a la Restricción 5 (no buscar consistencia léxica), y solo cubre el referente cultural adaptado.

- **E.3 Transposición narrativa Captain Blood → Bouchard (mayo 2026, agregado en v2):** el corpus XNLI tiene un subconjunto extenso de Captain Blood (Sabatini), corsario inglés siglo XVII en el Caribe. En v2 se transpone a su equivalente histórico AR: **Hipólito Bouchard**, corsario de la independencia argentina (siglo XIX) que comandó la fragata "La Argentina". Mapeo obligatorio: Peter Blood→Hipólito Bouchard; Lord Julian Wade→San Martín; Bishop→Rodríguez; Wolverstone→López; Ogle→González; Wade (solo)→Fernández; Calverley→Calderón; Arabella (fragata)→La Argentina; Royal Mary (barco pasajeros)→La Heroína; Blue Teacup (barco menor)→El Mate; Jamaica→Buenos Aires; Port Royal→Buenos Aires; Gobernador de Jamaica→Gobernador de Buenos Aires; "su señoría"→"mi General"/"Su Excelencia"; "Lord" genérico→"Don"/"General"/"Comandante". Su Majestad se MANTIENE (Bouchard pre-1816, rey español todavía válido). CRÍTICO: al desaparecer los marcadores ingleses ("su señoría", "Lord"), el caveat de voseo arcaico SE DESACTIVA y el voseo aplica normalmente (Bouchard/San Martín son XIX, voseo ya consolidado). Aplicar consistentemente prem y hyp. NO incluye millas (mantener náuticas para barcos). Esta es la **única** transposición narrativa completa en v2, justificada por (a) volumen del subcorpus, (b) paralelo histórico exacto, (c) preserva identidad referencial.

**Quedan FUERA de E (van a `cultural_candidates`, no se modifican inline)**: topónimos extranjeros (Texas, Del Rio, Dam Square), marcas comerciales (Texas Instruments), unidades imperiales (millas, pies), eventos históricos específicos, instituciones extranjeras. Estos los decidimos en Fase 3 humano-en-el-loop.

**Tipo E en la tipología:** se asigna E cuando el cambio cultural es el ÚNICO cambio. Si concurre con B/C/D dialectal, la letra dominante es la dialectal y la cultural va en `secondary_features` ("adaptacion_cultural_E1: Joe → José"). Esto preserva la métrica B/C/D existente y suma E como categoría adicional medible.

## 4. Estado actual

- **Gold 30** (`xnli_pilot_30_annotated.jsonl`): few-shots + referencia. **Leakage conocido** porque los 3 few-shots del prompt (idx 1638, 910, 2821) están dentro del gold; usar gold solo como sanity check, no como benchmark de generalización. **idx 1522 actualizado** (mayo 2026): se agregó cambio B `así lo creí → así creí` (eliminación de clítico anafórico) en `prem_rp`.
- **Held-out 70** (`xnli_held_out_70_raw.jsonl`): dev set anotado manualmente (Opus 4.7) sobre las posiciones 30-99 del pilot 500. Usar para optimizar el prompt sin contaminación.
- **Held-out 100** (`xnli_held_out_100_raw.jsonl`): dev set adicional anotado manualmente (Opus 4.7) sobre las posiciones 100-199 del pilot 500. Distribución actual: **A 72 / B 6 / C 13 / D 9** (post correcciones de gold idx 22, 1543, 1731, 4490 → A→D).
- **Combined dev 200** (`xnli_combined_dev_200.jsonl`): unión de los tres dev sets en un solo archivo, sin duplicados. Distribución total: **A 139 / B 19 / C 23 / D 19** (idx 3121 corregido A→B en mayo 2026). Cada fila lleva `source_set` ∈ {`gold30`, `held70`, `held100`}. Pensado para una sola corrida + eval únicos.
- **Test set**: pendiente, anotar al final (posiciones 200+ del pilot 500).
- **Prompt v1** actualizado en mayo 2026 con cuatro cambios:
  1. **D4 con caveat de Restricción 5**: D4 solo aplica cuando una traducción es claramente incorrecta; si ambas son sinónimos válidos, es A. Ejemplo nuevo `médico/doctor`.
  2. **`pues` con mapeo contextual**: 4 contextos (muletilla / causal / consecutivo / cierre) en lugar de reemplazo mecánico.
  3. **Caveat corto de registro arcaico para voseo**: si hay marcas de registro decimonónico/aristocrático (ej. "su señoría"), no aplicar voseo.
  4. **Regla acotada de eliminación de clítico anafórico**: `lo`/`la` se elimina solo cuando es redundante tras adverbio anafórico (`así`, `eso`); ejemplo único `así lo creí → así creí`.
- **Prompt v1 — Fase 1 (mayo 2026, post validación nativa batch 200-260):** ampliación del léxico B con seis sustituciones contextuales adicionales surgidas del feedback nativo:
  - `allí → ahí/allá` (paralelo a aquí→acá, contextual).
  - `padre/madre → papá/mamá` (registro coloquial 1ª persona, propios padres).
  - `recoger → reemplazar siempre según sentido` (levantar/juntar/cosechar/pasar a buscar según contexto; "recoger" no es natural en RP en ningún uso).
  - `enviar → mandar` (registro coloquial / agente impersonal).
  - `recordar X → acordarse de X` (coloquial 1ª persona, requiere ajuste de preposición).
  - `pequeño/a → chico/a` (edad informal de persona/animal).
- **Prompt v1 — Fase 1b (mayo 2026, post análisis 60 anotaciones nativas):** cuatro reglas léxicas B adicionales emergentes del feedback (alta confianza, sin riesgo NLI):
  - ~~`chaqueta → campera`~~ (eliminada mayo 2026: 0 ocurrencias en XNLI full 7.5k, sin impacto práctico).
  - `ello → eso` (pronombre neutro en registro no estrictamente formal).
  - `bachillerato → secundario` (nivel educativo medio en AR/UY; mantener para orientación específica del plan de estudios o sistema extranjero referido como tal).
  - `repleto/a → lleno/a` (forma neutral RP; mantener solo en registro literario explícito).
  - v2 hereda estas cuatro reglas. v2 además aclara que **Acción de Gracias / Thanksgiving** no se adapta inline (no hay equivalente 1:1 en RP) y se MARCA en `cultural_candidates` con `category="evento_historico_especifico"` y `suggestion=null` para Fase 3.
- **Prompt v1 — Fase 1c (mayo 2026, post análisis 60 anotaciones nativas — continuación):** una regla léxica B adicional emergente del feedback (alta confianza):
  - `joven/jóvenes → chico/a o adolescente` (sustantivo de personas en contexto informal; diminutivo/cachorro para animales; mantener como adjetivo emocional/narrativo o en registro académico). *Regla escrita por Claude Sonnet 4.6, revisada por Claude Opus 4.7.*
  - v2 hereda esta regla.
- **Prompt v1/v2 — Fase 1d (mayo 2026, análisis EsPal/corpus Cuentos + frecuencias XNLI full 7.5k):** cuatro reglas nuevas surgidas de análisis cuantitativo. Todas pendientes revisión Opus:
  - `vale → dale/bueno` (27 ocurrencias XNLI, EsPal ratio 4.4x).
  - `carretera → ruta/autopista` (16 ocurrencias XNLI; "autopista" si acceso controlado; nunca "calle"/"avenida").
  - `jersey → buzo/pulóver` (10 ocurrencias XNLI).
  - `tío → che/tipo según uso` (28 ocurrencias XNLI; mantener si es familiar; "che" si vocativo coloquial; "tipo/hombre" si referencia de género).
  - *Reglas escritas por Claude Sonnet 4.6.* **Todas pendientes revisión Opus.**
  - v1 y v2 incluyen estas reglas con tag `[Pendiente revisión Opus]`.
  - Dataset descargado: `data/raw/xnli/xnli_full_7500.jsonl` (5010 test + 2490 val, balanceado 2500/label).
- **Prompt v1/v2 — `dinero → plata` revisado (mayo 2026, validación nativa RP):** la regla original (plata solo en registro coloquial/personal) fue invertida tras validación directa con hablante nativo RP sobre 20 instancias XNLI. Plata pasa a ser el **default** en casi todos los contextos; dinero se mantiene solo cuando genuinamente suena mal en RP: (a) terrorismo/violencia organizada ("Al Qaeda recaudaba dinero", "talibanes querían dinero y armas"); (b) jerga técnica extranjera (hawaladar, rupias); (c) compuestos lexicalizados (lavado de dinero, blanqueo de dinero, ruta del dinero); (d) donación institucional formal explícita. Fondos cuando organización recauda/asigna fondos presupuestarios. Evidencia: validación nativa + corpus comentarios AR (plata:dinero 2.4x).
- **Prompt v2 cultural inline (mayo 2026, Fase 2):** nuevo archivo `prompt_v2_cultural_inline.txt` que reemplaza al v2 viejo de "solo marcar candidatos". Hereda todo el v1 (Fase 1 incluida) y agrega sección E con adaptación cultural conservadora: tabla cerrada de nombres anglo comunes (Joe→José, Mary→María, etc.) y festividades universales (Santa Claus→Papá Noel, Easter Bunny→conejo de Pascua). Topónimos, marcas, unidades imperiales y eventos históricos se MARCAN en `cultural_candidates` pero NO se modifican (Fase 3 humano-en-el-loop). El archivo viejo está en `scripts/prompts/_archive/`.
- **Billing Gemini** activo, **Tier 1, 1000 RPM**.
- Eval **pre-cambios de prompt** (stale, hay que re-evaluar):
  - held-out 70 @ Gemini 2.5 Flash T=0.1 v1: type accuracy **94.3%** (A 95.7 / B 83.3 / C 100 / D 87.5).
  - gold 30 @ idem: type accuracy **93.3%** (A 91.3 / B 100 / C 100 / D 100).
  - held-out 100 @ idem (con gold corregido en sesión actual): type accuracy ≈ **95%** (5 errores reales).
- **Validación post-cambios sobre subsets puntuales (8 instancias diversas, mayo 2026)**: 8/8 OK. Confirmó que (a) los 4 fixes del held-out 100 funcionan, (b) el voseo contemporáneo sigue aplicando bien, (c) la regla de clítico no se sobre-aplica en controles relativos/predicativos. Falta correr full sets para confirmar ausencia de regresiones globales.
- **`validation_app/index.html`** (mayo 2026): app web standalone para validación nativa. Stack HTML + vanilla JS + Supabase JS (CDN). Tabla Supabase `respuestas` con columnas: `anotador_id`, `idx`, `respuesta` ∈ {si/parcialmente/no}, `comentario_prem`, `comentario_hyp`, `region`, `quiere_mas`. UUID anónimo en `localStorage`, distribución automática de instancias entre anotadores (filtra `idx` ya respondidos por otros), guardado incremental por `id` de fila. Las instancias se embeben como JSON literal en `INSTANCES` en el HTML; cuando se quiera cambiar el set, editar ese array. **TODO (Opus):** cuando el volumen escale a cientos o miles de instancias, migrar `INSTANCES` a una tabla Supabase `instancias` (`idx`, `prem`, `hyp`) y reemplazar el array hardcodeado por un `SELECT` al cargar la app. Insertar nuevos lotes sería un CSV upload en lugar de editar el HTML. Tarea sencilla (~30 min) pero no prioritaria mientras los lotes sean de 60. — *Claude Sonnet 4.6* **Deploy:** el repo está vinculado a Netlify vía GitHub — cualquier `git push` a `main` dispara un redeploy automático. La raíz de publicación es `validation_app/` (configurado en `validation_app/netlify.toml`, `publish = "."`). NO hacer drag & drop manual — commitear y pushear.
- **Repo Git inicializado** (mayo 2026): `git init -b main` en la raíz. `.gitignore` excluye `.env`, `credentials/`, `.venv/`, `.claude/`, `results/` y `*.jsonl` con override `!data/processed/*.jsonl` y `!data/raw/**/*.jsonl` para conservar gold/dev sets en el repo. Commit inicial incluye `validation_app/`. Remote en GitHub configurado para push completo del proyecto. Netlify vinculado al repo GitHub con base directory `validation_app/`.

## 5. Lo que NO debe hacer Claude Code nunca

- **No modificar `data/raw/`** ni los gold anotados (`xnli_pilot_30_annotated.jsonl`, `xnli_held_out_70_raw.jsonl`).
- **No modificar los 3 few-shots del prompt** (idx 1638, 910, 2821).
- **No implementar Fase 2 de adaptación cultural** (los `cultural_candidates` se marcan en Fase 1; la adaptación cultural real es decisión humana posterior).
- **No escalar a 10k** sin validación previa en held-out.
- **No buscar consistencia léxica** entre premisa e hipótesis. **Excepción única (solo v2):** consistencia obligatoria del referente cultural adaptado bajo E.1/E.2 (Restricción 6 de v2).
- **No corregir nombres propios** aunque parezcan mal transcritos (ej. "Lecretius" se queda). **Excepción controlada (solo v2):** nombres anglo comunes de persona no-célebres y no-históricos según sección E.1 del prompt v2 cultural inline (Joe → José, Mary → María, etc.). Topónimos, marcas, antropónimos únicos siguen sin tocarse.
- **No traducir directamente del inglés**; el EN es solo referencia para detectar errores tipo D.
- **No alterar `label`/`label_int`** ni la estructura JSON del output.

## 6. Comandos frecuentes

Activar venv: `.venv\Scripts\activate` (Windows). Todos los comandos asumen ejecución desde la raíz del proyecto.

```bash
# Sanity check del entorno
python scripts/check_env.py

# Correr el dev combinado de 200 (gold30 + held70 + held100) con T=0.1 y v1 — base dialectal post Fase 1
python scripts/translate_xnli_pilot.py --input data/processed/xnli_combined_dev_200.jsonl \
    --temperatures 0.1 --prompt-variants v1

# Correr el dev combinado de 200 con T=0.1 y v2 cultural inline — base post Fase 2
python scripts/translate_xnli_pilot.py --input data/processed/xnli_combined_dev_200.jsonl \
    --temperatures 0.1 --prompt-variants v2

# Evaluar contra el dev combinado (v1 — gold dialectal estándar)
python scripts/evaluate_against_gold.py \
    --gold data/processed/xnli_combined_dev_200.jsonl \
    --run results/experiments/xnli_combined_dev_200__gemini-2.5-flash__T0.1__v1.jsonl

# Evaluar v2 contra el gold cultural (cuando exista xnli_combined_dev_200_cultural.jsonl)
python scripts/evaluate_against_gold.py \
    --gold data/processed/xnli_combined_dev_200_cultural.jsonl \
    --run results/experiments/xnli_combined_dev_200__gemini-2.5-flash__T0.1__v2.jsonl

# Correr held-out 70 con T=0.1 y v1 (config principal de optimización, dev individual)
python scripts/translate_xnli_pilot.py --held-out --temperatures 0.1 --prompt-variants v1

# Correr held-out 100 con T=0.1 y v1 (segundo dev set, posiciones 100-199)
python scripts/translate_xnli_pilot.py --input data/processed/xnli_held_out_100_raw.jsonl \
    --temperatures 0.1 --prompt-variants v1

# Correr solo las 30 gold
python scripts/translate_xnli_pilot.py --limit-to-gold --temperatures 0.1 --prompt-variants v1

# Correr un input arbitrario (ej. xnli_error_cases_15.jsonl)
python scripts/translate_xnli_pilot.py --input data/processed/xnli_error_cases_15.jsonl \
    --temperatures 0.1 --prompt-variants v1

# Evaluar contra el held-out 70
python scripts/evaluate_against_gold.py \
    --gold data/processed/xnli_held_out_70_raw.jsonl \
    --run results/experiments/held70__gemini-2.5-flash__T0.1__v1.jsonl

# Evaluar contra el held-out 100
python scripts/evaluate_against_gold.py \
    --gold data/processed/xnli_held_out_100_raw.jsonl \
    --run results/experiments/<config_label>.jsonl

# Evaluar contra el gold 30 (default --gold)
python scripts/evaluate_against_gold.py \
    --run results/experiments/gemini-2.5-flash__T0.1__v1.jsonl

# Evaluar TODAS las configs (ranking global)
python scripts/evaluate_against_gold.py --summary results/experiments/experiments_summary.json

# Validador independiente (regex sobre output)
python scripts/validate_translations.py --run results/experiments/<config>.jsonl

# HTML side-by-side para revisión visual
python scripts/visualize_comparison.py --input <jsonl> --output <html>
```

**Args principales de `translate_xnli_pilot.py`:**
- `--models` (default `gemini-2.5-flash`)
- `--temperatures` (default `0.1 0.3 0.5`) — itera por todas las combinaciones
- `--prompt-variants` (default `v1 v2`) — busca `prompts/prompt_<variant>*.txt`
- `--input <path>` | `--held-out` | `--limit-to-gold` | `--skip-gold-idxs` (mutuamente excluyentes en lo aplicable)
- `--limit N` — primeras N del subset
- `--include-english` / `--no-include-english`
- `--batch-size`, `--batch-pause` — control de throughput vs rate limit

**Args de `evaluate_against_gold.py`:**
- `--run <jsonl>` | `--summary <json>`
- `--gold <jsonl>` (default gold 30)
- `--lev-threshold N` (default 10) — tolerancia para auto-aprobación

## 7. Próximos pasos

1. Loop de optimización del prompt v1 contra held-out 70 hasta maximizar type accuracy (sin tocar few-shots).
2. Validar prompt estabilizado contra gold 30 (sanity check, leakage conocido).
3. Anotar manualmente un test set adicional (~100 instancias del pilot 500, posiciones 100+).
4. Lanzar revisión nativa multi-anotador sobre el output de la mejor config.
5. Decidir Fase 2 de adaptación cultural (humano-en-el-loop sobre `cultural_candidates`).
6. Escalar a 10k solo después de pasar (1)-(5).
7. Fine-tuning BETO/XLM-R en las 4 condiciones experimentales (ES→ES, ES→RP, RP→RP, RP→ES).
8. Experimentos ET-augmentado (Deng et al. 2024 + ablación MLM aleatorio).
9. **Dataset de QA sobre cuentos rioplatenses** (pendiente): construir un dataset de preguntas y respuestas a partir de los textos en `texts/` (corpus de cuentos RP del experimento de eye-tracking de Fermín). Scripts base ya existen: `scripts/generate_qa_dataset.py` y `scripts/validate_qa_dataset.py`. Output parcial en `data/processed/qa_stories_*.jsonl`. Objetivo: complementar XNLIrp con una tarea QA en dominio literario RP para evaluar comprensión más allá de NLI. Posible skill de Claude Code para generación + validación automática del dataset.

## 8. Pendientes: vocabulario XNLI a resolver

Palabras identificadas en análisis de vocabulario completo (7 500 instancias). Ordenadas por CNT descendente dentro de cada categoría. Contador de ocurrencias = suma de apariciones en prem_es + hyp_es. Ir resolviendo de a una: verificar ejemplos, decidir regla de prompt y marcar con ✓.

Leyenda columna ACCIÓN: **mantener** = dejar sin tocar (nombre propio, técnico, NLI-crítico); **regla** = agregar instrucción al prompt; **resuelto** = ya cubre el prompt actual.

### 8.1 Inglés / lugares / nombres propios

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

### 8.2 Peninsularismos léxicos

| ☐ | PALABRA | CNT | CONTEXTO / EJEMPLOS | ACCIÓN PROPUESTA |
|---|---------|-----|---------------------|-----------------|
| ✓ | dinero | 149 | Usado genéricamente. "tenía mucho dinero..." | **resuelto**: `dinero → plata` por defecto; MANTENER solo en terrorismo/compuestos lexicalizados/jerga técnica extranjera/donación institucional. Regla revisada por hablante nativo RP, mayo 2026. |
| ✓ | escuela | 115 | "fue a la escuela..." | **mantener**: "escuela" es natural en RP y más frecuente que "colegio" en corpus AR (1,645 vs 903). Usar "colegio" solo cuando el contexto indique secundaria explícitamente (raro en XNLI). |
| ☐ | he | 113 | PPC auxiliar. "he dicho / he ido..." | **resuelto**: regla PPC ya en prompt (cambiar si coloquial + acción puntual) |
| ✓ | eh | 93 | Muletilla / marcador discursivo. "¿eh? / pero eh..." | **resuelto**: MANTENER. "Eh" como muletilla de hesitación es idéntico en RP y en español neutro. Verificado en 15 ejemplos XNLI, todos usan "eh" exactamente como lo usaríamos en RP. Cero cambios. |
| ✓ | oh | 90 | Interjección anglicismo en transcripciones de habla. "Oh, pasé buena parte..." | **resuelto**: regla contextual `oh → ah/uy/ay Dios/etc` agregada al prompt (apertura suave → ah/uy; afirmación → ah, sí/ah, claro; sorpresa con Dios → ay Dios/Dios mío; doblada → uy, uy). Mantener solo en literario explícito. |
| ☐ | hemos | 70 | PPC primera persona plural. "hemos dicho / hemos ido..." | **resuelto**: regla PPC ya en prompt |
| ✓ | habían | 70 | Pluscuamperfecto. "habían dicho..." | **resuelto**: MAYORITARIAMENTE MANTENER (pluscuamperfecto idéntico en RP). Excepción: caso "habían piratas/algo" (haber existencial impersonal) → corregir a "había" como tipo D. D2 ya cubre el caso, no requiere nueva regla. |
| ✓ | millas | 65 (50 plural + 15 singular) | Unidad imperial. "a cinco millas de distancia..." | **resuelto**: regla agregada al prompt. `millas → kilómetros` con CONVERSIÓN NUMÉRICA REAL (1 mi ≈ 1.609 km, redondear a natural) para distancias terrestres. MANTENER SOLO en contexto náutico/marítimo (milla náutica = estándar AR). Nombres propios con unidad métrica TAMBIÉN se adaptan: "Milla de Oro" → "Kilómetro de Oro", "Golden Mile" → "Golden Kilometer" (excepción controlada a Restricción 2). Cuidado NLI: convertir ambos lados prem-hyp coherentemente. |
| ✓ | ti | 47 | Pronombre tónico. "a ti te dije..." | **resuelto**: regla `ti → vos` agregada al voseo (sección A) en v1 y v2. Aplica a TODAS las preposiciones (a/para/de/por/en/hacia/sin/contra/sobre) y al reflexivo enfático "a ti mismo → a vos mismo". Caveat de registro arcaico igual que voseo. |
| ✓ | señoría | 45 | Título nobiliario inglés (His Lordship) en Captain Blood. "su señoría ordenó..." | **resuelto**: MANTENER. Las 10 ocurrencias son Captain Blood (Sabatini) — título nobiliario inglés, no judicial. Cubierto por el caveat de voseo arcaico ("su señoría" bloquea voseo y mantiene "tú"). Además "señoría" es válido en RP (también judicial AR). Cero cambios. |
| ☐ | eres | 43 | Forma tuteo "tú eres". "¿tú eres...?" | **resuelto**: regla C voseo → "sos" |
| ☐ | españoles | 26 | Gentilicio. "los españoles dijeron..." | mantener (referente geográfico correcto) |
| ☐ | rey | 47 | Título o apellido. "el rey ordenó..." | mantener (referente real o título histórico) |
| ✓ | tonto | 29 | Adjetivo/insulto. "eres un tonto..." | **resuelto**: regla contextual `tonto → boludo/tarado/iluso/pavo` agregada al prompt. Insulto a persona → boludo/tarado/iluso; adjetivo de cosa abstracta → boludo/a; "hacerse el tonto" → "hacerse el boludo" (NO "el gil", que tiene otro sentido); predicativo impersonal → "al pedo/boludo". Mantener solo en narrativa literaria pura, compuestos lexicalizados o registro académico. |
| ✓ | niño | 35 | Sustantivo. "el niño jugó..." | **mantener** por defecto. En coloquial/familiar puede ir nene/nena o chico/a ("mi nene", "los chicos del barrio"). En la duda, mantener. |
| ✓ | pronto | 27 | Adverbio temporal. "lo hará pronto..." | **resuelto**: MANTENER por defecto. "Pronto" es estándar en RP en todos los registros, igual que "tan pronto como". Alternativas coloquiales "ni bien", "apenas", "enseguida", "rápido" son válidas pero NO obligatorias; solo cambiar si la oración es coloquial-conversacional y la alternativa suena más natural. Regla agregada al prompt. |
| ✓ | bote | 28 | "bote de basura" (ES) vs "tacho" (RP). "tiró en el bote..." | **resuelto**: embarcación chica → mantener "bote"; embarcación grande → "barco"; "bote de basura" → "tacho de basura" (1 sola ocurrencia en XNLI). |
| ☐ | cabo | 27 | Grado militar o topónimo. "el cabo dijo..." | mantener (grado militar = igual en RP) |
| ✓ | mmm | 60 | Muletilla reflexiva. "mmm, no sé..." | **resuelto**: MANTENER, idéntico en RP. |
| ✓ | uh / hum / um | 54+24+15 | Muletillas de hesitación anglófonas. "hum, no sé..." / "um, por lo que..." | **resuelto**: `uh/hum/um → este.../mmm/emm`; "uh-huh" → "ajá". Agregado mayo 2026 tras análisis subtítulos LA. |
| ☐ | chica | 29 | Sustantivo / adjetivo femenino. "la chica dijo..." | **resuelto**: `joven/jóvenes → chico/a` ya en prompt; "chica" como sustantivo directo ya es RP |
| ☐ | tío | 28 | Familiar o coloquial. "mi tío / oye tío..." | **resuelto**: regla `tío→che/tipo` ya agregada en Fase 1d |

### 8.3 Medio Oriente / geopolítica / 9-11

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

### 8.4 Otras

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

> **Nota de trabajo:** las palabras marcadas como "resuelto" o "mantener" pueden cerrarse rápidamente (cambiar ☐ a ✓). Las que dicen "revisar" necesitan ver 2-3 ejemplos del XNLI antes de decidir. Usar `scripts/_lookup_pendientes.py` para extraer ejemplos de cualquier palabra.
