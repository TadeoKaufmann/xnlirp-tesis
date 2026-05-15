# `upload_sql/` — SQL para subir instancias a Supabase

Archivos generados por el skill `supabase-instance-upload`. Cada uno contiene un
batch listo para ejecutar en el SQL editor de Supabase.

## Convención de nombres

```
<modo>_<nombre-batch>_<fecha>.sql
```

Donde `modo` es:
- `replace_all` — borra todo de la tabla `instancias` y carga este batch (uso típico al rotar batches).
- `append` — agrega al batch existente (ON CONFLICT DO UPDATE).
- `delete_batch` — borra solo las filas de un batch específico (rollback).

## Flujo de subida

1. **Setup inicial** (una sola vez, por ambiente Supabase):
   - Correr `validation_app/schema/setup.sql` en el SQL editor.
2. **Generar SQL del batch**:
   ```bash
   python skills/supabase-instance-upload/scripts/generate_upload_sql.py \
       --input <jsonl> --batch-name <name> --mode replace-all \
       --output validation_app/upload_sql/<file>.sql
   ```
3. **Ejecutar en Supabase**: pegar el SQL en el editor y correr.
4. **Marcar el batch como subido**:
   ```bash
   python skills/supabase-instance-upload/scripts/update_manifest.py \
       --batch-name <name> --action uploaded --source-file <jsonl> --count <n>
   ```

## Archivo `_archive/`

SQLs históricos del workflow viejo (pre-mayo 2026), cuando se subían instancias
a mano hardcodeadas en el HTML. Conservados solo por trazabilidad.
