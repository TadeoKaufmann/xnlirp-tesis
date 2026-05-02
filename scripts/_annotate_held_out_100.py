"""
Anotador del held-out de 100 instancias (posiciones 100-199 del 500).

Las 100 anotaciones están embebidas como tuplas:
  (idx, type, prem_rp, hyp_rp, changes, secondary_features, cultural_candidates, note)

Si prem_rp/hyp_rp son None, se copian de prem_es/hyp_es (instancias type A).
Levenshtein se calcula con python-Levenshtein.
Reanudable: si el archivo destino ya tiene rows, salta los idx procesados.
"""
import json
import sys
from pathlib import Path

import Levenshtein
from tqdm import tqdm

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parent.parent
INPUT_500 = REPO_ROOT / "data" / "raw" / "xnli" / "xnli_pilot_500.jsonl"
OUTPUT = REPO_ROOT / "data" / "processed" / "xnli_held_out_100_raw.jsonl"


# ---------------------------------------------------------------------------
# Anotaciones manuales (Opus 4.7, max effort).
# Cada entrada: (idx, type, prem_rp_or_None, hyp_rp_or_None, changes,
#                secondary_features, cultural_candidates, note)
# Si prem_rp/hyp_rp son None → se reusa el ES (type A).
# ---------------------------------------------------------------------------

ANNOTATIONS = [
    # --- pos 100 ---
    (271, "A", None, None, [], [], [],
     "1ª persona pretérito simple; sin marcadores dialectales."),

    # --- pos 101 ---
    (996, "B",
     "sí, bueno, últimamente mi única experiencia a medias con acampadas es que nosotros, este... mi marido corre con autos",
     None,
     ["coches → autos (léxico peninsular → RP)",
      "esto... → este... (muletilla peninsular → RP)"],
     ["lexico_peninsular", "muletilla"], [],
     "Dos sustituciones léxicas obligatorias: 'coches' del listado peninsular y 'esto...' como muletilla peninsular ('este...' es la forma rioplatense)."),

    # --- pos 102 ---
    (4139, "A", None, None, [], [], [],
     "Tercera persona futuro; sin marcadores dialectales."),

    # --- pos 103 ---
    (4309, "A", None, None, [], [], [],
     "1ª persona pretérito; 'Concurso/Natividad Viviente' vs 'desfile/pesebre viviente' son glosas distintas del traductor (no se busca consistencia)."),

    # --- pos 104 ---
    (1731, "C",
     "Bueno, como estaba diciendo a su señoría, que pensaba como vos que tener a la Sra. Bishop fuera garantizaría nuestra seguridad, ni por su madre olvidaría ese esclavista lo que se le debe.",
     None,
     ["tú → vos (pronombre tónico tuteo → voseo)"],
     [], [],
     "Voseo en el pronombre tónico 'como tú' → 'como vos'. PPC 'no he hablado en años' en hyp se mantiene: 'en años' es marcador de duración hasta el presente (experiencial), no acción puntual concluida."),

    # --- pos 105 ---
    (4550, "A", None, None, [], [], [],
     "Subjuntivo formal usted ('Si encuentra'); nombres de pueblos extranjeros (Peculiar, Surprise, Errata...) se preservan."),

    # --- pos 106 ---
    (3804, "A", None, None, [], [], [],
     "Pretérito + presente 3ª persona; 'exalumnos' panhispánico."),

    # --- pos 107 ---
    (4916, "C",
     "Fui tan rápido como un rayo, ya sabés.",
     "El evento tardó años en llegar a su fin, ya sabés.",
     ["sabes → sabés (voseo)"],
     [], [],
     "Voseo en muletilla 'ya sabés' tanto en prem como en hyp."),

    # --- pos 108 ---
    (4238, "C",
     "No podés encontrar una respuesta más económica.",
     "No podés encontrar una respuesta más barata del libro.",
     ["puedes → podés (voseo)"],
     [], [],
     "Voseo en 2ª singular indicativo, mismo cambio en prem y hyp."),

    # --- pos 109 ---
    (70, "A", None, None, [], [], [],
     "Tercera persona; sin marcadores."),

    # --- pos 110 ---
    (2713, "A", None, None, [], [], [],
     "Registro corporativo 3ª persona; sin marcadores."),

    # --- pos 111 ---
    (3383, "D",
     "El presidente Bush elogió más tarde su propuesta, diciendo que había cambiado de opinión radicalmente.",
     None,
     ["propuiesta → propuesta (corrección de typo)"],
     [], [],
     "Typo ortográfico del ES original (letra extra); corrección análoga a 'guia → guía' del held-out 70 (idx 3440)."),

    # --- pos 112 ---
    (483, "A", None, None, [], [], [],
     "PPC 'He visto unas pocas veces' en hyp con valor experiencial frecuentativo se mantiene."),

    # --- pos 113 ---
    (4435, "A", None, None, [], [], [],
     "Tercera persona; sin marcadores."),

    # --- pos 114 ---
    (2398, "A", None, None, [], [], [],
     "Registro histórico 3ª persona; sin marcadores."),

    # --- pos 115 ---
    (4961, "A", None, None, [], [], [],
     "Clítico 'te' en 'te hacen sentir' es invariante entre tuteo y voseo; nombres de lugares extranjeros se preservan."),

    # --- pos 116 ---
    (4475, "A", None, None, [], [], [],
     "Registro académico 3ª persona; sin marcadores."),

    # --- pos 117 ---
    (2431, "A", None, None, [], [], [],
     "Tercera persona pretérito/imperfecto; sin marcadores."),

    # --- pos 118 ---
    (1625, "B",
     "¡Así que te contaron sobre eso!",
     None,
     ["te han contado → te contaron (PPC → pretérito simple RP)"],
     ["cambio_PPC"], [],
     "Vía 1 del prompt v1 (registro coloquial exclamativo + acción puntual concluida); el hyp ya usa pretérito simple ('dijeron'), confirmando el aspecto."),

    # --- pos 119 ---
    (2480, "A", None, None, [], [], [],
     "Tercera persona descriptivo; sin marcadores."),

    # --- pos 120 ---
    (4684, "A", None, None, [], [], [],
     "Impersonal 'uno puede'; cita francesa preservada."),

    # --- pos 121 ---
    (4443, "A", None, None, [], [], [],
     "Tercera plural; sin marcadores."),

    # --- pos 122 ---
    (3448, "A", None, None, [], [], [],
     "Tercera plural; sin marcadores."),

    # --- pos 123 ---
    (2083, "A", None, None, [], [], [],
     "Tercera persona descriptivo turístico; sin marcadores."),

    # --- pos 124 ---
    (1620, "A", None, None, [], [], [],
     "Narrativa 3ª persona pretérito/imperfecto; sin marcadores."),

    # --- pos 125 ---
    (685, "A", None, None, [], [], [],
     "1ª persona presente; sin marcadores 2ª. La estructura 'tengo un niño una niña' es del ES original (calca el EN aposicional), no se reescribe."),

    # --- pos 126 ---
    (3310, "A", None, None, [], [], [],
     "PPC 'hemos entrevistado/localizado' y 'se ha solicitado' con valor experiencial-resultativo en registro institucional formal; aceptable en RP escrito."),

    # --- pos 127 ---
    (2640, "A", None, None, [], [], [],
     "Registro corporativo 3ª persona; sin marcadores."),

    # --- pos 128 ---
    (940, "A", None, None, [], [], [],
     "1ª persona; 'pues' aceptable como muletilla en RP coloquial; 'ojalá lo supiera' panhispánico."),

    # --- pos 129 ---
    (2029, "A", None, None, [], [], [],
     "Registro histórico 3ª persona; sin marcadores."),

    # --- pos 130 ---
    (435, "C",
     "Porque en realidad no vivían en Augusta, vivían en… bueno, ya sabés, Augusta todavía era una ciudad pequeña en esa época, a pesar de que para la gente que vive en ciudades tan grandes como esta, Augusta no es tan grande.",
     None,
     ["sabes → sabés (voseo)"],
     [], [],
     "Voseo en muletilla 'ya sabés'; el resto es 3ª persona narrativa neutra."),

    # --- pos 131 ---
    (3109, "A", None, None, [], [], [],
     "Tercera persona; sin marcadores."),

    # --- pos 132 ---
    (243, "A", None, None, [], [], [],
     "'y tal' como muletilla coloquial es panhispánico; 3ª persona."),

    # --- pos 133 ---
    (4595, "A", None, None, [], [], [],
     "Tercera persona; sin marcadores."),

    # --- pos 134 ---
    (1168, "B",
     None,
     "Podemos sacar una conclusión de la simulación que hicimos en la computadora.",
     ["ordenador → computadora (léxico peninsular → RP)"],
     [], [],
     "Sustitución léxica obligatoria del listado peninsular."),

    # --- pos 135 ---
    (22, "A", None, None, [], [], [],
     "1ª persona pluscuamperfecto + pretérito; el apóstrofe extraño en hyp ('No 'lidié') es del ES original, se preserva (no es D objetivo)."),

    # --- pos 136 ---
    (1452, "D",
     "La piñata se cuelga de un árbol, con una cuerda larga que es manipulada por un adulto, que puede mover la piñata hacia arriba y hacia abajo para que no se rompa demasiado rápido.",
     "La piñata es colorida.",
     ["pieta → piñata (corrección de typo del ES; cf. EN 'pieata')",
      "piata → piñata (corrección de typo del ES)"],
     [], [],
     "Typos ortográficos en ambas partes; el referente cultural es 'piñata' (contexto: cuerda larga + se rompe). Análogo al gold idx 1453 (mismo patrón 'pieta/piata → piñata')."),

    # --- pos 137 ---
    (3587, "A", None, None, [], [], [],
     "Imperativo formal 'Invente' (usted); fragmento de formulario sin marcadores."),

    # --- pos 138 ---
    (3613, "A", None, None, [], [], [],
     "Tercera persona académico/abstracto; 'facultades de derecho' / 'escuelas de leyes' son glosas distintas del traductor."),

    # --- pos 139 ---
    (4414, "A", None, None, [], [], [],
     "Tercera persona abstracto; sin marcadores."),

    # --- pos 140 ---
    (361, "C",
     "Si fuera un ápice, tenés que hacer algunos ajustes en el regulador.",
     None,
     ["tienes → tenés (voseo)"],
     [], [],
     "Voseo en 2ª singular ('tenés'); 'tu traje' en hyp es posesivo invariante entre tuteo y voseo."),

    # --- pos 141 ---
    (2574, "A", None, None, [], [], [],
     "Subjuntivo 'hagas' aceptable en RP escrito (la regla del prompt aplica el voseo a indicativo e imperativo, no al subjuntivo). Consistente con held-out 70 idx 1915."),

    # --- pos 142 ---
    (4526, "B",
     "Y simpatizo con su comentario en la página 19: La Primera Ley de la autoría de Brunner: En cualquier cuerpo de texto hay por lo menos un error que su autor leyó directamente más allá de tres veces.",
     None,
     ["ha leído → leyó (PPC → pretérito simple RP, marcador temporal puntual 'tres veces' — vía 2)"],
     ["cambio_PPC"], [],
     "Caso explícitamente listado en el prompt v1 como ejemplo de vía 2 (marcador temporal puntual cerrado obliga a aplicar el cambio aun en registro formal/escrito)."),

    # --- pos 143 ---
    (4279, "A", None, None, [], [], [],
     "Imperativo formal usted ('tenga en cuenta'); registro institucional."),

    # --- pos 144 ---
    (3894, "A", None, None, [], [], [],
     "'Usted' formal explícito; sin marcadores 2ª singular informal."),

    # --- pos 145 ---
    (652, "A", None, None, [], [], [],
     "Tercera plural; 'níquel' como moneda de 5 centavos EE.UU. es traducción literal del traductor, no peninsularismo del listado."),

    # --- pos 146 ---
    (2182, "C",
     None,
     "Podés comprarlos y hacer un techo.",
     ["Puedes → Podés (voseo)"],
     [], [],
     "Voseo en hyp; el prem usa 'Puede' usted formal que se mantiene."),

    # --- pos 147 ---
    (4490, "A", None, None, [], [], [],
     "Tercera persona; sin marcadores."),

    # --- pos 148 ---
    (355, "C",
     "Sabés, no podés, no podés sobrevivir si no tenés ninguna contrapresión, aumento de presión de respiración en esas alturas.",
     "Necesitás una contrapresión  superior a 5000 pies.",
     ["Sabes → Sabés (voseo)",
      "puedes → podés (voseo)",
      "tienes → tenés (voseo)",
      "Necesitas → Necesitás (voseo)",
      "conntrapresión → contrapresión (corrección de typo del ES)"],
     ["correccion_typo"], [],
     "Voseo dominante (4 cambios C); además se corrige el typo 'conntrapresión' en hyp (registrado como secundario). Doble espacio del ES se preserva (no se toca puntuación/espaciado)."),

    # --- pos 149 ---
    (485, "B",
     None,
     "La señora Faulk manejaba un Honda amarillo todos los días para ir a trabajar.",
     ["conducía → manejaba (léxico peninsular → RP)"],
     [], [],
     "Sustitución léxica obligatoria: 'conducir' es marcador peninsular fuerte para vehículos, RP usa 'manejar'. Cf. held-out 70 idx 2500."),

    # --- pos 150 ---
    (2819, "A", None, None, [], [], [],
     "Registro técnico 3ª persona; sin marcadores."),

    # --- pos 151 ---
    (3131, "A", None, None, [], [], [],
     "Tercera persona; sin marcadores. Hyp tiene un calco curioso ('Ashcroft fue interesante') pero es problema sintáctico de la traducción, no error de palabra puntual (no es D)."),

    # --- pos 152 ---
    (428, "A", None, None, [], [], [],
     "1ª persona; 'Pues' como muletilla aceptable en RP coloquial."),

    # --- pos 153 ---
    (3389, "A", None, None, [], [], [],
     "Forma 'véase' panhispánica de cita académica."),

    # --- pos 154 ---
    (2069, "A", None, None, [], [], [],
     "Tercera persona histórica; sin marcadores."),

    # --- pos 155 ---
    (2463, "A", None, None, [], [], [],
     "Tercera persona; sin marcadores."),

    # --- pos 156 ---
    (772, "C",
     "sabés que es fácil decir bueno construiremos un agujero de cemento y no pasará nada y después dirán bueno la única manera de probarlo es durante un largo periodo así que",
     None,
     ["sabes → sabés (voseo)"],
     [], [],
     "Voseo en 'sabés' inicial; resto del prem es 1ª/3ª plural sin marcadores."),

    # --- pos 157 ---
    (1933, "A", None, None, [], [], [],
     "1ª/3ª persona narrativa; sin marcadores."),

    # --- pos 158 ---
    (1050, "A", None, None, [], [], [],
     "Registro técnico-físico 3ª persona; sin marcadores."),

    # --- pos 159 ---
    (1939, "C",
     "Me pregunto, ahora, dijo en breve, si la jugarreta está funcionando en vos.",
     "Él cuestionó si los actos maliciosos fueron causados por vos o no.",
     ["en ti → en vos (pronombre tónico tuteo → voseo)",
      "por ti → por vos (pronombre tónico tuteo → voseo)"],
     [], [],
     "Pronombres tónicos preposicionales; ambos cambian a 'vos' en RP."),

    # --- pos 160 ---
    (3, "A", None, None, [], [], [],
     "1ª persona; 'yo' enfático no se elimina (regla pronombres sujeto del prompt v1)."),

    # --- pos 161 ---
    (1140, "C",
     None,
     "Omnes dijo que podés ver todo.",
     ["puedes → podés (voseo)"],
     [], [],
     "Voseo en hyp; 'punto de ataque' como traducción de 'striking point' es glosa válida del traductor (no D — paráfrasis aceptable)."),

    # --- pos 162 ---
    (2774, "A", None, None, [], [], [],
     "Registro técnico-financiero 3ª persona; sin marcadores."),

    # --- pos 163 ---
    (2843, "A", None, None, [], [], [],
     "Registro técnico-estadístico 3ª persona; sin marcadores."),

    # --- pos 164 ---
    (4198, "A", None, None, [], [], [],
     "Tercera persona abstracto; sin marcadores."),

    # --- pos 165 ---
    (1616, "C",
     "Podés estar en lo cierto, y podés estar equivocado.",
     "Podés estar equivocado, pero también es posible que estés en lo cierto",
     ["Puedes → Podés (voseo)",
      "puedes → podés (voseo)"],
     [], [],
     "Voseo múltiple; 'estés' subjuntivo se mantiene como forma estándar (regla v1: voseo no aplica al subjuntivo escrito)."),

    # --- pos 166 ---
    (4738, "D",
     "Sin esta explicación, la información de que surname viene del francés surnom me resulta de poco interés.",
     None,
     ["fránces → francés (corrección de typo: tilde mal posicionada)"],
     [], [],
     "Typo del ES original (tilde sobre la 'a' en lugar de la 'e'). 'surname' y 'surnom' se preservan porque son menciones metalingüísticas (la oración HABLA SOBRE las palabras), no usos."),

    # --- pos 167 ---
    (1405, "A", None, None, [], [], [],
     "Tercera persona histórica; nombre propio mexicano se preserva."),

    # --- pos 168 ---
    (736, "A", None, None, [], [], [],
     "1ª/3ª persona pretérito + imperfecto; sin marcadores 2ª persona."),

    # --- pos 169 ---
    (2530, "A", None, None, [], [], [],
     "Registro técnico 3ª persona; sin marcadores."),

    # --- pos 170 ---
    (3981, "C",
     "Por consiguiente, sé que te esforzás mucho para ser compasivo y cariñoso con otros.",
     None,
     ["te esfuerzas → te esforzás (voseo)"],
     [], [],
     "Voseo en 'esforzás' (acentuación); en hyp 'te importa'/'te rodea' son 3ª persona del verbo + clítico, invariantes entre tuteo y voseo."),

    # --- pos 171 ---
    (3728, "A", None, None, [], [], [],
     "Tercera persona histórica; sin marcadores."),

    # --- pos 172 ---
    (4495, "D",
     None,
     "Rusia no está segura de cómo actuar.",
     ["esta → está (corrección de tilde faltante en verbo 'estar')",
      "como → cómo (corrección de tilde faltante en interrogativa indirecta)"],
     [], [],
     "Dos tildes obligatorias faltantes en el ES; ambas son typos puros (no son tildes diacríticas obsoletas tipo 'éste/sólo' que sí se mantienen). Patrón análogo al gold idx 3440."),

    # --- pos 173 ---
    (1355, "A", None, None, [], [], [],
     "Tercera plural abstracto; sin marcadores."),

    # --- pos 174 ---
    (4018, "A", None, None, [], [], [],
     "Tercera persona pretérito/condicional; sin marcadores."),

    # --- pos 175 ---
    (3002, "A", None, None, [], [], [],
     "Registro técnico-corporativo 3ª persona; sin marcadores."),

    # --- pos 176 ---
    (4399, "A", None, None, [], [], [],
     "Tercera persona pretérito; sin marcadores."),

    # --- pos 177 ---
    (3416, "A", None, None, [], [], [],
     "Tercera persona/plural impersonal; sin marcadores."),

    # --- pos 178 ---
    (4517, "A", None, None, [], [], [],
     "1ª/3ª persona narrativa. 'un botella' es error de concordancia de género del ES — explícitamente NO D según el prompt v1 ('NO es D: concordancia número/persona')."),

    # --- pos 179 ---
    (632, "C",
     "era de Wills Point, no sé si lo sabés",
     None,
     ["sabes → sabés (voseo)"],
     [], [],
     "Voseo en 'sabés' final."),

    # --- pos 180 ---
    (2040, "A", None, None, [], [], [],
     "Tercera plural; sin marcadores."),

    # --- pos 181 ---
    (1610, "A", None, None, [], [], [],
     "Tercera persona narrativa; sin marcadores."),

    # --- pos 182 ---
    (2114, "A", None, None, [], [], [],
     "Tercera persona descriptivo turístico; 'submarinismo' aceptable en RP en registro técnico-deportivo (no está en lista obligatoria)."),

    # --- pos 183 ---
    (4147, "A", None, None, [], [], [],
     "Tercera persona; 'Nearly Everything' sin traducir en prem y 'Casi Todo' en hyp son glosas distintas del traductor (no se busca consistencia léxica entre prem y hyp; tampoco aplica D porque no es UN error puntual)."),

    # --- pos 184 ---
    (2840, "D",
     "Primero, usamos el volumen per cápita para cada país para aproximar piezas por parada posible.",
     None,
     ["por capital → per cápita (corrección de error de traducción: 'per capita' confundido con 'capital')"],
     [], [],
     "El ES traduce el latinismo 'per capita' como 'por capital' (calco erróneo); la corrección preserva el sentido técnico y no altera la relación con el hyp."),

    # --- pos 185 ---
    (3076, "A", None, None, [], [], [],
     "Tercera persona; siglas (PAPD, ESU) preservadas."),

    # --- pos 186 ---
    (4179, "A", None, None, [], [], [],
     "Tercera persona; nombre propio (Slate) preservado."),

    # --- pos 187 ---
    (150, "A", None, None, [], [], [],
     "1ª persona presente; sin marcadores 2ª."),

    # --- pos 188 ---
    (1371, "A", None, None, [], [], [],
     "Tercera persona histórico-descriptivo; sin marcadores."),

    # --- pos 189 ---
    (3663, "A", None, None, [], [], [],
     "'Puede esperar' usted formal (registro de invitación institucional); sin marcadores 2ª informal."),

    # --- pos 190 ---
    (3990, "C",
     "Por favor, da ahora para que podamos seguir dándote a vos, a tus amigos y a tus vecinos.",
     None,
     ["a ti → a vos (pronombre tónico tuteo → voseo)"],
     [], [],
     "Solo se cambia el pronombre tónico ('a ti' → 'a vos'); 'da' (imperativo monosílabo de 'dar') se mantiene sin tilde según norma RAE; posesivos 'tus' y clítico 'te' (en 'dándote') son invariantes entre tuteo y voseo."),

    # --- pos 191 ---
    (2242, "A", None, None, [], [], [],
     "Tercera persona narrativa; 'había comido' pluscuamperfecto, no PPC; sin marcadores."),

    # --- pos 192 ---
    (4555, "A", None, None, [], [], [],
     "Tercera persona impersonal formal; sin marcadores."),

    # --- pos 193 ---
    (2691, "A", None, None, [], [], [],
     "Registro técnico-médico 3ª persona; sin marcadores."),

    # --- pos 194 ---
    (941, "A", None, None, [], [], [],
     "1ª persona; 'pues' aceptable como muletilla en RP."),

    # --- pos 195 ---
    (2464, "A", None, None, [], [], [],
     "Tercera persona; sin marcadores."),

    # --- pos 196 ---
    (1543, "A", None, None, [], [], [],
     "Tercera persona narrativa; 'sábanas de popa' como traducción de 'stern sheets' es elección léxica del traductor (no es UN error puntual confirmado por la otra parte; aplica regla de abstención del prompt v1)."),

    # --- pos 197 ---
    (2809, "A", None, None, [], [], [],
     "Registro institucional 3ª plural formal; sin marcadores."),

    # --- pos 198 ---
    (3158, "A", None, None, [], [], [],
     "Forma 'véase' panhispánica de cita académica."),

    # --- pos 199 ---
    (4480, "A", None, None, [], [], [],
     "'Estás' coincide ortográficamente entre tuteo y voseo (presente indicativo de 'estar', forma 'tú estás' = 'vos estás'); sin marcadores diferenciables."),
]


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def already_processed(path: Path) -> set[int]:
    if not path.exists():
        return set()
    done = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            done.add(json.loads(line)["idx"])
        except Exception:
            pass
    return done


def main() -> int:
    all_500 = load_jsonl(INPUT_500)
    by_idx = {r["idx"]: r for r in all_500}

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    done_idxs = already_processed(OUTPUT)
    if done_idxs:
        print(f"Reanudando: {len(done_idxs)} idx ya procesados, se saltean.")

    pending = [a for a in ANNOTATIONS if a[0] not in done_idxs]
    if not pending:
        print("Nada por hacer; todas las anotaciones ya están en disco.")
        return 0

    pbar = tqdm(total=len(pending), desc="Anotando")
    written = 0
    with OUTPUT.open("a", encoding="utf-8") as f:
        for (idx, type_, prem_rp, hyp_rp, changes, secondary_features,
             cultural_candidates, note) in pending:
            src = by_idx.get(idx)
            if src is None:
                print(f"WARN: idx {idx} no está en el 500; saltando.", file=sys.stderr)
                pbar.update(1)
                continue
            prem_es = src["prem_es"]
            hyp_es = src["hyp_es"]
            final_prem_rp = prem_es if prem_rp is None else prem_rp
            final_hyp_rp = hyp_es if hyp_rp is None else hyp_rp

            row = {
                "idx": idx,
                "label": src["label"],
                "label_int": src["label_int"],
                "prem_en": src["prem_en"],
                "hyp_en": src["hyp_en"],
                "prem_es": prem_es,
                "hyp_es": hyp_es,
                "prem_rp": final_prem_rp,
                "hyp_rp": final_hyp_rp,
                "type": type_,
                "changes": changes,
                "lev_prem": Levenshtein.distance(prem_es, final_prem_rp),
                "lev_hyp": Levenshtein.distance(hyp_es, final_hyp_rp),
                "lev_total": (Levenshtein.distance(prem_es, final_prem_rp)
                              + Levenshtein.distance(hyp_es, final_hyp_rp)),
                "secondary_features": secondary_features,
                "cultural_candidates": cultural_candidates,
                "note": note,
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            written += 1
            pbar.update(1)
    pbar.close()
    print(f"Escritas {written} filas nuevas en {OUTPUT}.")

    rows = load_jsonl(OUTPUT)
    dist = {"A": 0, "B": 0, "C": 0, "D": 0}
    for r in rows:
        dist[r["type"]] = dist.get(r["type"], 0) + 1
    print(f"\nDistribución por tipo en {OUTPUT.name} ({len(rows)} total):")
    for t, n in dist.items():
        if n:
            print(f"  {t}: {n} ({n/len(rows)*100:.1f}%)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
