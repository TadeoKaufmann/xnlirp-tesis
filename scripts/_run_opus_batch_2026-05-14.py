"""One-shot: adapta 126 instancias del batch 2026-05-14 a RP.
Las adaptaciones están escritas inline por Opus (esta sesión).
Output: data/processed/opus_batch_2026-05-14_translated.jsonl
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / "data/processed/opus_batch_2026-05-14.jsonl"
OUTPUT = ROOT / "data/processed/opus_batch_2026-05-14_translated.jsonl"

# Cargo el batch original para extraer prem_es, hyp_es, label y metadata por idx
src_by_idx = {}
with INPUT.open(encoding="utf-8") as f:
    for line in f:
        d = json.loads(line)
        src_by_idx[d["idx"]] = d


def make(idx, prem_rp, hyp_rp, type_, changes, note,
         secondary_features=None, cultural_candidates=None,
         review_flag=False, review_note=None,
         replaced_original=False, replacement_rationale=None):
    src = src_by_idx[idx]
    return {
        "idx": idx,
        "label": src["label"],
        "prem_es": src["prem_es"],
        "hyp_es": src["hyp_es"],
        "prem_rp": prem_rp,
        "hyp_rp": hyp_rp,
        "type": type_,
        "changes": list(changes),
        "secondary_features": list(secondary_features or []),
        "cultural_candidates": list(cultural_candidates or []),
        "review_flag": review_flag,
        "review_note": review_note,
        "replaced_original": replaced_original,
        "replacement_rationale": replacement_rationale,
        "_matched_terms": src.get("_matched_terms", []),
        "_categories": src.get("_categories", []),
        "note": note,
    }


# ---------------------------------------------------------------------------
# GRUPOS POR PREMISA COMPARTIDA
# ---------------------------------------------------------------------------

# G1) idx 21, 23 — premisa entera en inglés (anglicismo masivo, D)
santo_prem_rp = ("Michael Santo, de Firewell and Company, de Buffalo, NY, fue el que, "
                 "este..., fabricó, este..., inventó el regulador de O2 alto antes de que "
                 "construyeran el control de fuego en la estufa.")
g1 = [
    make(21, santo_prem_rp,
         "Santo vivió en Nueva York y trabajó en el alto regulador de O2.",
         "D",
         ["premisa entera en inglés sin traducir → traducción al castellano RP (D masivo)",
          "uh → este... (muletilla de hesitación anglófona)"],
         "Premisa íntegramente en EN en el ES original; traducida al castellano RP. Firewell and Company y Buffalo NY se mantienen como nombres propios.",
         review_flag=True,
         review_note="Premisa original íntegramente en inglés; reescrita en castellano RP. 'fire control on the stove well' es ambiguo en el EN (fragmento de habla rota); se interpretó como 'control de fuego en la estufa'. Verificar interpretación."),
    make(23, santo_prem_rp,
         "Santo trabajó para Disney y operó las tazas de té.",
         "D",
         ["premisa entera en inglés sin traducir → traducción al castellano RP (D masivo)",
          "uh → este..."],
         "Mismo prem_rp que idx 21 (consistencia por compartir prem). Hyp en RP estándar.",
         review_flag=True,
         review_note="Premisa original íntegramente en inglés; reescrita en castellano RP."),
]

# G2) idx 102, 104 — Kennedy/Cuba (muletillas)
kennedy_prem_rp = ("Bueno, al día siguiente, por supuesto, el presidente Kennedy, este..., "
                   "bloqueó Cuba y, este..., nuestros buques detuvieron un barco ruso que se "
                   "dirigía a las afueras de Cuba y encontraron misiles.")
g2 = [
    make(102, kennedy_prem_rp,
         "Kennedy le dijo a nuestras tropas que buscaran misiles.",
         "B",
         ["mm... → este... (muletilla de hesitación anglófona)",
          "mmm... → este... (idem, para no duplicar 'mmm' y 'este...' en la misma oración)"],
         "Dos muletillas 'mm/mmm' adaptadas a 'este...' (RP); Cuba/Kennedy se mantienen (referentes históricos reales)."),
    make(104, kennedy_prem_rp,
         "Encontraron 20 misiles en el barco.",
         "B",
         ["mm... → este...",
          "mmm... → este..."],
         "Idem idx 102 con hyp distinta."),
]

# G3) idx 198, 199, 200 — Rudolph Anderson/Cuba (A)
anderson_prem_rp = "Fue desde una base aérea que pasaba sobre Cuba, y por supuesto derribaron a Rudolph Anderson."
g3 = [
    make(198, anderson_prem_rp, "Todos los aviones sobrevivieron sin que les dispararan.",
         "A", [], "Cuba/Rudolph Anderson son referentes históricos reales (Crisis de los Misiles, 1962); se mantienen."),
    make(199, anderson_prem_rp, "Algo fue derribado en Cuba.",
         "A", [], "Idem; sin cambios dialectales necesarios."),
    make(200, anderson_prem_rp, "El enorme avión fue derribado sobre Cuba en mayo.",
         "A", [], "Idem."),
]

# G4) idx 222, 223 — Crisis de Cuba/Kaiser
crisis_prem_rp = ("Fue la única baja de la Crisis de Cuba y, eh, Kaiser, eh, consiguió las "
                  "imágenes y voló directo a Andrews Air Force en Washington.")
g4 = [
    make(222, crisis_prem_rp, "10 000 personas murieron en la crisis cubana.",
         "B",
         ["se hizo con las imágenes → consiguió las imágenes ('hacerse con' es peninsular)"],
         "'Hacerse con algo' es marcador peninsular; 'consiguió' es la equivalencia RP natural. 'eh' se mantiene (es idéntico en RP)."),
    make(223, crisis_prem_rp, "Solo una persona murió en la crisis cubana.",
         "B",
         ["se hizo con las imágenes → consiguió las imágenes"],
         "Idem idx 222."),
]

# G5) idx 549, 550, 551 — McKim arquitecto histórico (A)
mckim1_prem_rp = "McKim, para su disgusto, no solo perdió, sino que quedó tercero detrás de Howard y Cauldwell."
g5 = [
    make(549, mckim1_prem_rp, "Howard y Cauldwell eran mujeres.",
         "A", [], "Charles Follen McKim (1847-1909), arquitecto histórico real (McKim, Mead & White). Antropónimos se mantienen. Texto neutral en RP."),
    make(550, mckim1_prem_rp, "McKim estaba muy feliz porque terminó primero.",
         "A", [], "Idem; sin cambios dialectales."),
    make(551, mckim1_prem_rp, "McKim fue humillado porque terminó tercero.",
         "A", [], "Idem."),
]

# G6) idx 657, 658 — Los Pastores/Guadalupe (D typo)
pastores_prem_rp = "En San Antonio la actuación de Los Pastores en la iglesia de Nuestra Señora de Guadalupe está presente desde 1913."
g6 = [
    make(657, pastores_prem_rp, "La representación nunca se hace en San Antonio.",
         "D",
         ["Pasores → Pastores (typo)",
          "señora → Señora (capitalización en advocación mariana)"],
         "'Los Pasores' es typo claro por 'Los Pastores' (auto litúrgico). 'Nuestra Señora de Guadalupe' va con mayúscula. Topónimo religioso se mantiene."),
    make(658, pastores_prem_rp, "El rendimiento se detuvo en 1987.",
         "D",
         ["Pasores → Pastores", "señora → Señora"],
         "Idem idx 657."),
]

# G7) idx 1023, 1024, 1025 — Sant Pau/Barcelona (A)
santpau_prem_rp = ("La simplicidad de las líneas románicas de Sant Pau, representa un cambio "
                   "agradable de la extravagancia del modernismo de Barcelona y la complejidad "
                   "de la arquitectura gótica.")
g7 = [
    make(1023, santpau_prem_rp, "Sant Pau no tiene líneas románicas.",
         "A", [], "Topónimos catalanes (Sant Pau, Barcelona) se mantienen. Texto formal/descriptivo neutral en RP."),
    make(1024, santpau_prem_rp, "Sant Pau tiene líneas románicas.",
         "A", [], "Idem."),
    make(1025, santpau_prem_rp, "Sant Pau tiene iglesias.",
         "A", [], "Idem."),
]

# G8) idx 1098, 1099, 1100 — pachuca/Chicana (A)
pachuca1_prem_rp = ("La pachuca era la contraparte del pachuco de la década de 1940, pero "
                    "también el arquetipo de la chica de barrio que se reúne en la Chicana y "
                    "crece en un ambiente urbano tipo gueto.")
g8 = [
    make(1098, pachuca1_prem_rp, "Pachucas eran bicicletas.",
         "A", [], "Pachuca/pachuco/Chicana son referentes culturales mexicano-estadounidenses específicos; no tienen equivalente AR y se mantienen."),
    make(1099, pachuca1_prem_rp, "Pachucas eran jóvenes Chicanas.",
         "A", [], "Idem; 'jóvenes Chicanas' refiere a edad menor pero acá funciona como noun phrase del grupo cultural — se mantiene."),
    make(1100, pachuca1_prem_rp, "Pachucas llevó mucho maquillaje.",
         "A", [], "Idem."),
]

# G9) idx 1137, 1138, 1139 — McKim Mead (A)
mckim2_prem_rp = "Desvío para ver la mansión diseñada por McKim Mead"
g9 = [
    make(1137, mckim2_prem_rp, "McKim Mead diseñó la mansión.",
         "A", [], "McKim Mead se refiere a la firma McKim, Mead & White (arquitectos históricos). Mantener."),
    make(1138, mckim2_prem_rp, "Construir la mansión cuesta 2 millones de dólares.",
         "A", [], "Idem."),
    make(1139, mckim2_prem_rp, "La mansión fue construída por Adam Sandler.",
         "A", [], "'construída' es variante ortográfica pre-2010 con tilde; no se corrige (cae en 'variantes ortográficas' que no son D)."),
]

# G10) idx 1152, 1153, 1154 — Montserrat (B: simplificar paréntesis con millas)
montserrat_prem_rp = ("Las escarpadas crestas de Montserrat surgen de la llanura sin rasgos "
                      "distintivos del Llobregat 62 kilómetros al noroeste de Barcelona, en el "
                      "corazón de Cataluña.")
g10 = [
    make(1152, montserrat_prem_rp, "Montesserant es un río.",
         "B",
         ["'62 kilómetros (38 millas)' → '62 kilómetros' (se elimina el paréntesis redundante con millas; el km ya es la unidad RP estándar)"],
         "Topónimos catalanes se mantienen; la unidad imperial parentética se elimina como cambio B menor (en RP no se ofrece la conversión a millas)."),
    make(1153, montserrat_prem_rp, "El Montserrat son montañas.",
         "B",
         ["'62 kilómetros (38 millas)' → '62 kilómetros'"],
         "Idem."),
    make(1154, montserrat_prem_rp, "Las montañas de Mountesserat son las más altas de la zona.",
         "B",
         ["'62 kilómetros (38 millas)' → '62 kilómetros'"],
         "Idem."),
]

# G11) idx 1158, 1159, 1160 — Paseo de Gracia (D múltiple: inglés sin traducir + typos)
paseo_prem_rp = ("Mirá el Paseo de Gracia al este, especialmente las calles Diputació, Consejo "
                 "de Ciento, Mallorca, y València hasta el mercado Mercat de la Concepció.")
g11 = [
    make(1158, paseo_prem_rp, "El mercado se llama Mercat de la Cantaloupe",
         "D",
         ["'Have a look at ... to the east' → 'Mirá ... al este' (frase inglesa sin traducir)",
          "'and' → 'y' (anglicismo sin traducir)",
          "'as faro as' → 'hasta' (anglicismo + typo 'faro'→'far')",
          "ValÃ¨ncia → València (encoding garbled)",
          "Concepcie → Concepció (typo del topónimo catalán)"],
         "Premisa con encoding corrupto y fragmentos en inglés sin traducir. Se restauró ortografía catalana de topónimos (Diputació, València, Concepció) y se tradujo el inglés.",
         review_flag=True,
         review_note="Premisa original mezcla EN y ES con encoding roto; reescrita preservando topónimos catalanes y registro descriptivo. Verificar consistencia ortográfica catalana."),
    make(1159, paseo_prem_rp, "El mercado vende muchas frutas y verduras.",
         "D",
         ["traducción de fragmentos en inglés", "restauración de topónimos catalanes (encoding)"],
         "Idem.",
         review_flag=True,
         review_note="Idem idx 1158."),
    make(1160, paseo_prem_rp, "Hay un mercado llamado Mercat de la Concepció.",
         "D",
         ["traducción de fragmentos en inglés", "restauración de topónimos catalanes (encoding)"],
         "Idem.",
         review_flag=True,
         review_note="Idem idx 1158."),
]

# G12) idx 1186, 1187 — Le Corbusier/Gehry (A)
gehry1_prem_rp = "El plan es el generador, proclamó Le Corbusier. Pero con Gehry, el plan es el resultado."
g12 = [
    make(1186, gehry1_prem_rp, "El plan no es importante",
         "A", [], "Le Corbusier y Frank Gehry son arquitectos reales famosos; se mantienen."),
    make(1187, gehry1_prem_rp, "El plan es invadir un país.",
         "A", [], "Idem."),
]

# G13) idx 1240 — China/Cuba (A)
g13 = [
    make(1240,
         "La cocina china aterriza en Cuba, y se inventa la cocina cubano-china.",
         "La comida china solo se encuentra en China",
         "A", [], "Cuba como referente histórico/gastronómico real; mantener."),
]

# G14) idx 1296, 1297, 1298 — Gehry (A)
gehry2_prem_rp = "Esta es la manera en la que vivimos hoy. Gehry parece estar diciendo, ¿por qué no la disfrutamos?"
g14 = [
    make(1296, gehry2_prem_rp, "A Gehry no le importa la felicidad.",
         "A", [], "Frank Gehry, arquitecto real. Mantener."),
    make(1297, gehry2_prem_rp, "Gehry es una persona feliz.",
         "A", [], "Idem."),
    make(1298, gehry2_prem_rp, "Gehry parece decir disfrutar de la vida.",
         "A", [], "Idem."),
]

# G15) idx 1314, 1315, 1316 — pachuca (A)
pachuca2_prem_rp = "Las pachucas eran las novias de los pachucos, pero también tenían un estilo de vestir propio."
g15 = [
    make(1314, pachuca2_prem_rp, "Pachucas no conocía pachucos.",
         "A", [], "Pachuca/pachuco son referentes culturales chicanos sin equivalente AR."),
    make(1315, pachuca2_prem_rp, "Pachucas conocía a pachucos.",
         "A", [], "Idem."),
    make(1316, pachuca2_prem_rp, "Las Pachucas llevaban más ropas que los Pachucos.",
         "A", [], "Idem."),
]

# G16) idx 1359, 1361 — química exergónica (A — texto técnico formal)
hex_prem_rp = ("Si se le deja con sus propios recursos, esta reacción es exergónica y, en "
               "presencia de trímeros en exceso en comparación con la relación de equilibrio "
               "de hexámero a trímeros, fluirá exergéticamente hacia el equilibrio al "
               "sintetizar el hexámero.")
g16 = [
    make(1359, hex_prem_rp, "Si esta reacción no se toca, al final acabará en equilibrio.",
         "A", [], "Texto técnico formal de bioquímica; léxico estándar científico, sin marcadores peninsulares."),
    make(1361, hex_prem_rp, "Esta reacción, si no se interfiere, puede durar milenios.",
         "A", [], "Idem."),
]

# G17) idx 1404 — José Guadalupe Posada (A)
g17 = [
    make(1404,
         "El artista y grabador mexicano José Guadalupe Posada comenzó a dibujar calaveras a finales del siglo XIX para coincidir con esta festividad.",
         "José Guadalupe Posada comenzó a dibujar imágenes de edificios y ríos.",
         "A", [], "José Guadalupe Posada, artista mexicano histórico real (1852-1913). Antropónimo se mantiene."),
]

# G18) idx 1421 — Richardson/McKim (A)
g18 = [
    make(1421,
         "H. H. Richardson y su protegido Charles Follen McKim fueron ex alumnos, así como los asistentes de McKim, John M. Carrare y Thomas Hastings.",
         "H. H. Richardson, Charles Follen McKim, John M. Carrare y Thomas Hastings fueron todos ex alumnos.",
         "A", [], "Arquitectos históricos reales; nombres propios se mantienen."),
]

# G19) idx 1428, 1429, 1430 — pachuco menospreciado (A)
pachuco3_prem_rp = ("El pachuco fue menospreciado en los EE. UU. por tanto los "
                    "mexicano-estadounidenses y las comunidades anglosajonas, y de igual "
                    "manera en México por los medios y los intelectuales.")
g19 = [
    make(1428, pachuco3_prem_rp,
         "En los Estados Unidos, los mexicoamericanos y los angloamericanos pensaban que el pachuco era indigno.",
         "A", [], "Pachuco como referente cultural chicano; 'por tanto los...y las...' es calco anglo de 'by both...and...' pero no es un error léxico aislado (es estructural), no aplica D. Mantener."),
    make(1429, pachuco3_prem_rp, "Pachuco fue adoptado en los Estados Unidos por los mexicoamericanos.",
         "A", [], "Idem."),
    make(1430, pachuco3_prem_rp, "El pachuco tuvo muchos efectos negativos.",
         "A", [], "Idem."),
]

# G20) idx 1476, 1477 — pachuco habla (A)
pachuco4_prem_rp = ("el pachuco, una combinación de inglés y español, también llamado caló, "
                    "fue una fascinante fusión proveniente de muchas fuentes lingüísticas.")
g20 = [
    make(1476, pachuco4_prem_rp,
         "Mucha gente hoy todavía habla una versión u otra versión de pachuco.",
         "A", [], "Pachuco como variedad lingüística; caló (jerga gitana/chicana) se mantiene. Sin marcadores peninsulares."),
    make(1477, pachuco4_prem_rp, "Los bloques de construcción del discurso pachuco son inglés y español.",
         "A", [], "Idem."),
]

# G21) idx 1527, 1528, 1529 — Pickard recuerda (A — formal biográfico)
pickard1_prem_rp = "Pickard recuerda la presunta aseveración que se hizo en una sesión informativa el 12 de julio."
g21 = [
    make(1527, pickard1_prem_rp, "Pickard no podía recordar nada de lo que habían dicho.",
         "A", [], "Thomas Pickard (ex-FBI director); registro formal biográfico, 'recuerda' se mantiene (no 'acordarse de'). Sin marcadores peninsulares."),
    make(1528, pickard1_prem_rp, "Pickard recordó que la sesión informativa cubría los hechos del accidente.",
         "A", [], "Idem."),
    make(1529, pickard1_prem_rp, "Pickard recordó lo que se dijo en el informe.",
         "A", [], "Idem."),
]

# G22) idx 2097, 2099 — Pynchon vida privada (A — PPC con estado vigente)
pynchon1_prem_rp = "Pynchon: Como corresponde a un hombre cauto, en lugar de alardear, Pynchon ha mantenido su vida privada en secreto."
g22 = [
    make(2097, pynchon1_prem_rp, "Se rumorea que Pynchon tiene un hijo y una hija.",
         "A", [], "Thomas Pynchon, escritor real famoso. 'ha mantenido' = PPC con estado resultante vigente (sigue manteniéndola en secreto); NO cambiar a pretérito simple."),
    make(2099, pynchon1_prem_rp,
         "Hay un famoso programa de televisión sobre la vida privada de Pynchon, que protagoniza el mismísimo Pynchon.",
         "A", [], "Idem."),
]

# G23) idx 2103, 2104, 2105 — Morrison/Pynchon (A — PPC estado vigente)
morrison_prem_rp = "Morrison se ha ganado el derecho a ser tan idiosincrático como, digamos, William Gaddis, Thomas Pynchon o William Faulkner."
g23 = [
    make(2103, morrison_prem_rp, "Gaddis y Pynchon no son tan idiosincráticos como Morrison.",
         "A", [], "Toni Morrison, autora real; 'se ha ganado el derecho' = estado vigente, MANTENER PPC."),
    make(2104, morrison_prem_rp, "Morrison ha trabajado muy duro para ganarse el derecho de ser idiosincrásico.",
         "A", [], "Idem; 'idiosincrásico' es variante atestiguada, no es typo D."),
    make(2105, morrison_prem_rp, "Morrison puede ser tan idiosincrático como William Gaddis.",
         "A", [], "Idem."),
]

# G24) idx 2118, 2119, 2120 — Jazz Bakery LA (A — nombres propios)
jazz_prem_rp = ("Entre los muchos clubes de jazz están el famoso Jazz Bakery en Culver City, "
                "el Catalina Bar and Grill en Hollywood, y el Baked Potato en North Hollywood.")
g24 = [
    make(2118, jazz_prem_rp, "No hay clubs de jazz famosos en Los Ángeles.",
         "A", [], "Nombres propios de clubes (Jazz Bakery, Catalina Bar and Grill, Baked Potato); 'and' adentro de nombre propio no es anglicismo, mantener."),
    make(2119, jazz_prem_rp, "En Los Ángeles hay varios clubes de jazz famosos.",
         "A", [], "Idem."),
    make(2120, jazz_prem_rp, "No hay muchos clubes de jazz en Los Ángeles.",
         "A", [], "Idem."),
]

# G25) idx 2187, 2189 — Cuba trópicos (A — literario)
cuba_trop_prem_rp = "Entonces, también en los trópicos cubanos, acaba de haber un día tan bello como la gloria, frío como la tumba."
g25 = [
    make(2187, cuba_trop_prem_rp, "Cuba está en el Ártico.",
         "A", [], "Texto literario; sin marcadores peninsulares."),
    make(2189, cuba_trop_prem_rp, "Siempre está por encima de 80 en Cuba.",
         "A", [], "Idem."),
]

# G26) idx 2211, 2212 — Noske/Freikorps (D estructural + B "de derechas")
noske_prem_rp = ("El implacable ministro de defensa Gustav Noske llamó a 4000 Freikorps "
                 "(soldados de asalto de derecha) para reventar el movimiento.")
g26 = [
    make(2211, noske_prem_rp, "Noske quiso que el movimiento se detuviera antes de perder el poder.",
         "D",
         ["'La defensa implacable del ministro Gustav Noske' → 'El implacable ministro de defensa Gustav Noske' (error estructural de traducción: 'defense minister' como sustantivo, no como genitivo de defense)",
          "de derechas → de derecha (peninsular plural → singular RP)"],
         "Error D estructural: el ES traduce 'ruthless defense minister' como si 'defense' fuera el sustantivo principal modificado por 'minister'. Hyps confirman que el sujeto es Noske (ministro), no la 'defensa'. Secondary B: 'de derechas' → 'de derecha'.",
         secondary_features=["leximo_B: de derechas → de derecha"]),
    make(2212, noske_prem_rp, "Noske quería que las cosas continuaran de inmediato.",
         "D",
         ["'La defensa implacable del ministro' → 'El implacable ministro de defensa'",
          "de derechas → de derecha"],
         "Idem idx 2211.",
         secondary_features=["leximo_B: de derechas → de derecha"]),
]

# G27) idx 2244, 2245, 2246 — Skeat sesenta (A)
skeat1_prem_rp = "Cuando llegó a los sesenta años, en 1895, Skeat dio la impresión de que estaba empezando a tomarse menos en serio estos asuntos"
g27 = [
    make(2244, skeat1_prem_rp, "Cuando Skeat cumplió los sesenta, no dio señales de que estaba pensando en nada.",
         "A", [], "Walter William Skeat, filólogo británico real (1835-1912). Texto biográfico/literario formal; sin marcadores peninsulares."),
    make(2245, skeat1_prem_rp, "A medida que Skeat creció, tuvo la sensación de que se tomaba estos asuntos menos.",
         "A", [], "Idem."),
    make(2246, skeat1_prem_rp, "Skeat comenzó a preocuparse por diferentes cosas a medida que envejecía.",
         "A", [], "Idem."),
]

# G28) idx 2328, 2330 — Olimpiadas Barcelona (A)
olimp_prem_rp = "Las Olimpiadas de 1992 sentaron las bases de la reputación de Barcelona como una ciudad loca por el deporte."
g28 = [
    make(2328, olimp_prem_rp, "Los Juegos Olímpicos nunca se han celebrado en Europa.",
         "A", [], "Olimpiadas de Barcelona 1992 = evento histórico real; mantener."),
    make(2330, olimp_prem_rp, "Las olimpiadas fueron en España en 1992.",
         "A", [], "Idem."),
]

# G29) idx 2361, 2362, 2363 — bares marrones Holanda (D: "and" inglés)
bares_prem_rp = ("Les encanta socializar y los bares, especialmente los conocidos bares "
                 "marrones, son el lugar donde se reúnen, normalmente para arreglar los "
                 "problemas del mundo.")
g29 = [
    make(2361, bares_prem_rp, "Nunca salen con amigos, solo se quedan adentro solos.",
         "D",
         ["'y los and bares' → 'y los bares' (eliminación de 'and' anglicismo sin traducir)"],
         "El ES original tiene 'and' duplicado por residuo de traducción ('and bars' → 'y bares', pero quedó 'y los and bares'). Anglicismo sin traducir = D."),
    make(2362, bares_prem_rp, "Les gusta pasar el rato con la gente.",
         "D",
         ["'y los and bares' → 'y los bares'"],
         "Idem idx 2361."),
    make(2363, bares_prem_rp, "Les gusta hablar con la gente con la que trabajan.",
         "D",
         ["'y los and bares' → 'y los bares'"],
         "Idem."),
]

# G30) idx 2418, 2420 — Madrid colección Maestros (A)
madrid1_prem_rp = "La colección de Madrid de los Viejos Maestros españoles Velázquez, El Greco, Goya, Zurbarán y más no tiene rival en el mundo."
g30 = [
    make(2418, madrid1_prem_rp, "Madrid todavía no tiene una colección.",
         "A", [], "Topónimo (Museo del Prado en Madrid) y pintores históricos; texto formal museográfico, sin peninsularismos léxicos relevantes."),
    make(2420, madrid1_prem_rp, "La colección de Madrid contiene 500 piezas.",
         "A", [], "Idem."),
]

# G31) idx 2454, 2455, 2456 — Barcino-Barcelona película (A)
barcino_prem_rp = "Los visitantes también podrán ver una película multimedia de historia virtual de 28 minutos sobre Barcino-Barcelona."
g31 = [
    make(2454, barcino_prem_rp, "Barcino-Barcelona es el foco de una película multimedia de historia virtual.",
         "A", [], "Texto descriptivo/turístico neutral; topónimo se mantiene."),
    make(2455, barcino_prem_rp, "Lamentablemente, la película sobre Vincent Van Gogh no está disponible para los visitantes.",
         "A", [], "Idem."),
    make(2456, barcino_prem_rp, "Los visitantes en el Museo de Historia Natural pueden ver una película sobre Barcino-Barcelona.",
         "A", [], "Idem."),
]

# G32) idx 2478, 2479 — John Burke/Boswell (B: cotilleos → chismes)
burke_prem_rp = ("John Burke (Alabama) revisa y analiza otros relatos contemporáneos y "
                 "descubre que Boswell no solo es el más preciso, sino que lo utiliza para "
                 "demostrar el carácter de Johnson, mientras que otros simplemente vendían "
                 "chismes literarios.")
g32 = [
    make(2478, burke_prem_rp, "A John Burke no le agrada Boswell.",
         "B",
         ["cotilleos → chismes (peninsularismo léxico)"],
         "'Cotilleos' es marcador peninsular claro; 'chismes' es la equivalencia RP estándar. James Boswell/Samuel Johnson son figuras históricas reales (mantener)."),
    make(2479, burke_prem_rp, "John Burke ignora las cuentas.",
         "B",
         ["cotilleos → chismes"],
         "Idem idx 2478."),
]

# G33) idx 2583, 2584, 2585 — CIO externalizar (B: externalizar → tercerizar)
cio_prem_rp = ("El CIO y las autoridades responsables deciden qué tipo de trabajo es "
               "apropiado tercerizar y qué tipo de trabajo es mejor realizarlo internamente.")
g33 = [
    make(2583, cio_prem_rp, "El CIO dijo que solo el trabajo de interés público estaba bien.",
         "B",
         ["externalizar → tercerizar (calco anglo 'outsource' → forma RP estándar)"],
         "'Externalizar' es calco anglosajón; en AR/UY 'tercerizar' es la forma estándar empresarial. CIO se mantiene (sigla)."),
    make(2584, cio_prem_rp, "El Gerente dijo qué el trabajo estaba bien.",
         "B",
         ["externalizar → tercerizar"],
         "Idem; 'El Gerente' vs 'El CIO' en hyp es paráfrasis intencional del corpus (no D)."),
    make(2585, cio_prem_rp,
         "El CIO se mantuvo al margen de las discusiones sobre los trabajos que se permitían.",
         "B",
         ["externalizar → tercerizar"],
         "Idem."),
]

# G34) idx 2799, 2800, 2801 — externalizar 2
ext_prem_rp = ("Mirando hacia el futuro, alrededor de un tercio de las agencias que "
               "respondieron, informaron que están considerando tercerizar más funciones "
               "de revisión de diseño.")
g34 = [
    make(2799, ext_prem_rp, "Muchas agencias contemplan la idea de tercerizar funciones de revisión de diseño.",
         "B",
         ["externalizar → tercerizar"],
         "Hyp 2799 ya usaba 'tercerizar' (forma RP); prem se armoniza solo por la regla léxica, no por consistencia espuria."),
    make(2800, ext_prem_rp, "Ninguna agencia está considerando tercerizar funciones de revisión de diseño.",
         "B",
         ["externalizar → tercerizar (en prem y en hyp por aplicar la misma regla léxica B)"],
         "Misma regla B aplica a hyp ('externalizar' → 'tercerizar'). NLI contradiction preservada (un tercio vs ninguna)."),
    make(2801, ext_prem_rp, "Estas agencias tendrán diseños inferiores si subcontratan.",
         "B",
         ["externalizar → tercerizar (en prem; hyp ya usa 'subcontratan' que es válido en RP)"],
         "Solo prem cambia; hyp usa 'subcontratan' (válido también en RP). NLI neutral preservada."),
]

# G35) idx 2820, 2822 — Allenbrand-Drews/defensores → demandados (D)
defens_prem_rp = ("Además de LNL y Allenbrand-Drews, se nombra como demandados a Gary "
                  "Allenbrand y Loren Drews, directores de Allenbrand-Drews; y desarrolladores "
                  "o contratistas R.L.")
g35 = [
    make(2820, defens_prem_rp,
         "Allenbrand y Drews están siendo demandados por encarcelamiento falso.",
         "D",
         ["defensores → demandados (falso amigo jurídico inequívoco: 'defendants' ≠ 'defenders'; hyp confirma 'demandados')"],
         "D clásico: 'defendants' mal traducido como 'defensores'. La hyp usa 'demandados' (correcto). Se agrega 'a' por concordancia tras corrección."),
    make(2822, defens_prem_rp,
         "Allenbrand y Drews son los fiscales del caso.",
         "D",
         ["defensores → demandados (falso amigo jurídico)"],
         "Idem idx 2820."),
]

# G36) idx 3129, 3130 — Ashcroft/Pickard interés (A)
ashcr1_prem_rp = "Existe una disputa sobre el interés de Ashcroft en las reuniones informativas de Pickard sobre la situación de amenaza terrorista."
g36 = [
    make(3129, ashcr1_prem_rp, "Ashcroft dijo que las sesiones de información no valían la pena.",
         "A", [], "John Ashcroft (ex-AG EEUU) y Thomas Pickard (ex-FBI); figuras públicas reales. Registro formal biográfico. Sin marcadores peninsulares."),
    make(3130, ashcr1_prem_rp, "Ashcroft quería escuchar los informes una y otra vez.",
         "A", [], "Idem."),
]

# G37) idx 3255, 3256, 3257 — hawaladar Pakistán (A — jerga técnica extranjera)
hawal_prem_rp = ("El último receptor en Pakistán iría entonces al hawaladar pakistaní y "
                 "recibiría el dinero, en rupias, del dinero que el hawaladar pakistaní "
                 "tenga a mano.")
g37 = [
    make(3255, hawal_prem_rp, "El hawaladar paquistaní daría 5.000 rupias al receptor.",
         "A", [],
         "'Dinero' se MANTIENE en contexto de jerga técnica extranjera (hawaladar, rupias) — excepción explícita de la regla B."),
    make(3256, hawal_prem_rp, "El destinatario final sería pagado por el hawaladar paquistaní.",
         "A", [], "Idem."),
    make(3257, hawal_prem_rp, "El último destinatario tendría que viajar a Turquía para obtener su dinero.",
         "A", [], "Idem."),
]

# G38) idx 3447, 3449 — Pickard/Ashcroft relación (A)
pickard_ashcr_prem_rp = "Nos dijeron que Pickard y Ashcroft no tenían una buena relación."
g38 = [
    make(3447, pickard_ashcr_prem_rp, "Pickard y Ashcroft eran conocidos por ser muy buenos amigos.",
         "A", [], "Figuras públicas reales; texto biográfico neutral."),
    make(3449, pickard_ashcr_prem_rp,
         "Nunca podían ponerse de acuerdo sobre qué ingredientes colocar en la pizza en las reuniones del personal.",
         "A", [], "Idem."),
]

# G39) idx 3453, 3454, 3455 — FDNY/vídeo (B)
fdny_prem_rp = ("Para la llegada del jefe y las compañías, véase Jules Naudet y Gedeon Naudet, "
                "grabación de video, 11 de septiembre de 2001; Entrevista 4 de FDNY, Jefe (Jan.")
g39 = [
    make(3453, fdny_prem_rp, "El jefe llegó al sitio del WTC a las 10 am.",
         "B",
         ["vídeo → video (peninsular con tilde → RP sin tilde)"],
         "'Vídeo' con tilde es peninsular; 'video' sin tilde es la forma RP estándar. FDNY y nombres propios se mantienen (referente histórico real, 9/11)."),
    make(3454, fdny_prem_rp, "El jefe llegó al sitio.",
         "B", ["vídeo → video"],
         "Idem idx 3453."),
    make(3455, fdny_prem_rp, "El jefe nunca apareció.",
         "B", ["vídeo → video"],
         "Idem."),
]

# G40) idx 3711, 3712 — Rock 'n' Roll/FOREVER PLAID (A)
plaid_prem_rp = "Aunque el Rock 'n' Roll iba hacia abajo y sin frenos, FOREVER PLAID creía en su música."
g40 = [
    make(3711, plaid_prem_rp, "Sólo unos pocos adolescentes seguían escuchando Rock and Roll.",
         "A", [], "'Rock 'n' Roll' es nombre cultural fijo (igual que 'rock and roll'); el 'and/n' interno es parte del nombre, no anglicismo sin traducir."),
    make(3712, plaid_prem_rp,
         "El rock and roll crecía en popularidad, lo que hacía que miles de conciertos agotaran sus entradas.",
         "A", [], "Idem."),
]

# G41) idx 4008, 4009, 4010 — Lewinsky/Brit Hume (A)
lewinsky1_prem_rp = ("El amor lo vence todo (a menos que trabajes para el Weekly Standard): "
                     "Brit Hume (Fox News Sunday) especula sobre el porqué Lewinsky podría no... "
                     "Todavía tiene un enamoramiento sin esperanza con el presidente.")
g41 = [
    make(4008, lewinsky1_prem_rp, "Brit Hume es el reportero principal de Fox.",
         "A", [], "Mónica Lewinsky, Brit Hume, Fox News — figuras y medios reales. Texto formal/periodístico. 'trabajes' (subjuntivo) se mantiene (subjuntivo voseo no obligatorio)."),
    make(4009, lewinsky1_prem_rp, "Brit Hume trabaja para CNN.",
         "A", [], "Idem."),
    make(4010, lewinsky1_prem_rp, "Brit Hume trabaja para Fox.",
         "A", [], "Idem."),
]

# G42) idx 4107, 4108, 4109 — Clinton/Lewinsky impeachment (A)
clinton_prem_rp = ("No contento con deshonrar moralmente a Clinton, sus adversarios trataron "
                   "de inflar su encubrimiento del caso Lewinsky en crímenes y delitos imputables.")
g42 = [
    make(4107, clinton_prem_rp, "Clinton le fue completamente fiel a su mujer durante su largo matrimonio.",
         "A", [], "Figuras políticas reales; registro formal/periodístico. Sin peninsularismos léxicos."),
    make(4108, clinton_prem_rp, "Los adversarios de Clinton intentaron deshonrarlo y también acusarlo.",
         "A", [], "Idem."),
    make(4109, clinton_prem_rp,
         "El romance de Clinton con Lewinsky fue una desgracia moral para el Partido Demócrata y causó la derrota de Gore cuando se postuló para presidente.",
         "A", [], "Idem."),
]

# G43) idx 4281, 4282, 4283 — Madrid/Atlanta (A)
madrid_atl_prem_rp = ("Sospecho que los residentes de Madrid y Atlanta, si bien pueden "
                      "arrepentirse de haber perdido algo de tradición, de alguna manera "
                      "prefieren la modernidad.")
g43 = [
    make(4281, madrid_atl_prem_rp,
         "Estoy bastante seguro de que los residentes están en contra de cualquier cosa que los traiga al mundo moderno.",
         "A", [], "Topónimos reales (Madrid, Atlanta) sin marcadores dialectales relevantes."),
    make(4282, madrid_atl_prem_rp,
         "En secreto, los residentes de Madrid y Atlanta practican sus costumbres en casa.",
         "A", [], "Idem."),
    make(4283, madrid_atl_prem_rp,
         "Aunque pueden tener cierto remordimiento por perder sus costumbres, a ellos les gustan los cambios más recientes.",
         "A", [], "Idem."),
]

# G44) idx 4521, 4522, 4523 — yiddish supone (A — fragmento elíptico)
yid1_prem_rp = "Se supone de forma gratuita que el yiddish ..."
g44 = [
    make(4521, yid1_prem_rp, "Se asume con buenos motivos que el yiddish ...",
         "A", [], "Yiddish (lengua) sin equivalente RP; mantener. Fragmento elíptico formal."),
    make(4522, yid1_prem_rp, "Groseramente nunca se considera que el Yiddish...",
         "A", [], "Idem."),
    make(4523, yid1_prem_rp, "Hay muchas suposiciones diferentes sobre el Yiddish.",
         "A", [], "Idem."),
]

# G45) idx 4629, 4630, 4631 — ejercicio pronunciación inglesa (C: di → decí)
g45 = [
    make(4629, "Decí: break, steak, but bleak and streak.",
         "No digas descanso.",
         "C",
         ["di → decí (voseo imperativo)"],
         "Ejercicio de pronunciación con palabras EN; el imperativo 'di' se vosea a 'decí'. Las palabras EN del ejercicio se mantienen (forman parte del enunciado pedagógico). 'No digas' en hyp es válido tanto en tú como vos (forma de subjuntivo negativo coincide)."),
    make(4630, "Decí: break, steak, but bleak and streak.",
         "Decí curva.",
         "C",
         ["di → decí (voseo imperativo, en prem y en hyp)"],
         "Voseo imperativo aplicado en prem y hyp. Mismo prem que idx 4629."),
    make(4631, "Decí: break, steak, but bleak and streak.",
         "Decí romper",
         "C",
         ["di → decí (voseo imperativo, en prem y en hyp)"],
         "Idem idx 4630."),
]

# G46) idx 4635, 4636, 4637 — Yiddish Guide 2000 (A — PPC experiencial)
yid2_prem_rp = ("Espero vivir para el año 2000 para ayudar con la Guía Yiddish. Estoy seguro "
                "de que el yidish seguirá existiendo, sobreviviendo a sus detractores, como lo "
                "ha hecho durante mil años.")
g46 = [
    make(4635, yid2_prem_rp, "Estoy seguro de que el yiddish aún existirá en el 2000.",
         "A", [], "'como lo ha hecho durante mil años' = PPC con valor experiencial/habitual, MANTENER PPC."),
    make(4636, yid2_prem_rp, "Estoy seguro de que la cultura yiddish desafortunadamente se perderá para el año 2000.",
         "A", [], "Idem."),
    make(4637, yid2_prem_rp, "La cultura Yiddish ha sobrevivido por más de mil años.",
         "A", [], "Idem."),
]

# G47) idx 4647, 4648 — Boswell Cambridge (A — PPC estado vigente)
bosw_camb_prem_rp = ("La Cambridge University Press ha sido nombrada encargada de honrar el 200 "
                     "aniversario de La Vida de Johnson de Boswell con una colección de catorce "
                     "ensayos sobre el biógrafo y su tema.")
g47 = [
    make(4647, bosw_camb_prem_rp, "Boswell pasó unos años en compañía de Johnson.",
         "A", [], "'ha sido nombrada' = PPC con estado resultante vigente (sigue siendo la encargada), MANTENER."),
    make(4648, bosw_camb_prem_rp, "Boswell escribió sobre la vida de Johnson hace unos 200 años.",
         "A", [], "Idem."),
]

# G48) idx 4815, 4816, 4817 — Skeat nota (A)
skeat2_prem_rp = "En este caso, Skeat no ignorará esta nota y repetirá la ofensa en algún momento futuro."
g48 = [
    make(4815, skeat2_prem_rp, "Skeat va a prestar atención a la nota.",
         "A", [], "Texto biográfico formal sobre Skeat (filólogo). Sin peninsularismos relevantes."),
    make(4816, skeat2_prem_rp, "Skeat no va a prestarle nada de atención a la nota.",
         "A", [], "Idem."),
    make(4817, skeat2_prem_rp, "Skeat estudiará la nota todos los días.",
         "A", [], "Idem."),
]

# G49) idx 4887, 4888, 4889 — yiddish fonema (A)
yid3_prem_rp = "La e viene del fonema /e/, que en esta palabra se pronuncia como la e de ebb en todas las variantes del yiddish."
g49 = [
    make(4887, yid3_prem_rp, "Cada dialecto del yidis pronuncia la e en esta palabra de manera diferente.",
         "A", [], "Texto lingüístico técnico-formal; sin marcadores peninsulares."),
    make(4888, yid3_prem_rp, "La e en esta palabra se pronuncia igual en todas las variedades de yiddish.",
         "A", [], "Idem."),
    make(4889, yid3_prem_rp, "Hay 20 variedades de yidis.",
         "A", [], "Idem."),
]

# G50) idx 4935, 4936, 4937 — gruyere Suiza (A — registro literario-académico)
gruy_prem_rp = ("Parece tonto separar el queso gruyere de Gruyere, el lugar de Suiza de donde "
                "viene en realidad, este último ni siquiera es una entrada en las secciones "
                "geográficas de ninguno de los dos diccionarios.")
g50 = [
    make(4935, gruy_prem_rp, "Gruyere hace el mejor queso.",
         "A", [], "Comentario académico/lexicográfico (sobre diccionarios); 'parece tonto' en este registro narrativo-académico se mantiene (regla 'tonto' excepción de registro literario/académico)."),
    make(4936, gruy_prem_rp, "El queso gruyere no tiene que ver con el lugar.",
         "A", [], "Idem."),
    make(4937, gruy_prem_rp, "No se puede separar el queso Gruyere del lugar.",
         "A", [], "Idem."),
]

# ---------------------------------------------------------------------------
# Concatenamos en el orden original del input
# ---------------------------------------------------------------------------
all_records = (g1 + g2 + g3 + g4 + g5 + g6 + g7 + g8 + g9 + g10 +
               g11 + g12 + g13 + g14 + g15 + g16 + g17 + g18 + g19 + g20 +
               g21 + g22 + g23 + g24 + g25 + g26 + g27 + g28 + g29 + g30 +
               g31 + g32 + g33 + g34 + g35 + g36 + g37 + g38 + g39 + g40 +
               g41 + g42 + g43 + g44 + g45 + g46 + g47 + g48 + g49 + g50)

# Sanity: cubrir todos los 126
out_idxs = {r["idx"] for r in all_records}
src_idxs = set(src_by_idx.keys())
missing = src_idxs - out_idxs
extra = out_idxs - src_idxs
if missing or extra:
    raise SystemExit(f"MISMATCH — missing={sorted(missing)} extra={sorted(extra)}")
if len(all_records) != 126:
    raise SystemExit(f"Expected 126 records, got {len(all_records)}")

# Ordenar por idx del input para mantener orden estable
all_records.sort(key=lambda r: r["idx"])

with OUTPUT.open("w", encoding="utf-8") as f:
    for r in all_records:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

# Reporte
type_counts = {}
flag_count = 0
for r in all_records:
    type_counts[r["type"]] = type_counts.get(r["type"], 0) + 1
    if r["review_flag"]:
        flag_count += 1

print(f"OK — {len(all_records)} records escritos en {OUTPUT}")
print(f"   Distribución por tipo: {type_counts}")
print(f"   Con review_flag: {flag_count}")
