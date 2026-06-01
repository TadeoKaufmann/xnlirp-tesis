# Pendientes: vocabulario XNLI a resolver

---

## Completar las instancias faltantes del full 7500

**30 instancias del test set sin procesar** (inventariadas el 2026-05-28). Son del test split (5010 inst) — no sustituibles con instancias del train de XNLI porque son contenido diferente (MultiNLI vs. LILT).

**Idx faltantes:**
`528, 540, 600, 615, 2693, 4125, 4234, 4235, 4236, 4237, 4239, 4240, 4241, 4242, 4243, 4517, 4526, 4664, 4737, 4783, 4948, 4949, 4950, 4951, 4952, 4953, 4954, 4955, 4956, 4975`

**Opciones:**
- ☐ Traducir los 30 (run puntual ~5 min, gradear, agregar a `combined_6884_full.jsonl` o `to_fix_pending_all.jsonl`)
- ☐ Dejar el gap y documentarlo: 7.467/7.500 = 99.6% de cobertura, truncación de pipeline, defensible en tesis

Cluster sospechoso: idx 4234–4243 y 4948–4956 son corridas de números consecutivos → probablemente un batch que falló o fue truncado.

---

> **SUPERSEDED — mayo 2026**
> Las decisiones de este archivo fueron incorporadas a:
> - `decisiones_traduccion_tomadas.md` (rationales + decisiones por cluster)
> - `prompt_v2_cultural_inline.txt` (reglas activas)

Todo el vocabulario analizado está cerrado salvo los dos ítems de abajo y §9.

---

## Pendiente de análisis — PPC progresivo

☐ **Analizar cobertura de PPC progresivo en el dataset full 7500.** La regla "ha estado + gerundio → estuvo + gerundio" se agregó al prompt en mayo 2026 pero no fue testeada sistemáticamente. Hay que cuantificar cuántas instancias del full tienen PPC progresivo y verificar que el nuevo few-shot 3b lo cubre bien antes de escalar.

---

## Pendiente de resolución

| ☐ | pákistan | 33 | Topónimo con tilde inusual en el corpus ES. "en Pákistan..." | Forma estándar en RP es "Pakistán" — posible D fix. Verificar en corpus con `_lookup_pendientes.py`. |
| ☐ | pakistan | — | Variante sin tilde. | Normalizar a "Pakistán" — mismo D fix. |

---

## 9. Traducción del train set MultiNLI ES → RP (pendiente decisión con tutor)

**Contexto.** HuggingFace tiene `load_dataset("xnli", "es", split="train")` con ~392k instancias del MultiNLI traducidas al español por traductores profesionales (LILT, EN→ES con post-edición humana). Es el único train set disponible para XNLI ES — no hay datos de entrenamiento NLI nativos en RP.

**Por qué importa.** Para las 4 condiciones experimentales (ES→ES, ES→RP, RP→RP, RP→ES) las condiciones RP→RP y RP→ES necesitan instancias de entrenamiento en RP. Eso requiere traducir K instancias del train ES → RP con el pipeline.

**Dos niveles de ambición:**

- **Nivel tesis (mínimo necesario):** 5k instancias bien traducidas con Gemini + Sonnet validation son más que suficientes para K=200/500/1000. Un día de pipeline.
- **Nivel contribución (discutir con tutor):** Traducir el full 392k crearía el corpus de entrenamiento NLI en RP más grande existente — comparable a AmericasNLI. Costo estimado ~$45 con Gemini Batch API + Haiku para validación automática.

**Consideración metodológica.** El train ES ya tiene translationese EN→ES de la traducción original. Agregar ES→RP crea un doble layer. Para entrenamiento es aceptable (los modelos son robustos al ruido), pero vale mencionarlo como limitación y como argumento adicional de por qué los resultados RP→RP probablemente subestiman el potencial de datos RP nativos.

**Estrategia de validación propuesta.** Gemini Batch traduce todo → Haiku valida todo automáticamente → Sonnet valida muestra estratificada del 5% para reportar calidad en la tesis.

☐ **Decisión pendiente con tutor**: ¿cuántas instancias traducir (5k vs 392k)?
