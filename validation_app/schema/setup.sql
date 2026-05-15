-- ============================================================
-- SCHEMA SETUP — IDEMPOTENTE
-- Correr una sola vez en el SQL editor de Supabase.
-- Después de esto, los datos se cargan vía archivos de upload_sql/.
-- ============================================================
DROP TABLE IF EXISTS public.reservas CASCADE;
DROP TABLE IF EXISTS public.instancias CASCADE;

-- ============================================================
-- 1. Tabla instancias
-- ============================================================
CREATE TABLE public.instancias (
  idx           INTEGER     PRIMARY KEY,
  prem          TEXT        NOT NULL,
  hyp           TEXT        NOT NULL,
  batch_name    TEXT,                                       -- ej. "sample_300_v2_test_2026-05-14"
  uploaded_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  source_file   TEXT                                        -- jsonl de origen, ej. "results/experiments/..."
);

CREATE INDEX instancias_batch_idx ON public.instancias (batch_name);

-- RLS: cualquier anon puede leer, nadie puede escribir desde el cliente
ALTER TABLE public.instancias ENABLE ROW LEVEL SECURITY;
CREATE POLICY instancias_anon_read ON public.instancias
  FOR SELECT TO anon USING (true);

-- ============================================================
-- 2. Tabla reservas (anti-race-condition)
-- ============================================================
CREATE TABLE public.reservas (
  idx         INTEGER      PRIMARY KEY,
  anotador_id TEXT         NOT NULL,
  created_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- RLS: anon puede leer, insertar, actualizar y BORRAR solo reservas expiradas (>2h)
ALTER TABLE public.reservas ENABLE ROW LEVEL SECURITY;
CREATE POLICY reservas_anon_read ON public.reservas
  FOR SELECT TO anon USING (true);
CREATE POLICY reservas_anon_insert ON public.reservas
  FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY reservas_anon_update ON public.reservas
  FOR UPDATE TO anon USING (true);  -- la app controla el anotador_id
CREATE POLICY reservas_anon_delete_expired ON public.reservas
  FOR DELETE TO anon USING (created_at < now() - interval '2 hours');

CREATE INDEX reservas_created_at_idx ON public.reservas (created_at);

-- ============================================================
-- 3. Policy UPDATE para Respuestas (idempotente)
-- ============================================================
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename  = 'Respuestas'
      AND policyname = 'respuestas_anon_update'
  ) THEN
    EXECUTE 'CREATE POLICY respuestas_anon_update ON public."Respuestas" FOR UPDATE TO anon USING (true)';
  END IF;
END $$;

-- ============================================================
-- LISTO. Schema creado, sin datos.
-- Próximo paso: correr el SQL de upload_sql/ con el batch deseado.
-- ============================================================
