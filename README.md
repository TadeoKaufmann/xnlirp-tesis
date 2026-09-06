# Datasets Rioplatenses: XNLIrp + QA-Cuentos-ET

Datasets y pipelines de la tesis de licenciatura **"Representación dialectal en NLP: un benchmark para el español rioplatense y enriquecimiento de datos guiado por eye-tracking"** (Tadeo Kaufmann, Universidad de Buenos Aires — Facultad de Ciencias Exactas y Naturales, 2026).

El español rioplatense, hablado por ~50 millones de personas en Argentina y Uruguay, está prácticamente ausente de los benchmarks de evaluación en NLP. Este repo publica dos datasets construidos para llenar ese vacío en dos tareas distintas, junto con los pipelines completos usados para construirlos.

## Contenido

### [`xnlirp/`](xnlirp/) — inferencia de lenguaje natural

La primera adaptación de [XNLI](https://github.com/facebookresearch/XNLI) al español rioplatense. 7.500 instancias (premisa, hipótesis, etiqueta) con correspondencia exacta entre las versiones en español peninsular y rioplatense, lo que permite comparar directamente el rendimiento de un modelo entre ambas variedades.

- Pipeline de traducción/adaptación dialectal con Gemini 2.5 Flash (tipología A/B/C/D/E de cambios).
- Validación automática (gpt-4o-mini) y validación nativa (340 hablantes rioplatenses, 7.120 respuestas).

### [`qa_cuentos_et/`](qa_cuentos_et/) — comprensión lectora / selección de oraciones respuesta

El primer dataset de comprensión lectora en español rioplatense construido sobre el corpus **Cuentos ET** (Travi et al., 2026, *Scientific Data*) — cuentos de ficción breve leídos por lectores rioplatenses con eye-tracking. 1.788 preguntas, 8.940 instancias (1 oración correcta + 4 negativas duras por pregunta).

- Pipeline de generación de preguntas con Gemini 2.5 Flash y validación cruzada con Claude Haiku.
- Negativas seleccionadas por similitud semántica (embeddings) para evitar atajos léxicos triviales.

## Resultado de la tesis

Ambas hipótesis de la tesis se pusieron a prueba entrenando y evaluando BETO sobre estos datasets, y **ninguna se confirmó**: un modelo entrenado en español peninsular transfiere al rioplatense en NLI prácticamente sin pérdida de rendimiento, y las señales de eye-tracking no mostraron una mejora consistente en comprensión lectora. El valor de este repositorio está en los datasets y los pipelines en sí — ambos documentados y reproducibles — más que en un resultado positivo de las hipótesis.

## Cómo citar

Si usás alguno de estos datasets, por favor citá la tesis:

```
Kaufmann, T. (2026). Representación dialectal en NLP: un benchmark para el
español rioplatense y enriquecimiento de datos guiado por eye-tracking.
Tesis de Licenciatura en Ciencias de Datos, Universidad de Buenos Aires.
```

## Contacto

Tadeo Kaufmann — tadeokaufmann1@gmail.com
