-- =============================================================
-- Limpieza de Respuestas y reservas contaminadas por testeos
-- Generado por clean_contaminated.py
-- Filas afectadas en Respuestas: 106
-- Anotadores contaminados: 14
-- Instancias que quedan libres: 102
-- =============================================================

-- 1. Borrar respuestas contaminadas
DELETE FROM "Respuestas"
WHERE id IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106);

-- 2. Liberar reservas de anotadores contaminados
DELETE FROM reservas
WHERE anotador_id IN ('4b459860-1d20-44c6-bbca-7ceb9a37b661', '4b4e1908-a9de-4b46-af8b-aae3d1b8f237', '74f093cc-87fb-4445-b2d4-00eaa1823a42', '77a5bbb2-a786-4e5a-95a9-a2e39671fd61', '82be7025-65b3-4d6e-8ef5-8ce2496b349e', '8f58f46a-06fa-4260-8668-6b9ca99a4128', '93c1520e-81ff-4fd3-8f27-0340e662c7ba', 'a96c6b91-2038-4808-a591-9134a51b1891', 'b11a3e2a-f5b5-4f01-b883-5334c3fa18f6', 'c8f862b5-1acc-4968-9342-78719b0ed5b2', 'c8ff2838-4c89-4b69-9572-c3fdf7782346', 'c9f096b9-1698-40d2-8abd-fea1324b3d59', 'e98c92d8-fd86-41ce-9173-0ab36b9d36dc', 'f8d94754-393a-49ac-b54f-629f7297d468');

-- Verificación (debería devolver 0 para ambas):
SELECT COUNT(*) AS respuestas_contaminadas_restantes
FROM "Respuestas" WHERE id IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106);

SELECT COUNT(*) AS reservas_contaminadas_restantes
FROM reservas WHERE anotador_id IN ('4b459860-1d20-44c6-bbca-7ceb9a37b661', '4b4e1908-a9de-4b46-af8b-aae3d1b8f237', '74f093cc-87fb-4445-b2d4-00eaa1823a42', '77a5bbb2-a786-4e5a-95a9-a2e39671fd61', '82be7025-65b3-4d6e-8ef5-8ce2496b349e', '8f58f46a-06fa-4260-8668-6b9ca99a4128', '93c1520e-81ff-4fd3-8f27-0340e662c7ba', 'a96c6b91-2038-4808-a591-9134a51b1891', 'b11a3e2a-f5b5-4f01-b883-5334c3fa18f6', 'c8f862b5-1acc-4968-9342-78719b0ed5b2', 'c8ff2838-4c89-4b69-9572-c3fdf7782346', 'c9f096b9-1698-40d2-8abd-fea1324b3d59', 'e98c92d8-fd86-41ce-9173-0ab36b9d36dc', 'f8d94754-393a-49ac-b54f-629f7297d468');
