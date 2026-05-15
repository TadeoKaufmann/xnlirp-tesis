-- Schema de la tabla `instancias` en Supabase.
-- Ejecutar una sola vez (o como ALTER TABLE si ya existe sin columnas de tracking).

CREATE TABLE IF NOT EXISTS instancias (
  idx          int PRIMARY KEY,
  prem         text NOT NULL,
  hyp          text NOT NULL,
  batch_name   text,
  uploaded_at  timestamptz DEFAULT now(),
  source_file  text
);

-- Si la tabla ya existía sin las columnas de tracking, agregarlas:
-- ALTER TABLE instancias ADD COLUMN IF NOT EXISTS batch_name text;
-- ALTER TABLE instancias ADD COLUMN IF NOT EXISTS uploaded_at timestamptz DEFAULT now();
-- ALTER TABLE instancias ADD COLUMN IF NOT EXISTS source_file text;

-- Index por batch para queries de filtrado/delete por batch
CREATE INDEX IF NOT EXISTS idx_instancias_batch ON instancias(batch_name);

-- Policy RLS (Row Level Security): asumiendo que el app usa anon key,
-- permitir SELECT público (solo lectura). INSERT/UPDATE/DELETE solo
-- desde la consola SQL (con service_role o el dueño del proyecto).

-- ALTER TABLE instancias ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "public read instancias" ON instancias FOR SELECT USING (true);
