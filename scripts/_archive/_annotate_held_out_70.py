"""
Anotador del held-out de 70 instancias (posiciones 30-99 del 500).

Las 70 anotaciones están embebidas como tuplas:
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
OUTPUT = REPO_ROOT / "data" / "processed" / "xnli_held_out_70_raw.jsonl"


# ---------------------------------------------------------------------------
# Anotaciones manuales (Opus 4.7, max effort).
# Cada entrada: (idx, type, prem_rp_or_None, hyp_rp_or_None, changes,
#                secondary_features, cultural_candidates, note)
# Si prem_rp/hyp_rp son None → se reusa el ES (type A).
# ---------------------------------------------------------------------------

ANNOTATIONS = [
    # --- pos 30 ---
    (1708, "A", None, None, [], [], [],
     "Tercera persona narrativa; sin marcadores dialectales."),

    # --- pos 31 ---
    (628, "A", None, None, [], [], [],
     "Sin marcadores dialectales; registro neutro."),

    # --- pos 32 ---
    (4006, "D",
     None,
     "Hicimos tres obras históricas en el pasado.",
     ["jugadas → obras (corrección de error de traducción: 'plays' como obras de teatro, no 'jugadas')",
      "hemos hecho → hicimos (PPC → pretérito simple RP)"],
     ["cambio_PPC"], [],
     "El ES traduce 'plays' como 'jugadas' cuando el contexto del prem ('obras') indica obras teatrales; adicionalmente PPC peninsular → pretérito simple."),

    # --- pos 33 ---
    (2295, "C",
     "Acá se pueden encontrar muchos ejemplos de todas las artesanías producidas localmente, y vas a comprarlas mucho más baratas que en cualquier resort, sobre todo si practicás tu habilidad para negociar antes.",
     "Es más barato comprar cosas acá porque no hay impuestos.",
     ["practicas → practicás (acentuación voseo)", "Aquí → Acá (léxico peninsular → RP)", "aquí → acá (léxico peninsular → RP)"],
     ["lexico_aqui_aca"], [],
     "Voseo dominante (rasgo más distintivo); aquí→acá registrado como sustitución léxica adicional obligatoria."),

    # --- pos 34 ---
    (1222, "A", None, None, [], [], [],
     "Sin marcadores; pretérito simple panhispánico."),

    # --- pos 35 ---
    (2990, "A", None, None, [], [], [],
     "Registro técnico/institucional sin marcadores."),

    # --- pos 36 ---
    (4125, "A", None, None, [], [], [],
     "PPC con valor experiencial ('Has leído... en el pasado año') aceptable en RP."),

    # --- pos 37 ---
    (3716, "C",
     "Ya entendés la importancia de la narración, poesía, canción y teatro a la hora de fomentar la empatía, compasión e imaginación.",
     None,
     ["entiendes → entendés (acentuación voseo)"],
     [], [],
     "Voseo en 2ª persona singular indicativo (entender)."),

    # --- pos 38 ---
    (3813, "A", None, None, [], [], [],
     "Tercera persona; 'Hoosiers' es gentilicio extranjero (Indiana, EEUU), se mantiene."),

    # --- pos 39 ---
    (197, "A", None, None, [], [], [],
     "Pretérito simple 1ª persona; sin marcadores dialectales."),

    # --- pos 40 ---
    (1409, "A", None, None, [], [], [],
     "Registro académico tercera persona; sin marcadores."),

    # --- pos 41 ---
    (4014, "A", None, None, [], [], [],
     "Sin marcadores; 'parka', 'montar en trineo' panhispánicos."),

    # --- pos 42 ---
    (3103, "D",
     None,
     "Múltiples pasajeros podrían ser transportados en estos casos.",
     ["cajas → casos (corrección de error de traducción: 'cases' = 'casos', no 'cajas')"],
     [], [],
     "El ES traduce 'cases' como 'cajas' (boxes); la corrección a 'casos' preserva el entailment."),

    # --- pos 43 ---
    (4207, "A", None, None, [], [], [],
     "PPC con valor estado-resultado ('se ha convertido en') aceptable en RP escrito periodístico."),

    # --- pos 44 ---
    (2240, "A", None, None, [], [], [],
     "Sin marcadores; 'de momento' panhispánico."),

    # --- pos 45 ---
    (1534, "C",
     "Sí, claro, se lo diré.",
     None,
     ["os lo diré → se lo diré (vosotros peninsular → ustedes RP, regla pronominal les+lo → se+lo)"],
     [], [],
     "'Os' es marcador inequívoco de 2ª plural peninsular; en RP se usa 'ustedes' que rige 3ª plural y aplica la regla 'le(s) lo → se lo'."),

    # --- pos 46 ---
    (4562, "A", None, None, [], [], [],
     "PPC ('no ha tenido en cuenta') con valor estado-resultado se mantiene; 'aportación' aceptable en RP formal."),

    # --- pos 47 ---
    (2957, "A", None, None, [], [], [],
     "Tercera persona; tilde diacrítica deprecada en 'ésta' se mantiene (decisión consistente con gold)."),

    # --- pos 48 ---
    (4617, "A", None, None, [], [], [],
     "Tercera persona; sin marcadores dialectales."),

    # --- pos 49 ---
    (4783, "A", None, None, [], [], [],
     "PPC con valor estado-resultado en registro literario; aceptable en RP."),

    # --- pos 50 ---
    (659, "C",
     "Cada vez que comprás un artículo, especialmente un artículo de gran compra, es algo en lo que pagás y siempre has añadido un impuesto del diez por ciento.",
     "Nunca tenés que calcular el impuesto para determinar el costo.",
     ["compras → comprás (acentuación voseo)",
      "pagas → pagás (acentuación voseo)",
      "tienes → tenés (voseo)",
      "coste → costo (léxico peninsular → RP)"],
     ["lexico_peninsular"], [],
     "Voseo dominante en 2ª persona singular (3 cambios C); 'coste → costo' como cambio léxico secundario. PPC con 'siempre' (habitual) se mantiene."),

    # --- pos 51 ---
    (595, "C",
     "eso es lo bueno de vivir más en el país, no tenés que preocuparte por nada de esto",
     None,
     ["tienes → tenés (voseo)"],
     [], [],
     "Voseo en 'tenés'; clítico 'te' en 'preocuparte' es igual en tuteo y voseo."),

    # --- pos 52 ---
    (1000, "A", None, None, [], [],
     [{"original": "haga bueno", "suggestion": "esté lindo", "category": "lexico_cultural_generico"}],
     "'Haga bueno' es expresión meteorológica peninsular; se marca como candidato cultural sin adaptar (cambio mínimo)."),

    # --- pos 53 ---
    (1002, "A", None, None, [], [], [],
     "Primera persona plural; registro abstracto sin marcadores."),

    # --- pos 54 ---
    (391, "A", None, None, [], [], [],
     "Pretérito simple 1ª plural; sin marcadores."),

    # --- pos 55 ---
    (573, "A", None, None, [], [], [],
     "Tercera persona; 'oye' interjección panhispánica, 'no hayan sido' subjuntivo neutro."),

    # --- pos 56 ---
    (4751, "A", None, None, [], [], [],
     "PPC ('han tenido un éxito mixto') con valor estado-resultado en registro académico; aceptable en RP."),

    # --- pos 57 ---
    (1535, "C",
     "Sí, claro, se lo diré.",
     None,
     ["os lo diré → se lo diré (vosotros peninsular → ustedes RP)"],
     [], [],
     "'Os' es marcador peninsular plural; 'prometiste' pretérito simple igual en tuteo/voseo."),

    # --- pos 58 ---
    (4769, "A", None, None, [], [], [],
     "Registro académico tercera persona; sin marcadores."),

    # --- pos 59 ---
    (4126, "A", None, None, [], [], [],
     "PPC experiencial en prem se mantiene; hyp usa 'el año pasado' RP estándar."),

    # --- pos 60 ---
    (4524, "A", None, None, [], [], [],
     "Registro formal de carta; PPC ('ha leído... tres veces') con valor recurrente se mantiene."),

    # --- pos 61 ---
    (1915, "A", None, None, [], [], [],
     "Subjuntivo 'hayas' aceptable en RP escrito formal; voseo en subjuntivo ('hayás') es opcional/coloquial y la regla estándar de la spec aplica al indicativo e imperativo."),

    # --- pos 62 ---
    (3087, "A", None, None, [], [], [],
     "Tercera persona; 'Hezbolá'/'Hozbollah' es variación ortográfica del nombre propio, no dialectal."),

    # --- pos 63 ---
    (3297, "A", None, None, [], [], [],
     "Narrativa tercera persona; sin marcadores."),

    # --- pos 64 ---
    (978, "A", None, None, [], [], [],
     "Primera persona y registro coloquial sin marcadores 2ª persona; 'maquinaria militar' panhispánico."),

    # --- pos 65 ---
    (1294, "A", None, None, [], [], [],
     "Pretérito simple tercera persona; sin marcadores."),

    # --- pos 66 ---
    (2453, "A", None, None, [], [], [],
     "Descriptivo tercera persona; nombres propios alemanes se preservan."),

    # --- pos 67 ---
    (991, "A", None, None, [], [], [],
     "Primera plural; 'acre' y 'pie cuadrado' como unidades imperiales se mantienen, no son marcadores dialectales."),

    # --- pos 68 ---
    (1993, "D",
     None,
     "Blood se metió en un bote.",
     ["La sangre → Blood (corrección de error de traducción: 'Blood' es nombre propio del Capitán Blood, no traducir como sustantivo común)"],
     [], [],
     "El hyp_es traduce literalmente 'Blood' como 'La sangre' rompiendo la referencia al personaje del prem; la corrección preserva el entailment."),

    # --- pos 69 ---
    (619, "C",
     None,
     "No tenés que hacerlo todo.",
     ["tienes → tenés (voseo)"],
     [], [],
     "Voseo en 'tenés'; 'no hagas' (subjuntivo en imperativo negativo) se mantiene como forma neutra aceptable en RP escrito."),

    # --- pos 70 ---
    (574, "A", None, None, [], [], [],
     "Tercera persona; igual que idx 573 mismo prem narrativo."),

    # --- pos 71 ---
    (4664, "D",
     "(a) Cambiá cada d o t del objetivo con c.",
     "Debería haber más c's en el objetivo de d's.",
     ["tarjeta → objetivo (corrección de error de traducción: 'target' es 'objetivo' como en prem, no 'tarjeta')",
      "Cambia → Cambiá (imperativo voseo)"],
     ["voseo"], [],
     "Inconsistencia interna del ES: 'target' se traduce como 'objetivo' en prem pero 'tarjeta' en hyp; se unifica a 'objetivo'. Adicionalmente voseo en imperativo afirmativo."),

    # --- pos 72 ---
    (3281, "A", None, None, [], [], [],
     "Tercera persona; 'lobby' anglicismo aceptado en RP."),

    # --- pos 73 ---
    (827, "C",
     "Es increíble, es increíble lo que podés sacar de un poquito",
     None,
     ["puedes → podés (voseo)"],
     [], [],
     "Voseo en 'podés' 2ª persona singular indicativo."),

    # --- pos 74 ---
    (4706, "A", None, None, [], [], [],
     "'Blood and flood' como sustantivos comunes en juego fonológico (rima), no nombre propio; traducción literal a 'sangre y flujo/crecida' adecuada."),

    # --- pos 75 ---
    (3841, "D",
     "Y más del 30 % de los niños a los que servimos no pueden permitirse el precio del campamento.",
     None,
     ["permiirse → permitirse (corrección de typo)",
      "campañemto → campamento (corrección de typo)"],
     [], [],
     "Typos ortográficos del ES original; se corrigen sin alterar el significado, análogo al caso 'pieta/piata → piñata' en gold (idx 1453)."),

    # --- pos 76 ---
    (3459, "D",
     "Dijo que si sus asesores le hubieran dicho que había una célula en Estados Unidos, se habrían trasladado para ocuparse del asunto.",
     None,
     ["celda → célula (corrección de error de traducción: 'cell' en contexto de terrorismo es 'célula', no 'celda')"],
     [], [],
     "El ES traduce 'cell' como 'celda' (de prisión) cuando el contexto requiere 'célula' (grupo terrorista); el hyp ya usa 'células' correctamente, se unifica."),

    # --- pos 77 ---
    (421, "A", None, None, [], [], [],
     "Tercera plural pretérito simple; sin marcadores."),

    # --- pos 78 ---
    (709, "A", None, None, [], [], [],
     "Primera persona condicional + tercera plural; sin marcadores 2ª persona."),

    # --- pos 79 ---
    (3260, "A", None, None, [], [], [],
     "Tercera plural pretérito simple; registro neutro."),

    # --- pos 80 ---
    (2595, "A", None, None, [], [], [],
     "Registro corporativo tercera persona; 'fiable' panhispánico."),

    # --- pos 81 ---
    (3322, "A", None, None, [], [], [],
     "Imperativo formal usted ('consulte') igual en RP."),

    # --- pos 82 ---
    (2594, "A", None, None, [], [], [],
     "Tercera plural; registro técnico sin marcadores."),

    # --- pos 83 ---
    (2329, "A", None, None, [], [], [],
     "'Olimpiadas' / 'Juegos Olímpicos' son sinónimos panhispánicos; tercera persona sin marcadores."),

    # --- pos 84 ---
    (2174, "A", None, None, [], [], [],
     "Tercera persona descriptiva; sin marcadores."),

    # --- pos 85 ---
    (3305, "A", None, None, [], [], [],
     "Imperativo formal usted ('consulte') igual en RP."),

    # --- pos 86 ---
    (416, "C",
     "Es como un archivo con un montón de pestañas diferentes, ya sabés. Cada pestaña tiene como una hoja de cálculo diferente en ella.",
     None,
     ["sabes → sabés (voseo)"],
     [], [],
     "Voseo en 'sabés' 2ª persona singular."),

    # --- pos 87 ---
    (765, "A", None, None, [], [], [],
     "Primera persona con 'yo tampoco' (énfasis contrastivo válido); sin marcadores 2ª."),

    # --- pos 88 ---
    (2816, "A", None, None, [], [], [],
     "Tercera persona; registro burocrático sin marcadores."),

    # --- pos 89 ---
    (1888, "A", None, None, [], [], [],
     "Vocativo 'capitán' + futuro simple; sin marcadores 2ª persona."),

    # --- pos 90 ---
    (3336, "A", None, None, [], [], [],
     "Tercera persona; 'camioneta' aceptado en RP."),

    # --- pos 91 ---
    (3121, "A", None, None, [], [], [],
     "Tercera persona; 'automovilístico' panhispánico."),

    # --- pos 92 ---
    (4690, "A", None, None, [], [], [],
     "Tercera persona reflexiva; registro abstracto."),

    # --- pos 93 ---
    (1181, "A", None, None, [], [], [],
     "Tercera plural imperfecto pasivo; sin marcadores."),

    # --- pos 94 ---
    (4065, "A", None, None, [], [], [],
     "PPC ('se ha denominado') con valor estado-resultado en registro periodístico; aceptable en RP."),

    # --- pos 95 ---
    (2500, "B",
     None,
     "El camino era tan curvilíneo que era difícil manejar por él.",
     ["conducir → manejar (léxico peninsular → RP)"],
     [], [],
     "'Conducir' es marcador léxico peninsular fuerte; RP usa 'manejar' para vehículos."),

    # --- pos 96 ---
    (1514, "A", None, None, [], [], [],
     "Futuro 1ª persona + narrativa 3ª; sin marcadores."),

    # --- pos 97 ---
    (1777, "A", None, None, [], [], [],
     "Narrativa literaria tercera persona; pretérito simple e imperfecto sin marcadores."),

    # --- pos 98 ---
    (1942, "D",
     "Astuta defensa, él está de acuerdo.",
     None,
     ["Shrewd → Astuta (corrección: palabra inglesa sin traducir en el ES original)"],
     [], [],
     "El ES dejó 'Shrewd' sin traducir; el hyp ya usa 'astuta defensa', se unifica."),

    # --- pos 99 ---
    (3440, "D",
     "Sin embargo, la guía presupuestaria emitida al día siguiente destacó como prioridades los crímenes con armas de fuego, el narcotráfico y los derechos civiles.",
     None,
     ["guia → guía (corrección de typo: tilde faltante en 'guía')"],
     [], [],
     "Typo ortográfico del ES original (falta tilde en 'guía'); se corrige análogamente a otros typos en el gold."),
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

    # Verificación: type distribution
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
