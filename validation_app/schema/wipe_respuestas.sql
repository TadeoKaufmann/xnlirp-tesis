-- ============================================================
-- WIPE TOTAL — Respuestas + catalogo_instancias legacy.
-- Útil para empezar limpio antes de subir un batch nuevo de instancias.
-- NO toca `instancias` ni `reservas` (esas las maneja replace_all_*.sql).
-- ============================================================

-- 1. Borra todas las respuestas y resetea el id sequence a 1.
--    Próximas inserciones arrancarán en id=1.
TRUNCATE TABLE public."Respuestas" RESTART IDENTITY CASCADE;

-- 2. Elimina la tabla legacy catalogo_instancias (si existe).
DROP TABLE IF EXISTS public.catalogo_instancias CASCADE;
