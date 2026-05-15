"""Re-pasada agresiva de adaptación cultural sobre las 51 instancias type=A
del batch anterior. Anglos → equivalentes AR; pachuco → compadrito.

Mapeo (estrategia híbrida Opción B):
  McKim                        → Etchegaray (arquitecto, apellido AR plausible)
  Mead (en firma "McKim Mead") → Bustillo (apellido AR de arquitecto real)
  H. H. Richardson             → Mario Roberto Álvarez (arquitecto AR icónico)
  Charles Follen McKim         → Etchegaray (consistencia con McKim solo)
  John M. Carrare              → Sánchez Elía (arquitecto AR real)
  Thomas Hastings              → Peralta Ramos (arquitecto AR real)
  Howard, Cauldwell            → Ramírez, Sánchez (apellidos AR genéricos)
  Adam Sandler                 → Marcelo Tinelli (no-arquitecto AR famoso)
  Gehry                        → Pelli (César Pelli, arquitecto AR contemporáneo)
  Le Corbusier                 → MANTENER (suizo-francés, no anglo)
  Pickard                      → García, ex-director de la SIDE
  Ashcroft                     → Domínguez, ministro de Justicia
  Lewinsky                     → Liñares (apellido AR neutral, evita carga política)
  Clinton                      → Pérez (genérico, evita carga política)
  Pynchon                      → Borges
  Boswell                      → Sábato
  Johnson (subject of bio)     → Borges
  Skeat                        → Borges
  Morrison                     → Sábato
  William Gaddis               → César Aira
  William Faulkner             → Juan José Saer
  John Burke (Alabama)         → Juan Báez (Universidad Nacional de Tucumán)
  pachuco/pachucos             → compadrito/compadritos
  pachuca/pachucas             → compadrita/compadritas
  Chicana(s)                   → barrio porteño / piba(s) porteña(s)
  EE. UU.                      → Buenos Aires (cuando contextualiza pachuco)
  México (en contexto pachuco) → el interior del país
  inglés y español (caló)      → español e italiano (lunfardo)
  Brit Hume                    → Joaquín Morales Solá
  Fox News (Sunday)            → La Nación
  CNN                          → C5N
  Weekly Standard              → Noticias
  Cambridge University Press   → Eudeba
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / "data/processed/opus_anglos_batch_2026-05-15.jsonl"
OUTPUT = ROOT / "data/processed/opus_anglos_batch_2026-05-15_translated.jsonl"

src_by_idx = {}
with INPUT.open(encoding="utf-8") as f:
    for line in f:
        d = json.loads(line)
        src_by_idx[d["idx"]] = d


def make(idx, prem_rp, hyp_rp, changes, note,
         review_flag=False, review_note=""):
    src = src_by_idx[idx]
    return {
        "idx": idx,
        "label": src["label"],
        "prem_es": src["prem_es"],
        "hyp_es": src["hyp_es"],
        "prem_rp": prem_rp,
        "hyp_rp": hyp_rp,
        "type": "E",
        "changes": list(changes),
        "secondary_features": [],
        "cultural_candidates": [],
        "review_flag": review_flag,
        "review_note": review_note,
        "note": note,
    }


# ---------- Group 1: idx 549, 550, 551 — McKim (competition) ----------
mckim1 = "Etchegaray, para su disgusto, no solo perdió, sino que quedó tercero detrás de Ramírez y Sánchez."
g1 = [
    make(549, mckim1, "Ramírez y Sánchez eran mujeres.",
         ["McKim → Etchegaray (E.1: apellido AR plausible para arquitecto, evita anacronismo con Pelli)",
          "Howard, Cauldwell → Ramírez, Sánchez (apellidos AR genéricos)"],
         "Tres antropónimos angloamericanos → equivalentes AR; Etchegaray reemplaza a McKim consistentemente en el grupo."),
    make(550, mckim1, "Etchegaray estaba muy feliz porque terminó primero.",
         ["McKim → Etchegaray (consistencia con prem)",
          "Howard, Cauldwell → Ramírez, Sánchez"],
         "Idem idx 549."),
    make(551, mckim1, "Etchegaray fue humillado porque terminó tercero.",
         ["McKim → Etchegaray", "Howard, Cauldwell → Ramírez, Sánchez"],
         "Idem."),
]

# ---------- Group 2: idx 1098, 1099, 1100 — pachuca/Chicana ----------
pachuca_prem1 = ("La compadrita era la contraparte del compadrito de la década de 1940, pero "
                 "también el arquetipo de la piba de barrio porteño que se junta con su grupo "
                 "y crece en un ambiente urbano de conventillo.")
g2 = [
    make(1098, pachuca_prem1, "Las compadritas eran bicicletas.",
         ["pachuca/pachuco → compadrita/compadrito (E.4: equivalente urbano AR de inicios s.XX)",
          "chica de barrio que se reúne en la Chicana → piba de barrio porteño que se junta con su grupo (Chicana no tiene equivalente AR)",
          "ambiente urbano tipo gueto → ambiente urbano de conventillo (paralelo histórico: conventillos porteños s.XX)"],
         "Transposición del referente chicano (pachuca de los 40 en EEUU) al compadrito porteño; gueto → conventillo preserva el matiz socioeconómico marginal.",
         review_flag=True,
         review_note="Transposición cultural extensa: pachuca chicana → compadrita porteña, incluyendo geografía (gueto/Chicana → conventillo/barrio porteño). NLI contradiction (compadritas=bicicletas) preservada."),
    make(1099, pachuca_prem1, "Las compadritas eran pibas porteñas.",
         ["pachucas → compadritas", "jóvenes Chicanas → pibas porteñas"],
         "Chicana sin equivalente AR; 'pibas porteñas' captura el subtipo cultural urbano.",
         review_flag=True,
         review_note="Idem; entailment preservada (compadritas son por definición pibas porteñas)."),
    make(1100, pachuca_prem1, "Las compadritas llevaban mucho maquillaje.",
         ["pachucas → compadritas"],
         "Idem; NLI neutral preservada.",
         review_flag=True,
         review_note="Idem grupo pachuca."),
]

# ---------- Group 3: idx 1137, 1138, 1139 — McKim Mead ----------
mckim2 = "Desvío para ver la mansión diseñada por Etchegaray Bustillo"
g3 = [
    make(1137, mckim2, "Etchegaray Bustillo diseñó la mansión.",
         ["McKim Mead → Etchegaray Bustillo (E.1: par de apellidos AR de arquitectos plausibles, replicando la firma 'McKim, Mead & White')"],
         "Firma de arquitectura adaptada como dúo AR; preserva la estructura prem/hyp."),
    make(1138, mckim2, "Construir la mansión cuesta 2 millones de dólares.",
         ["McKim Mead → Etchegaray Bustillo"],
         "Idem; hyp sin referente anglo."),
    make(1139, mckim2, "La mansión fue construída por Marcelo Tinelli.",
         ["McKim Mead → Etchegaray Bustillo",
          "Adam Sandler → Marcelo Tinelli (E.1: figura mediática AR no-arquitecta, preserva la contradicción humorística)"],
         "Adam Sandler (comediante de Hollywood) → Marcelo Tinelli (figura televisiva AR icónica, claramente no arquitecto) preserva la NLI contradiction."),
]

# ---------- Group 4: idx 1186, 1187 — Le Corbusier + Gehry ----------
gehry1 = "El plan es el generador, proclamó Le Corbusier. Pero con Pelli, el plan es el resultado."
g4 = [
    make(1186, gehry1, "El plan no es importante",
         ["Gehry → Pelli (E.1: César Pelli, arquitecto AR contemporáneo de fama internacional, equivalente directo)"],
         "Le Corbusier se mantiene (suizo-francés, no anglo, figura universal de la arquitectura)."),
    make(1187, gehry1, "El plan es invadir un país.",
         ["Gehry → Pelli"],
         "Idem."),
]

# ---------- Group 5: idx 1296, 1297, 1298 — Gehry alone ----------
gehry2 = "Esta es la manera en la que vivimos hoy. Pelli parece estar diciendo, ¿por qué no la disfrutamos?"
g5 = [
    make(1296, gehry2, "A Pelli no le importa la felicidad.",
         ["Gehry → Pelli (en prem y en hyp, consistencia)"],
         "Pelli reemplaza consistentemente."),
    make(1297, gehry2, "Pelli es una persona feliz.",
         ["Gehry → Pelli"],
         "Idem."),
    make(1298, gehry2, "Pelli parece decir disfrutar de la vida.",
         ["Gehry → Pelli"],
         "Idem."),
]

# ---------- Group 6: idx 1314, 1315, 1316 — pachucas/pachucos ----------
pachuca_prem2 = "Las compadritas eran las novias de los compadritos, pero también tenían un estilo de vestir propio."
g6 = [
    make(1314, pachuca_prem2, "Compadritas no conocía compadritos.",
         ["pachucas → compadritas (en prem y en hyp)", "pachucos → compadritos"],
         "Sustitución directa; concordancia gramatical defectuosa del ES original ('no conocía' con sujeto plural) se preserva para fidelidad al corpus."),
    make(1315, pachuca_prem2, "Compadritas conocía a compadritos.",
         ["pachucas → compadritas", "pachucos → compadritos"],
         "Idem."),
    make(1316, pachuca_prem2, "Las Compadritas llevaban más ropas que los Compadritos.",
         ["pachucas → compadritas", "pachucos → compadritos"],
         "Idem; mayúsculas se conservan según hyp original ('Las Pachucas... los Pachucos')."),
]

# ---------- Group 7: idx 1421 — multi-arquitectos ----------
arch_prem = ("Mario Roberto Álvarez y su protegido Etchegaray fueron ex alumnos, así como los "
             "asistentes de Etchegaray, Sánchez Elía y Peralta Ramos.")
g7 = [
    make(1421, arch_prem,
         "Mario Roberto Álvarez, Etchegaray, Sánchez Elía y Peralta Ramos fueron todos ex alumnos.",
         ["H. H. Richardson → Mario Roberto Álvarez (arquitecto AR icónico s.XX)",
          "Charles Follen McKim → Etchegaray (consistencia con McKim solo)",
          "John M. Carrare → Sánchez Elía (arquitecto AR real)",
          "Thomas Hastings → Peralta Ramos (arquitecto AR real)"],
         "Cuatro arquitectos angloamericanos del s.XIX-XX → cuatro figuras AR de la arquitectura moderna; entailment preservado.",
         review_flag=True,
         review_note="Sustitución múltiple (4 nombres). Mario Roberto Álvarez, Sánchez Elía y Peralta Ramos son arquitectos AR reales pero con cronología distinta (s.XX) a Richardson/McKim (s.XIX); el NLI no depende de la cronología."),
]

# ---------- Group 8: idx 1428, 1429, 1430 — pachuco menospreciado ----------
pachuco_prem3 = ("El compadrito fue menospreciado en Buenos Aires por tanto la clase media "
                 "porteña y la elite tradicional, y de igual manera en el interior del país "
                 "por los medios y los intelectuales.")
g8 = [
    make(1428, pachuco_prem3,
         "En Buenos Aires, la clase media porteña y la elite tradicional pensaban que el compadrito era indigno.",
         ["pachuco → compadrito",
          "EE. UU. → Buenos Aires",
          "mexicano-estadounidenses → clase media porteña",
          "comunidades anglosajonas → elite tradicional",
          "México → el interior del país (en mapeo cultural: compadrito como fenómeno porteño visto desde el interior)"],
         "Transposición sociológica completa del pachuco (México/EEUU) al compadrito (BA/interior); entailment preservada.",
         review_flag=True,
         review_note="Transposición cultural-geográfica extensa. El NLI se preserva porque las relaciones internas (menosprecio mutuo entre grupos) se mantienen."),
    make(1429, pachuco_prem3,
         "El compadrito fue adoptado en Buenos Aires por la clase media porteña.",
         ["pachuco → compadrito (en prem y en hyp)",
          "EE. UU. → Buenos Aires", "mexicano-estadounidenses → clase media porteña",
          "comunidades anglosajonas → elite tradicional", "México → el interior del país"],
         "Contradiction preservada (adopción ≠ menosprecio).",
         review_flag=True,
         review_note="Idem idx 1428."),
    make(1430, pachuco_prem3, "El compadrito tuvo muchos efectos negativos.",
         ["pachuco → compadrito"],
         "Hyp solo nombra al sujeto; NLI neutral preservada.",
         review_flag=True,
         review_note="Idem grupo 1428."),
]

# ---------- Group 9: idx 1476, 1477 — pachuco habla ----------
pachuco_prem4 = ("el compadrito, una variedad de español con italiano y otras lenguas, también "
                 "llamado lunfardo, fue una fascinante fusión proveniente de muchas fuentes "
                 "lingüísticas.")
g9 = [
    make(1476, pachuco_prem4,
         "Mucha gente hoy todavía habla una versión u otra versión de lunfardo.",
         ["pachuco (habla) → compadrito (habla)",
          "combinación de inglés y español → variedad de español con italiano y otras lenguas",
          "caló → lunfardo (paralelo lingüístico: caló chicano ↔ lunfardo porteño)"],
         "Pachuco habla = caló chicano (EN+ES). Compadrito habla = lunfardo (ES+IT+indigenismos+jergas). Paralelo cultural-lingüístico exacto. NLI neutral preservada.",
         review_flag=True,
         review_note="Transposición lingüística: inglés-español (caló) → español-italiano (lunfardo). Cambia el contenido factual pero preserva la estructura argumental ('mucha gente todavía habla una versión')."),
    make(1477, pachuco_prem4,
         "Los bloques de construcción del discurso compadrito son español e italiano.",
         ["pachuco (habla) → compadrito (habla)",
          "inglés y español → español e italiano",
          "caló → lunfardo"],
         "Entailment preservada: prem describe lunfardo como español+italiano+otras, hyp afirma los componentes principales.",
         review_flag=True,
         review_note="Idem idx 1476."),
]

# ---------- Group 10: idx 1527, 1528, 1529 — Pickard ----------
pickard_prem = ("García, ex-director de la SIDE, recuerda la presunta aseveración que se hizo "
                "en una sesión informativa el 12 de julio.")
g10 = [
    make(1527, pickard_prem, "García no podía recordar nada de lo que habían dicho.",
         ["Pickard → García, ex-director de la SIDE (E.1: apellido AR genérico + rol contextual; Thomas Pickard fue ex-director del FBI, equivalente funcional AR)"],
         "Rol funcional preservado (servicio de inteligencia federal); contradiction preservada."),
    make(1528, pickard_prem,
         "García recordó que la sesión informativa cubría los hechos del accidente.",
         ["Pickard → García (ex-SIDE)"],
         "Idem."),
    make(1529, pickard_prem, "García recordó lo que se dijo en el informe.",
         ["Pickard → García (ex-SIDE)"],
         "Idem."),
]

# ---------- Group 11: idx 2097, 2099 — Pynchon vida privada ----------
pynchon_prem1 = ("Borges: Como corresponde a un hombre cauto, en lugar de alardear, Borges ha "
                 "mantenido su vida privada en secreto.")
g11 = [
    make(2097, pynchon_prem1, "Se rumorea que Borges tiene un hijo y una hija.",
         ["Pynchon → Borges (E.1: escritor argentino universalmente reconocido, equivalente icónico)"],
         "NLI neutral preservada (rumor sobre vida privada no derivable de cautela del autor).",
         review_flag=True,
         review_note="Borges no era recluso como Pynchon (perfil público diferente), pero la NLI depende solo de la estructura 'autor cauto + rumor sobre vida privada' que se preserva."),
    make(2099, pynchon_prem1,
         "Hay un famoso programa de televisión sobre la vida privada de Borges, que protagoniza el mismísimo Borges.",
         ["Pynchon → Borges (en prem y en hyp)"],
         "Contradiction preservada (programa público ↔ vida en secreto).",
         review_flag=True,
         review_note="Idem idx 2097."),
]

# ---------- Group 12: idx 2103, 2104, 2105 — Morrison + Pynchon ----------
morrison_prem = ("Sábato se ha ganado el derecho a ser tan idiosincrático como, digamos, "
                 "César Aira, Jorge Luis Borges o Juan José Saer.")
g12 = [
    make(2103, morrison_prem, "Aira y Borges no son tan idiosincráticos como Sábato.",
         ["Morrison → Sábato (Nobel-aspirante AR, ensayista-novelista)",
          "William Gaddis → César Aira (escritor AR idiosincrático contemporáneo)",
          "Thomas Pynchon → Jorge Luis Borges (per tabla)",
          "William Faulkner → Juan José Saer (escritor AR experimental)"],
         "Cuatro escritores anglosajones idiosincráticos → cuatro AR equivalentes. Contradiction preservada.",
         review_flag=True,
         review_note="Sustitución cuádruple de autores. La equivalencia es estilística (todos idiosincráticos en su tradición); el NLI depende solo de la jerarquía interna 'X tan idiosincrático como Y, Z, W'."),
    make(2104, morrison_prem,
         "Sábato ha trabajado muy duro para ganarse el derecho de ser idiosincrásico.",
         ["Morrison → Sábato"],
         "Neutral preservada (esfuerzo no se deriva del derecho ganado).",
         review_flag=True,
         review_note="Idem idx 2103."),
    make(2105, morrison_prem, "Sábato puede ser tan idiosincrático como César Aira.",
         ["Morrison → Sábato", "William Gaddis → César Aira"],
         "Entailment preservada.",
         review_flag=True,
         review_note="Idem."),
]

# ---------- Group 13: idx 2244, 2245, 2246 — Skeat sesenta ----------
skeat_prem1 = ("Cuando llegó a los sesenta años, en 1959, Borges dio la impresión de que estaba "
               "empezando a tomarse menos en serio estos asuntos")
g13 = [
    make(2244, skeat_prem1,
         "Cuando Borges cumplió los sesenta, no dio señales de que estaba pensando en nada.",
         ["Skeat → Borges (per tabla; Borges fue bibliotecario/lingüista, encaja con filólogo)",
          "1895 → 1959 (ajuste cronológico: Borges nació en 1899, sesenta en 1959)"],
         "Año adaptado para coherencia biográfica con Borges; NLI contradiction preservada (depende de 'señales de pensamiento', no del año).",
         review_flag=True,
         review_note="Año cambiado (1895 → 1959) para no introducir anacronismo con Borges. El NLI no depende de la cifra exacta."),
    make(2245, skeat_prem1,
         "A medida que Borges creció, tuvo la sensación de que se tomaba estos asuntos menos.",
         ["Skeat → Borges", "1895 → 1959"],
         "Entailment preservada.",
         review_flag=True,
         review_note="Idem idx 2244."),
    make(2246, skeat_prem1,
         "Borges comenzó a preocuparse por diferentes cosas a medida que envejecía.",
         ["Skeat → Borges", "1895 → 1959"],
         "Neutral preservada.",
         review_flag=True,
         review_note="Idem."),
]

# ---------- Group 14: idx 2478, 2479 — Boswell + John Burke + Johnson ----------
boswell_prem1 = ("Juan Báez (Universidad Nacional de Tucumán) revisa y analiza otros relatos "
                 "contemporáneos y descubre que Sábato no solo es el más preciso, sino que lo "
                 "utiliza para demostrar el carácter de Borges, mientras que otros simplemente "
                 "vendían chismes literarios.")
g14 = [
    make(2478, boswell_prem1, "A Juan Báez no le agrada Sábato.",
         ["Boswell → Sábato (per tabla)",
          "John Burke (Alabama) → Juan Báez (Universidad Nacional de Tucumán) (académico AR genérico con afiliación regional)",
          "Johnson → Borges (sujeto biografiado, paralelo: Sábato escribiendo sobre Borges)"],
         "Sábato como biógrafo de Borges es plausible (contemporáneos); paralelo Boswell/Johnson preservado."),
    make(2479, boswell_prem1, "Juan Báez ignora las cuentas.",
         ["Boswell → Sábato", "John Burke → Juan Báez (UNT)", "Johnson → Borges"],
         "Idem."),
]

# ---------- Group 15: idx 3129, 3130 — Ashcroft + Pickard 1 ----------
ashcroft_prem1 = ("Existe una disputa sobre el interés del ministro de Justicia Domínguez en "
                  "las reuniones informativas del ex-director de la SIDE García sobre la "
                  "situación de amenaza terrorista.")
g15 = [
    make(3129, ashcroft_prem1,
         "Domínguez dijo que las sesiones de información no valían la pena.",
         ["Ashcroft → Domínguez, ministro de Justicia (apellido AR genérico + rol contextual)",
          "Pickard → García, ex-director de la SIDE"],
         "Doble sustitución con roles funcionales explícitos; contradiction preservada."),
    make(3130, ashcroft_prem1, "Domínguez quería escuchar los informes una y otra vez.",
         ["Ashcroft → Domínguez", "Pickard → García"],
         "Idem."),
]

# ---------- Group 16: idx 3447, 3449 — Pickard + Ashcroft 2 ----------
ashcroft_prem2 = ("Nos dijeron que García, ex-director de la SIDE, y Domínguez, ministro de "
                  "Justicia, no tenían una buena relación.")
g16 = [
    make(3447, ashcroft_prem2,
         "García y Domínguez eran conocidos por ser muy buenos amigos.",
         ["Pickard → García (ex-SIDE)", "Ashcroft → Domínguez (Justicia)"],
         "Contradiction preservada."),
    make(3449, ashcroft_prem2,
         "Nunca podían ponerse de acuerdo sobre qué ingredientes colocar en la pizza en las reuniones del personal.",
         ["Pickard → García", "Ashcroft → Domínguez"],
         "Hyp sin nombres explícitos; sujeto implícito refiere a García y Domínguez. Neutral preservada."),
]

# ---------- Group 17: idx 4008, 4009, 4010 — Brit Hume + Lewinsky + Fox ----------
hume_prem = ("El amor lo vence todo (a menos que trabajes para Noticias): Joaquín Morales Solá "
             "(La Nación) especula sobre el porqué Liñares podría no... Todavía tiene un "
             "enamoramiento sin esperanza con el presidente.")
g17 = [
    make(4008, hume_prem, "Joaquín Morales Solá es el reportero principal de La Nación.",
         ["Brit Hume → Joaquín Morales Solá (columnista político mainstream AR)",
          "Fox News Sunday → La Nación",
          "Weekly Standard → Noticias (revista política AR)",
          "Lewinsky → Liñares (apellido AR neutral, evita confusión con Fernández AR)"],
         "Periodista AR + medio AR equivalente; neutral preservada."),
    make(4009, hume_prem, "Joaquín Morales Solá trabaja para C5N.",
         ["Brit Hume → Joaquín Morales Solá", "Fox News Sunday → La Nación",
          "Weekly Standard → Noticias", "Lewinsky → Liñares",
          "CNN → C5N (cable news AR de signo opuesto a La Nación, preserva la contradicción)"],
         "Contradiction preservada (trabaja en medio rival)."),
    make(4010, hume_prem, "Joaquín Morales Solá trabaja para La Nación.",
         ["Brit Hume → Joaquín Morales Solá", "Fox News Sunday → La Nación",
          "Weekly Standard → Noticias", "Lewinsky → Liñares",
          "Fox → La Nación (consistencia con prem)"],
         "Entailment preservada."),
]

# ---------- Group 18: idx 4107, 4108, 4109 — Clinton + Lewinsky impeachment ----------
clinton_prem = ("No contento con deshonrar moralmente al presidente Pérez, sus adversarios "
                "trataron de inflar su encubrimiento del caso Liñares en crímenes y delitos "
                "imputables.")
g18 = [
    make(4107, clinton_prem,
         "El presidente Pérez le fue completamente fiel a su mujer durante su largo matrimonio.",
         ["Clinton → presidente Pérez (apellido AR genérico, evita carga política — paralelo histórico Menem omitido por carga)",
          "caso Lewinsky → caso Liñares"],
         "Contradiction preservada; Pérez genérico evita anclaje a Menem (políticamente cargado).",
         review_flag=True,
         review_note="Clinton → 'presidente Pérez' (genérico). El paralelo histórico exacto sería Menem (presidente AR de los 90 con escándalos sexuales), pero el usuario pidió evitar carga política para Ashcroft/Lewinsky; aplico la misma regla a Clinton."),
    make(4108, clinton_prem,
         "Los adversarios de Pérez intentaron deshonrarlo y también acusarlo.",
         ["Clinton → Pérez", "caso Lewinsky → caso Liñares"],
         "Entailment preservada.",
         review_flag=True,
         review_note="Idem idx 4107."),
    make(4109, clinton_prem,
         "El romance de Pérez con Liñares fue una desgracia moral para su partido y causó la derrota de su candidato a sucesor cuando se postuló para presidente.",
         ["Clinton → Pérez", "Lewinsky → Liñares",
          "Partido Demócrata → su partido (genérico)",
          "Gore → su candidato a sucesor (genérico)"],
         "Neutral preservada; sustituciones genéricas evitan anclaje partidario AR.",
         review_flag=True,
         review_note="Múltiples sustituciones genéricas para evitar carga política (Partido Demócrata y Gore omitidos como nombres específicos)."),
]

# ---------- Group 19: idx 4647, 4648 — Cambridge Press + Boswell + Johnson ----------
boswell_prem2 = ("Eudeba ha sido nombrada encargada de honrar el 20 aniversario de La Vida de "
                 "Borges de Sábato con una colección de catorce ensayos sobre el biógrafo y su tema.")
g19 = [
    make(4647, boswell_prem2, "Sábato pasó unos años en compañía de Borges.",
         ["Cambridge University Press → Eudeba (editorial universitaria AR equivalente)",
          "Boswell → Sábato", "Johnson → Borges",
          "200 aniversario → 20 aniversario (ajuste cronológico: Sábato y Borges son s.XX, no s.XVIII)"],
         "Neutral preservada; el biógrafo (Sábato) y su sujeto (Borges) fueron contemporáneos en el s.XX.",
         review_flag=True,
         review_note="Cambio cronológico mayor (200 → 20 años) para evitar anacronismo. La hyp 4648 también cambia coherentemente."),
    make(4648, boswell_prem2,
         "Sábato escribió sobre la vida de Borges hace unos 20 años.",
         ["Cambridge University Press → Eudeba", "Boswell → Sábato", "Johnson → Borges",
          "200 → 20 (hyp también, para preservar entailment con el cambio del prem)"],
         "Entailment preservada por consistencia numérica entre prem y hyp.",
         review_flag=True,
         review_note="Cifra de aniversario armonizada en prem y hyp (200 → 20). Esta consistencia es necesaria para preservar la NLI entailment."),
]

# ---------- Group 20: idx 4815, 4816, 4817 — Skeat note ----------
skeat_prem2 = ("En este caso, Borges no ignorará esta nota y repetirá la ofensa en algún momento futuro.")
g20 = [
    make(4815, skeat_prem2, "Borges va a prestar atención a la nota.",
         ["Skeat → Borges (consistencia con grupo 2244-2246)"],
         "Entailment preservada."),
    make(4816, skeat_prem2, "Borges no va a prestarle nada de atención a la nota.",
         ["Skeat → Borges"],
         "Contradiction preservada."),
    make(4817, skeat_prem2, "Borges estudiará la nota todos los días.",
         ["Skeat → Borges"],
         "Neutral preservada."),
]

all_records = (g1 + g2 + g3 + g4 + g5 + g6 + g7 + g8 + g9 + g10 +
               g11 + g12 + g13 + g14 + g15 + g16 + g17 + g18 + g19 + g20)

# Sanity check
out_idxs = {r["idx"] for r in all_records}
src_idxs = set(src_by_idx.keys())
missing = src_idxs - out_idxs
extra = out_idxs - src_idxs
if missing or extra:
    raise SystemExit(f"MISMATCH — missing={sorted(missing)} extra={sorted(extra)}")
if len(all_records) != 51:
    raise SystemExit(f"Expected 51 records, got {len(all_records)}")

all_records.sort(key=lambda r: r["idx"])

with OUTPUT.open("w", encoding="utf-8") as f:
    for r in all_records:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

flag_count = sum(1 for r in all_records if r["review_flag"])
print(f"OK — {len(all_records)} records escritos en {OUTPUT}")
print(f"   Todas type=E (adaptación cultural agresiva)")
print(f"   Con review_flag: {flag_count}")
