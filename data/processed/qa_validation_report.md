# Reporte de validación zero-shot del dataset QA

**Modelo:** gemini-2.5-flash (T=0.0, zero-shot)
**Grupos evaluados:** 129
**Respondidos:** 129 (0 fallos API)
**Chance baseline:** 20.0% (1 de 5 candidatos)

## Accuracy global

| Métrica | Valor |
|---------|-------|
| Correctas | 127 / 129 |
| Accuracy | 98.4% |
| Chance baseline | 20.0% |
| Lift sobre chance | +78.4pp |

## Por tipo de pregunta

| Tipo | Correctas | Total | Accuracy |
|------|-----------|-------|----------|
| factual | 108 | 110 | 98.2% |
| inferencial | 19 | 19 | 100.0% |

## Por split

| Split | Correctas | Total | Accuracy |
|-------|-----------|-------|----------|
| train | 34 | 34 | 100.0% |
| dev | 93 | 95 | 97.9% |

## Por cuento

| Cuento | Correctas | Total | Accuracy |
|--------|-----------|-------|----------|
| Axolotl | 93 | 95 | 97.9% |
| Ahora debería reírme, si no estuviera muerto | 34 | 34 | 100.0% |

## Errores (2 casos)

**Cuento:** Axolotl | **Tipo:** factual
**Pregunta:** ¿Cuándo iba el narrador al principio?
**Eligió candidato:** 3 (correcto era 5)

**Cuento:** Axolotl | **Tipo:** factual
**Pregunta:** ¿Según lo que le parecía al narrador, cómo estaban él y el otro personaje al comienzo?
**Eligió candidato:** 2 (correcto era 4)
