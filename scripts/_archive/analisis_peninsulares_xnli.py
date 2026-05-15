"""
Analiza frecuencia de peninsularismos en el corpus XNLI ES completo.
Muestra: ocurrencias por palabra, ratio ES/RP, ejemplos en contexto.
"""
import json
import re
import sys
from pathlib import Path
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')

INPUT = Path("data/raw/xnli/xnli_full_7500.jsonl")

# (peninsular, [rioplatense], nota)
PARES = [
    # Lista B vigente
    ("aquí",         ["acá"],                       "adverbio lugar"),
    ("allí",         ["ahí", "allá"],                "adverbio lugar"),
    ("coche",        ["auto"],                       "vehículo"),
    ("autobús",      ["colectivo"],                  "transporte"),
    ("piso",         ["departamento"],               "vivienda"),
    ("coger",        ["agarrar", "tomar"],            "verbo"),
    ("ordenador",    ["computadora"],                "tecnología"),
    ("móvil",        ["celular"],                    "teléfono"),
    ("conducir",     ["manejar"],                    "verbo"),
    ("aparcar",      ["estacionar"],                 "verbo"),
    ("enfadado",     ["enojado"],                    "emoción"),
    ("vestíbulo",    ["hall"],                       "arquitectura"),
    ("coste",        ["costo"],                      "economía"),
    ("chaqueta",     ["campera"],                    "ropa"),
    ("ello",         ["eso"],                        "pronombre"),
    ("bachillerato", ["secundario"],                 "educación"),
    ("repleto",      ["lleno"],                      "estado"),
    ("recoger",      ["levantar", "juntar"],          "verbo"),
    ("enviar",       ["mandar"],                     "comunicación"),
    ("pequeño",      ["chico"],                      "tamaño/edad"),
    ("padre",        ["papá"],                       "familiar"),
    ("madre",        ["mamá"],                       "familiar"),
    ("joven",        ["chico", "adolescente"],        "edad"),
    ("recordar",     ["acordarse"],                  "memoria"),
    ("vale",         ["dale", "bueno"],              "afirmación"),
    # 5 candidatos nuevos
    ("acera",        ["vereda"],                     "calle — candidato nuevo"),
    ("gafas",        ["anteojos", "lentes"],          "óptica — candidato nuevo"),
    ("zumo",         ["jugo"],                       "bebida — candidato nuevo"),
    ("patata",       ["papa"],                       "comida — candidato nuevo"),
    ("calcetín",     ["media"],                      "ropa — candidato nuevo"),
    # Otros peninsularismos potenciales
    ("vosotros",     ["ustedes"],                    "pronombre plural"),
    ("carretera",    ["ruta", "autopista"],           "vía"),
    ("bolso",        ["cartera"],                    "accesorio"),
    ("tío",          ["tipo", "pibe"],               "coloquial"),
    ("jersey",       ["buzo", "pulóver"],             "ropa"),
    ("frigorífico",  ["heladera"],                   "electrodoméstico"),
    ("ascensor",     ["ascensor", "elevador"],        "edificio — control"),
    ("boli",         ["lapicera", "birome"],          "escritura"),
    ("pasta",        ["plata", "guita"],             "dinero coloquial"),
    ("zumo",         ["jugo"],                       "bebida"),
    ("portátil",     ["notebook", "laptop"],          "tecnología"),
    ("bocadillo",    ["sándwich"],                   "comida"),
    ("melocotón",    ["durazno"],                    "fruta"),
    ("cacahuete",    ["maní"],                       "fruta seca"),
    ("tarta",        ["torta"],                      "repostería"),
]

# Eliminar duplicados manteniendo orden
seen = set()
PARES_UNICOS = []
for p in PARES:
    if p[0] not in seen:
        PARES_UNICOS.append(p)
        seen.add(p[0])

def load_sentences(path):
    sentences = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            sentences.append(r["prem_es"])
            sentences.append(r["hyp_es"])
    return sentences

def count_word(word, sentences):
    pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
    hits = []
    for s in sentences:
        matches = pattern.findall(s)
        if matches:
            hits.append(s)
    return len(hits), hits

def main():
    if not INPUT.exists():
        print(f"ERROR: {INPUT} no existe. Corré primero download_xnli_full.py")
        return

    print(f"Cargando {INPUT}...")
    sentences = load_sentences(INPUT)
    n_inst = len(sentences) // 2
    print(f"  {n_inst} instancias → {len(sentences)} oraciones\n")

    results = []
    for es, rps, nota in PARES_UNICOS:
        cnt_es, ctx_es = count_word(es, sentences)
        cnt_rp = sum(count_word(rp, sentences)[0] for rp in rps)
        results.append((cnt_es, es, rps, cnt_rp, nota, ctx_es))

    results.sort(reverse=True)

    print(f"{'PENINSULAR':<16} {'OCURR':>6}  {'RP':>22} {'RP_CNT':>7}  {'%_inst':>6}  NOTA")
    print("-" * 85)
    for cnt_es, es, rps, cnt_rp, nota, _ in results:
        pct = cnt_es / n_inst * 100
        rp_str = "/".join(rps)
        marker = " ◄ NUEVO" if "candidato nuevo" in nota else ""
        print(f"{es:<16} {cnt_es:>6}  {rp_str:>22} {cnt_rp:>7}  {pct:>5.1f}%  {nota}{marker}")

    print(f"\n{'='*85}")
    print("TOP 10 CON OCURRENCIAS — ejemplos en contexto")
    print(f"{'='*85}")
    top = [(cnt, es, rps, nota, ctx) for cnt, es, rps, _, nota, ctx in results if cnt > 0][:10]
    for cnt, es, rps, nota, ctx in top:
        print(f"\n[{es} → {'/'.join(rps)}] ({cnt} oraciones)")
        for ex in ctx[:3]:
            print(f"  • {ex[:120]}")

if __name__ == "__main__":
    main()
