# Prompt para Opus — re-pasada nombres anglos + pachuco

**Fecha**: 2026-05-15
**Input**: `data/processed/opus_anglos_batch_2026-05-15.jsonl` (51 instancias)
**Output esperado**: `data/processed/opus_anglos_batch_2026-05-15_translated.jsonl`

## Instrucciones para vos (Tadeo)

Abrí una sesión nueva de Claude.ai con **Opus**. Pegale el bloque de abajo.

---

# Tarea

Sos un experto en lingüística rioplatense. Vas a hacer una **segunda pasada** sobre 51 instancias XNLI que ya procesé antes y dejé como **type=A** (sin cambios). El usuario quiere ahora que las adapte CULTURALMENTE de forma agresiva — todo lo anglo se transpone al equivalente argentino, sin importar que sean figuras históricas reales.

## Lo que necesito que adaptes

### A. Nombres de figuras públicas reales EEUU → equivalente argentino (38 instancias)

**Estrategia híbrida (Opción B)**: usar famosos argentinos donde encaja sin distorsión, apellidos argentinos genéricos donde el rol es muy específico o políticamente cargado. Mantené siempre el rol/profesión explícito en el texto.

| EN | AR | Justificación |
|----|----|---------------|
| **McKim** (arquitecto 1890s) | **Pérez, arquitecto** o **Etchegaray, arquitecto** | apellido AR plausible, evita anacronismo (Pelli es contemporáneo) |
| **Gehry** (arquitecto contemporáneo) | **César Pelli** (o "Pelli") | encaja: arquitecto AR famoso contemporáneo ✓ |
| **Pickard** (Thomas Pickard, ex-FBI) | **García, ex-director de la SIDE** | apellido AR genérico, rol contextual |
| **Ashcroft** (John Ashcroft, AG EEUU) | **Domínguez, ministro de Justicia** | apellido AR genérico, evita carga política |
| **Lewinsky** (Monica Lewinsky) | **María Fernández** o **Liñares** | nombre AR neutral, evita carga política/escándalo |
| **Pynchon** (Thomas Pynchon, escritor) | **Borges** | el escritor AR universalmente reconocido ✓ |
| **Boswell** (James Boswell, biógrafo) | **Sábato** (Ernesto Sábato, ensayista) | escritor-ensayista famoso AR ✓ |
| **Skeat** (Walter Skeat, filólogo) | **Borges** | Borges fue bibliotecario/lingüista, encaja ✓ |

**Nota sobre Borges**: aparece como equivalente para Pynchon Y Skeat. Si en alguna instancia los dos referentes aparecen juntos en la misma oración (lo cual sería raro en XNLI), elegí solo uno y dejá el otro como **Cortázar** o **Sábato** para no duplicar.

Si aparecen **medios de comunicación EEUU** asociados, también adaptar:
- Newsweek, Fox News → **Clarín, La Nación, TN, Página/12, Perfil** según contexto
- Cambridge University Press → **Eudeba** (editorial UBA) o **Siglo XXI**

### B. pachuco/pachucas → compadrito/compadrita (11 instancias)

Reemplazar consistentemente:
- pachuco/pachucos → **compadrito/compadritos**
- pachuca/pachucas → **compadrita/compadritas**

**Importante con "Chicana/Chicanas"**: cuando aparezca la palabra "Chicana" como identidad étnica, **eliminala o reescribí esa parte**. En RP no existe ese referente. Ejemplos:
- "el arquetipo de la chica de barrio que se reúne en la Chicana" → "el arquetipo de la chica de barrio porteño"
- "jóvenes Chicanas" → "jóvenes compadritas" o "pibas de barrio"

### C. Preservar NLI

La etiqueta entailment/neutral/contradiction NO puede cambiar. Si la adaptación rompe la lógica, registralo en `review_flag: true` con `review_note`.

## Archivos a leer (en este orden)

1. `data/processed/opus_anglos_batch_2026-05-15.jsonl` — input (51 instancias, cada una con `_opus_previa_prem_rp` que es tu decisión anterior)
2. `data/processed/cultural_adaptations.jsonl` — referencia para consistencia E.1/E.3/E.4 (387 instancias ya procesadas)
3. `scripts/prompts/prompt_v2_cultural_inline.txt` — reglas base
4. `scripts/prompts/prompt_opus_cultural.txt` — reglas extendidas E.3/E.4

## Output

Mismo formato JSONL que `cultural_adaptations.jsonl`. Cada línea:

```json
{
  "idx": <int>,
  "label": "...",
  "prem_es": "...", "hyp_es": "...",
  "prem_rp": "<adaptado AR>", "hyp_rp": "<adaptado AR>",
  "type": "E",
  "changes": ["McKim → Bustillo (E.1: arquitecto AR equivalente)", ...],
  "secondary_features": [],
  "cultural_candidates": [],
  "review_flag": false,
  "review_note": "",
  "note": "una línea explicando la decisión"
}
```

Guardalo en `data/processed/opus_anglos_batch_2026-05-15_translated.jsonl`.

## Tono de decisión

**Adaptá agresivamente**. El usuario fue explícito: "no importa que sean figuras históricas, cambialas por personas argentinas, por diarios argentinos y demás". Si dudás entre mantener (por fidelidad histórica) y adaptar, **adaptá**.

## Volumen

51 instancias. ~25-35 min de procesamiento.

## Si te faltan nombres argentinos

El usuario dijo: "si te faltan famosos argentinos te puedo buscar". Si llegás a un caso donde no encontrás un equivalente argentino plausible, marcalo `review_flag: true` con `review_note: "necesito sugerencia de figura argentina equivalente"`. No inventes nombres sin sustento.
