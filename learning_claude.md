# Learning Claude Code

Guía personal — lo que voy entendiendo de cómo funciona Claude Code.

---

## Plan Mode

Cuando uso `/plan` o Claude entra en modo plan, el plan queda guardado en `.claude/plans/` dentro del proyecto actual.

- El archivo se crea automáticamente con un nombre basado en el prompt.
- Puedo releerlo en conversaciones futuras para retomar el contexto.
- Claude puede editarlo durante la planificación antes de ejecutar.
- Al aprobar el plan, Claude sale del modo plan y empieza a ejecutar.

---

## El símbolo @

`@archivo` en el **chat** → Claude lo lee automáticamente e incluye el contenido en el contexto.

`@archivo` en un **archivo del repo** (CLAUDE.md, etc.) → no hace nada especial, es solo texto.

Si querés mencionar un archivo sin que Claude lo lea, usá backticks: `` `ruta/al/archivo` ``

---
think, think more, think a lot, think longer, ultrathink