# Decisiones de traducción tomadas

Documento de referencia. No duplica las reglas del prompt — documenta **rationales** y **decisiones de caso específico** que no son inferibles leyendo el prompt.

---

## Fuentes de verdad activas

| Fuente | Qué contiene | Estado |
|--------|-------------|--------|
| `prompt_v2_cultural_inline.txt` | Reglas activas A/B/C/D/E | vigente |
| `data/dev/cultural_adaptations.jsonl` | ~387 instancias con adaptaciones culturales (Opus); muestra qué se hizo realmente | primaria |
| `pipeline_traduccion/referencias/historial_prompts.md` | Evolución cronológica de reglas + rationales | vigente |
| `pipeline_traduccion/referencias/_ejemplos_xnli_archivado.txt` | Bitácora de decisiones instancia por instancia (1266 líneas) | archivado (git 596a46c^) |

Cuando haya discrepancia entre fuentes, `cultural_adaptations.jsonl` tiene prioridad (muestra los cambios realmente aplicados).

---

## Decisiones dialectales — rationale

### `dinero → plata` (regla INVERTIDA)

La regla original era "plata solo en registro coloquial/personal". Tras validación directa con hablante nativo RP sobre 20 instancias XNLI + corpus AR (ratio plata:dinero = 2.4x), la regla se **invirtió**: plata es el DEFAULT. Mantener `dinero` solo en:
- (a) terrorismo organizado (Al Qaeda, talibanes: "Al Qaeda recaudaba dinero")
- (b) jerga técnica extranjera (hawaladar, rupias)
- (c) compuestos lexicalizados (lavado de dinero, blanqueo de dinero)
- (d) donación institucional formal explícita

### `pequeño → chico`

Corpus AR muestra "chico" ~16x más frecuente que "pequeño" en uso cotidiano. Aplica a tamaño físico, comparativos, cantidad abstracta. No aplica a registro formal/técnico.

### `pronto` — MANTENER

No es peninsularismo. Estándar en RP en todos los registros. El prompt lo mantiene por defecto.

### `escuela` — MANTENER

Corpus AR muestra "escuela" (1.645 ocurrencias) vs "colegio" (903 ocurrencias). "Escuela" es más frecuente y natural en RP para educación primaria. Solo cambiar a "colegio" cuando el contexto indique secundaria explícitamente.

### `eh` — MANTENER

Idéntico en RP como muletilla de hesitación. Verificado en 15 ejemplos XNLI, cero diferencia.

### PPC vigente vs puntual

Si el estado resultante sigue vigente hoy ("se ha convertido en X" = sigue siendo X) → **mantener**. Si hay marcador temporal puntual explícito o el evento es puntual en registro coloquial → **cambiar a pretérito simple**.

### Voseo — caveat arcaico

En contexto inglés/nobiliario original (texto tipo *Captain Blood* antes de la transposición E.3) → no aplicar voseo. Después de aplicar E.3 Bouchard, los marcadores arcaicos desaparecen → sí aplicar voseo normalmente.

### Tipología B+E — E tiene prioridad

Si una instancia tiene adaptación cultural E + cambios B/C/D → `type=E`; los cambios B/C/D van a `secondary_features`. Rationale: E es la adaptación más invasiva y la que más puede romper NLI; debe estar en el radar del evaluador con scrutinio extra.

---

## Decisiones culturales por cluster

Verificadas contra `data/dev/cultural_adaptations.jsonl` (fuente primaria).

### `911_alqaeda` (166 instancias)

- **World Trade Center** → "Torres Gemelas" (nombre castellano popular en RP). **Pentagon** → "Pentágono". Estos usan E.1 (nombre castellano conocido), NO transposición a AMIA.
- **KSM / Ramzi Yousef** → descriptores funcionales: "el organizador del atentado" / "el organizador previo". Nunca apellidos AR en roles de terroristas.
- **Trama aérea de Manila (1995)** → "un complot anterior" (1988, pre-AMIA). World Trade Center en ese contexto → "sede de la AMIA".
- **PAPD** → "Prefectura Naval" (más AR que "policía portuaria"). Fix manual aprobado.
- Instancias clave: 3060-3062 (Torres Gemelas), 1521-1523 (KSM/Manila/AMIA), 3456-3458 (PAPD).

### `texas` (54 instancias)

- Texas → **Córdoba** consistentemente (provincia, no ciudad).
- República de Texas → "provincia de Córdoba" (movimiento separatista ficticio tolerable, NLI preservado).
- Medicaid → "salud pública" (sin equivalente directo AR).
- Houston → **Buenos Aires**.
- "Republicano/Republicana" → "del partido" (contexto partidista EEUU sin paralelo directo AR).
- Instancias clave: 138, 153-155, 183-184, 321-323, 2115-2117, 2802-2804, 3891-3893.

### `indiana` (50 instancias)

- Indiana → **Córdoba** (provincia).
- Indianapolis / Indianápolis → **Córdoba**.
- Adaptaciones institucionales específicas:
  - Museo de Arte de Indianapolis → Museo de Bellas Artes de Córdoba (Museo Provincial de Bellas Artes Emilio Caraffa)
  - Teatro Cívico de Indianápolis → Teatro Cívico de Córdoba
  - IRT (Indiana Repertory Theatre) → Comedia Cordobesa (compañía oficial real)
  - Asociación Dental de Indiana → Asociación Odontológica de Córdoba
  - Goodwill → Cáritas
  - Gary / Elkhart / Terre Haute → Río Cuarto / Villa María / Marcos Juárez
  - "Oscar" (en hyp) → Martín Fierro
- Instancias clave: 1755-1757, 1776-1781, 1827-1829, 1962-1964, 1983, 1932-1934.

### `fbi_cia` (80 instancias)

- CIA → **SIDE** (Secretaría de Inteligencia AR).
- FBI → **PFA** (Policía Federal Argentina).
- Instancias clave: 129-131, 324-326.

### `california` (25 instancias)

- En contexto de trabajadores migrantes: California → **Mendoza**; Arizona → **Salta**; México → **Bolivia** (paralelo real: trabajadores bolivianos en Mendoza/Salta).
- En contexto de nombres hispanos (Santa Fe NM): **MANTENER** (el argumento se basa en nombres hispanos en EEUU, topónimo NLI-crítico).
- Hoosiers de Indiana (idx 3813, en cluster california): → "cordobeses"; figuras históricas reemplazadas por: Leopoldo Lugones, Deán Funes, Arturo Illia.
- Instancias clave: 2811-2813, 2394-2396, 3813.

### `pak_afg` (9 instancias)

- campo Al-Faruq → **campo La Enredadera** (nombre AR ficticio).
- Kandahar → **Entre Ríos** (provincia AR).
- Predator → **drone** (nombre técnico desconocido en RP; E.4).
- Taliban → **talibanes** (D: anglicismo sin traducir).
- ⚠️ **Inconsistencia conocida en tracking**: idx 3225-3227 tienen `type=A` en el JSONL pero los cambios E.4 SÍ están aplicados en `prem_rp` (verificado). Error de clasificación al momento de guardar. Los cambios son válidos y están en el texto.

### `E.1` — escritores y figuras intelectuales

Decisión: **mantener figuras públicas reales** (McKim, Gehry, Pickard, Ashcroft, Pynchon, Skeat, Boswell, Lewinsky, etc.). Regla E.1 no aplica a personas reales históricas ni científicas. Solo aplica a nombres de ficción no célebres.

Excepciones resueltas específicamente:
- **Pynchon** → Borges (escritor AR icónico con vida privada similar; aprobado por usuario 2026-05-15)
- **Morrison** → Sábato; Gaddis → Aira; Faulkner → Saer (cuarteto idiosincrático AR)
- **Boswell** → Sábato; Johnson → Borges; Burke (Alabama) → Báez (UNT)
- **Skeat** → Borges (filólogo → lingüista; año ajustado 1895→1959 para coherencia biográfica)
- Estas sustituciones fueron caso por caso, no regla general.

### Convención Houston (idx 3891-3893)

- "Republicano/Republicana" → "del partido" (genérico).
- Houston, Texas → Buenos Aires.

### Captain Blood — E.3 Bouchard

Manejado por **regla de prompt** (sección E.3), no por `cultural_adaptations.jsonl`. Los ~28 instancias del corpus son detectadas por los nombres del texto y mapeadas según la tabla del prompt. Instancias no están en el JSONL cultural porque se procesan en el flujo normal de traducción.

Mapeo principal: Calverley → Calderón; Jamaica/Port Royal → Buenos Aires; Su Majestad → MANTENER (rey español pre-1816). Voseo arcaico se aplica normalmente (E.3 elimina el marcador nobiliario).

### Augusta (racial, idx 18)

No está en `cultural_adaptations.jsonl` (fue excluido del lote cultural). Decisión: MANTENER contexto Augusta post-bellum EEUU. Sin paralelo AR directo; adaptar introduciría distorsión histórica sin ganancia NLI.

---

## Instancias descartadas

Excluidas del dataset y no presentes en `cultural_adaptations.jsonl`:

| Idx | Razón de descarte |
|-----|------------------|
| 1566-1568 | Apellidos AR (Suárez/Saliba/Salgado) asignados a roles terroristas — éticamente inaceptable |
| 1650-1652 | Rumsfeld + plan talibanes — sin paralelo AR histórico aceptable |
| 4200-4202 | Talibán anti-pastunes — sin paralelo AR |

---

## Fixes D específicos del corpus

- **Indianapolis sin tilde** (idx 1755-1757): prem_es usa "Indianapolis" → normalizar a "Indianápolis" en prem_rp (D: ortografía española estándar).
- **haber existencial impersonal** (idx ~2399): "En el Caribe habían piratas" → "había piratas" (D: concordancia). La regla D2 del prompt ya lo cubre.
- **"y los and bares"** (idx 2361-2363): residuo de traducción ("and" sin traducir). D masivo — eliminar "and".
- **Bouchard D fixes** (ver historial_prompts.md): "La sangre" → "Bouchard"; género fragata Arabella → La Argentina.
- **"de derechas" → "de derecha"** (B: peninsular plural → singular RP; también idx 2211-2212).

---

## Inconsistencias conocidas en el gold

- **idx 1617-1618 vs 1619** (cluster Rey): los tres comparten estructura PPC. idx 1619 aplica correctamente pretérito simple (tipo B); 1617-1618 quedaron como tipo A. En re-evaluación con prompt v2, deberían ser tipo B.
- **pak_afg tracking**: idx 3225-3227 tienen `type=A` pero cambios E.4 aplicados (ver sección pak_afg arriba).

---

## Referencia histórica

```
Fuente primaria archivada: pipeline_traduccion/referencias/_ejemplos_xnli_archivado.txt
(1266 líneas — git commit 596a46c^, path original: scripts/_archive/_ejemplos_xnli.txt)
Contiene bitácora completa de decisiones con ejemplos instancia por instancia.
Estado al archivar: todos los análisis cerrados, 0 review_flag activos.
```
