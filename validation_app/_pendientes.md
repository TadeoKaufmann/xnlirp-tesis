# Validation App — Estado actual (mayo 2026)

Deploy: https://tadeo-tesis.vercel.app/ (Vercel, push a main = redeploy)
Backend: Supabase (anon key en index.html)

## Tablas Supabase

- **instancias**: idx, prem, hyp, batch_name — 6739 instancias cargadas
- **Respuestas**: anotador_id, idx, respuesta (1-5), palabras_marcadas (JSON), comentario_prem, comentario_hyp, region
- **reservas**: idx PK, anotador_id, created_at — anti-race-condition, TTL 2h
- **anotadores**: anotador_id PK, nombre, region, ranking_cap (NULL = sin cap)
- **RPC ranking_top10_with_me**: ranking con cap aplicado via LEAST(count, cap)

## Features implementadas

- Batch siempre 20 instancias (Fisher-Yates shuffle sobre instancias sin responder)
- Catch trial idx 9999 (hardcoded, fuera del sistema de reservas, siempre primero):
  - prem: "El chaval cogió el móvil y buscó el piso en internet, luego llamó a su jefe."
  - hyp:  "En Kettering, los Wollongong Bears ganaron el Tournament of Kilimsworth ante miles de fans."
  - Animación cursor 👆 sobre "chaval" y "Kettering" al entrar (solo si sin marcas previas, una vez por sesión)
- Welcome screen con animación typewriter char-by-char (21s total, skip si ya visitó)
- Ranking top 10 + fila del usuario actual aunque no esté en top 10
- Validador de nombre duplicado al enviar (confirm para mergear o elegir otro nombre)
- Barra de progreso meta 5000 en screen-thanks (query COUNT a Respuestas)
- ranking_cap en anotadores: Pablete cap=26 (datos reales intactos, solo cambia display)
- Escala 1-5 ("1 — Nada" / "5 — Muy"), hint: "recordá que no importa si tiene sentido, solo la argentinidad del texto"
- palabras_marcadas: JSON array de {pos, source, palabra} — clickeable en prem y hyp
- **Agrupación de hipótesis con misma premisa** (mayo 2026, rama `feat/grouped-hyps`, pendiente merge):
  - x1 (prem única): card normal prem+hyp — sin cambio
  - x2 (≤400 chars): card prem+hyp1+hyp2, dos score selectors
  - x2 (>400 chars): dos cards separadas normales — solo 11 casos en el dataset
  - x3 (tripla NLI completa): Card 1 = prem+entailment / Card 2 = neutral+contradiction sin premisa
  - Prem marks se copian a ambas instancias del par (Supabase sin cambios)
  - Shuffle balanceado: instancias cortas y largas intercaladas, nunca todas las pesadas juntas
  - Lookup `_label_by_idx.js` (45KB, 6739 entries) para identificar entailment sin tocar Supabase
  - **Resultado: 6.739 instancias → 4.577 grupos (−2.162, −32.1%); texto mostrado −430.629 chars (−36.8%)**

## Pendiente

- Feedback al avanzar en catch trial sin palabras marcadas (alternativa a toast: animación o hint inline)
- Verificar animación cursor en dispositivos móviles
- Workflow de descarga y limpieza post-ronda: exportar Respuestas → limpiar reservas → nueva ronda
