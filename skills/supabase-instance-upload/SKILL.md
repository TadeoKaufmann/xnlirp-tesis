---
name: supabase-instance-upload
description: Subir batches de instancias XNLI traducidas a la tabla `instancias` de Supabase para que la validation_app las muestre a los anotadores nativos. Maneja replace-all (reemplazar todo) o append (sumar a lo existente), genera SQL, y mantiene un manifest de qué batches fueron subidos.
---

# Supabase Instance Upload

## Cuándo usar este skill

Cuando un batch de traducciones está listo para validación humana en la app:
- Pasó por revisión automática (Gemini) y/o manual (usuario, Opus).
- Tiene 0 review_flag activos.
- Está marcado como "ready for app validation" en `processed_idxs.json`.

NO usar para:
- Modificar la tabla `Respuestas` (eso lo maneja el app mismo).
- Cambios al schema de Supabase (eso va por SQL editor manual).
- Batches sin validar internamente primero.

## Modelo de datos

Tabla `instancias` en Supabase:
```sql
CREATE TABLE instancias (
  idx          int PRIMARY KEY,
  prem         text NOT NULL,
  hyp          text NOT NULL,
  batch_name   text,                  -- ej. "sample_300_v2_test"
  uploaded_at  timestamptz DEFAULT now(),
  source_file  text                   -- ej. "results/experiments/.../xxx.jsonl"
);
```

Si la tabla no tiene `batch_name`, `uploaded_at`, `source_file` todavía, el skill imprime el ALTER TABLE necesario al inicio del SQL generado.

## Operaciones soportadas

### `replace-all`
Borra todo lo existente en `instancias` y sube el batch nuevo. Útil cuando el batch
anterior fue completamente validado o se quiere empezar fresh.

```bash
python skills/supabase-instance-upload/scripts/generate_upload_sql.py \
    --input results/experiments/xnli_sample_300_v2_test__gemini-2.5-flash__T0.1__v2.jsonl \
    --batch-name "sample_300_v2_test_2026-05-14" \
    --mode replace-all \
    --output validation_app/upload_sql/replace_all_2026-05-14.sql
```

### `append`
Suma el batch a lo existente. La PK `idx` previene duplicados; si hay conflicto,
ON CONFLICT DO UPDATE (actualiza prem/hyp).

```bash
python skills/supabase-instance-upload/scripts/generate_upload_sql.py \
    --input <jsonl> \
    --batch-name "sample_1000_v2_2026-06-xx" \
    --mode append \
    --output validation_app/upload_sql/append_2026-06-xx.sql
```

### `delete-batch`
Borra todas las instancias de un batch específico (por nombre). Útil para revertir.

```bash
python skills/supabase-instance-upload/scripts/generate_upload_sql.py \
    --batch-name "sample_300_v2_test_2026-05-14" \
    --mode delete-batch \
    --output validation_app/upload_sql/delete_batch_xxx.sql
```

## Workflow completo para un upload

1. **Generar el SQL**:
   ```bash
   python skills/supabase-instance-upload/scripts/generate_upload_sql.py \
       --input <run.jsonl> --batch-name <name> --mode replace-all \
       --output validation_app/upload_sql/<name>.sql
   ```

2. **Ejecutar en Supabase**: abrir el SQL editor de Supabase, pegar el SQL, run.

3. **Actualizar el manifest**:
   ```bash
   python skills/supabase-instance-upload/scripts/update_manifest.py \
       --batch-name <name> --action uploaded
   ```

4. **Actualizar processed_idxs.json**: marcar el batch como `pending_app_validation: false` cuando empiecen a llegar respuestas (eso es decisión humana, no automática).

5. **(Opcional) Actualizar index.html** si todavía no se migró a leer de Supabase: el skill puede regenerar la const `INSTANCES` con `--also-regen-html`.

## Manifest

`skills/supabase-instance-upload/scripts/upload_manifest.json` lleva el registro de
qué batches están subidos:

```json
{
  "current_batch": "sample_300_v2_test_2026-05-14",
  "history": [
    {
      "batch_name": "sample_300_v2_test_2026-05-14",
      "uploaded_at": "2026-05-14T12:00:00",
      "count": 298,
      "source_file": "results/experiments/...",
      "status": "active"
    }
  ]
}
```

## Estructura del skill

```
skills/supabase-instance-upload/
├── SKILL.md                       (este archivo)
├── scripts/
│   ├── generate_upload_sql.py     (jsonl → SQL)
│   ├── update_manifest.py         (actualiza upload_manifest.json)
│   ├── regenerate_html_instances.py  (regenera const INSTANCES — fallback)
│   └── upload_manifest.json       (estado de uploads)
└── references/
    └── schema.sql                 (DDL de la tabla instancias)
```

## Migración del app a leer de Supabase (one-time)

Estado actual: `validation_app/index.html` tiene `const INSTANCES = [...]` hardcoded.
Para que el upload SQL surta efecto sin tocar el HTML, el app debe migrar a:

```js
// reemplazar la const INSTANCES por:
let INSTANCES = [];
async function loadInstances() {
  const { data, error } = await sb.from('instancias').select('idx, prem, hyp');
  if (error) throw error;
  INSTANCES = data;
}
// Llamar loadInstances() antes de iniciar el flujo.
```

El skill incluye `references/migration_snippet.js` con el diff a aplicar.

## Notas

- Las inserciones usan `ON CONFLICT (idx) DO UPDATE` para que re-uploads sean idempotentes.
- Los textos se escapan con `$$...$$` (dollar-quoted) para evitar problemas con comillas.
- El SQL generado se commitea junto al jsonl para auditabilidad (`validation_app/upload_sql/`).
