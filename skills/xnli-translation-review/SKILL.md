---
name: xnli-translation-review
description: Revisar traducciones XNLI ES → RP hechas por Gemini, juzgar calidad dialectal y consistencia NLI usando el gold anotado como referencia anclada. Pensado para chat-review (humano o LLM-as-judge) en lotes.
---

# XNLI Translation Review

## Cuándo usar este skill

Después de correr Gemini sobre un batch nuevo (300, 500, 1000 instancias) que no fue anotado manualmente todavía. El objetivo: decidir si el batch tiene calidad suficiente para mandar a validación humana o si necesita iteración del prompt antes.

NO usar para:
- Re-evaluar el gold contra runs (eso usa `xnli-review-format` + `evaluate_against_gold.py`).
- Corregir UN caso puntual (es un workflow de lotes).

## Cómo funciona

1. Correr Gemini sobre el batch (output en `results/experiments/<config>.jsonl`).
2. Correr `scripts/format_for_review.py` que toma el run + lo agrupa en N bloques chat-friendly:
   - Bloques estándar: instancias con `type ≠ A` (cambios aplicados).
   - Bloques flag: instancias con `review_flag=true`.
   - Sample de control: muestra aleatoria de `type=A` (verificar que no se perdieron cambios).
3. El reviewer (humano por chat o LLM-as-judge) recibe cada bloque y devuelve veredicto.
4. Agregar veredictos y decidir.

## Anclas (references)

El gold `data/processed/xnli_combined_dev_200.jsonl` es la referencia anclada de qué cuenta como una buena traducción RP. Contiene 200 instancias con type A/B/C/D/E anotadas a mano. Usalo para:

- **Calibración**: si dudás de si un cambio es B o A, buscá una instancia similar en el gold y comparar.
- **Patrones aceptados**: el gold define implícitamente qué cambios léxicos son obligatorios vs opcionales.
- **Falsos positivos**: si el run aplica un cambio que el gold NO aplicaría, es candidato a rechazo.

El archivo `cultural_adaptations.jsonl` (387 instancias) es referencia para casos culturales E.3/E.4.

## Prompt para el reviewer (chat o LLM-as-judge)

Pegale este texto al inicio de la sesión de review:

```
Vas a revisar un batch de traducciones español neutro → español rioplatense del
benchmark XNLI. Tu tarea: para cada instancia, juzgar si la traducción RP es
de calidad aceptable. Calidad = (a) naturalidad rioplatense, (b) preservación
de la relación NLI entre prem y hyp.

Para cada instancia, devolver un veredicto en este formato:

idx <N>: <APROBAR | REVISAR | RECHAZAR>
  motivo: <una línea>
  fix: <propuesta de corrección o null>

Criterios:
- APROBAR: la traducción suena natural en RP, los cambios aplicados son
  defendibles según las reglas del prompt v2, NLI se preserva.
- REVISAR: hay un cambio que podría ser correcto pero requiere chequeo nativo
  (regla nueva, contexto ambiguo, registro discutible).
- RECHAZAR: hay error claro — armonización entre prem/hyp (mismo término EN
  traducido distinto), regla inventada, NLI roto, no es RP sino otro dialecto,
  o cambio mecánico que descontextualiza.

Estilo: terso. UN renglón por veredicto, no expliques de más.

Reglas RP que definen "natural" (resumen):
- Voseo en 2ª persona informal (tenés, podés, sabés, sos, vos, contigo→con vos, ti→vos).
- Léxico B: aquí→acá, allí→ahí, coche→auto, ordenador→computadora, móvil→celular,
  enfadado→enojado, pequeño→chico (por defecto), niño→chico/nene en coloquial,
  dinero→plata (por defecto, mantener solo en terrorismo/jerga técnica/compuestos
  lexicalizados), tonto→boludo/tarado/iluso según función, uh/hum/um→este.../mmm.
- PPC → pretérito simple si registro coloquial + acción puntual.
- Mantener PPC si estado vigente ("se ha convertido en X").
- D solo cuando hay error objetivo (falso amigo, anglicismo no traducido, typo).
- NO armonizar prem y hyp por sinonimia: divergencia léxica defendible es A.
- Cultural inline (v2): Joe→José tipo E.1; Santa Claus→Papá Noel tipo E.2;
  Captain Blood→Bouchard tipo E.3. Cluster 9/11/Indiana/Texas son E.4.

Ante la duda: REVISAR, no rechazar.
```

## Output esperado del reviewer

El reviewer devuelve líneas en el formato indicado. El script
`scripts/aggregate_verdicts.py` parsea esas líneas y produce:

- % aprobados, % a revisar, % rechazados.
- Top causas de rechazo (motivos repetidos).
- Lista de idx para iterar prompt si hay un patrón sistemático.

Decisión:
- ≥90% aprobados, ≤5% rechazados → batch listo para validación humana en producción.
- 70-90% aprobados → iterar prompt en los patrones de rechazo y re-correr.
- <70% aprobados → revisar prompt seriamente, hay un problema sistémico.

## Estructura del skill

```
skills/xnli-translation-review/
├── SKILL.md                         (este archivo)
├── scripts/
│   ├── format_for_review.py         (run jsonl → bloques chat-friendly)
│   └── aggregate_verdicts.py        (líneas de veredicto → métricas)
└── references/
    └── README.md                    (pointers a gold + ejemplos canónicos)
```
