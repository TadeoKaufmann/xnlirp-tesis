"""
Escanea xnli_combined_dev_200.jsonl en busca de candidatos a tipo E:
  E.1) Nombres anglo comunes de persona (tabla cerrada del prompt v2)
  E.2) Festividades/referentes universales con equivalente directo

Imprime los idx con los matches encontrados, agrupados por categoría, para que
el anotador humano construya el gold cultural.
"""

import json
import re
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
import sys
DEV = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "data/processed/xnli_combined_dev_200.jsonl")

E1_NAMES = {
    "Joe": "José", "John": "Juan", "Bob": "Roberto",
    "Tom": "Tomás", "Mike": "Miguel", "Dave": "Diego",
    "Bill": "Guillermo", "Steve": "Esteban", "Paul": "Pablo",
    "Rick": "Ricardo", "Frank": "Francisco", "Tony": "Antonio",
    "Charlie": "Carlos", "Jack": "Joaquín", "Larry": "Lautaro",
    "Gary": "Gerardo", "Ron": "Ramón", "Pete": "Pedro",
    "Mary": "María", "Susan": "Susana", "Sue": "Susana",
    "Anne": "Ana", "Ann": "Ana", "Helen": "Elena",
    "Jenny": "Jésica",
    "Sam": "Samuel/Samanta",
    "Sarah": "Sara", "Kate": "Catalina", "Cathy": "Catalina",
}

E2_REFERENTS = {
    "Santa Claus": "Papá Noel",
    "Father Christmas": "Papá Noel",
    "Easter Bunny": "conejo de Pascua",
}

GENERIC_NAMES_TO_FLAG_AS_UNKNOWN = [
    "Donny", "Liz", "Greg", "Hank", "Brad", "Doug", "Phil", "Stan", "Ed",
    "Eddie", "Walt", "Wally", "Lenny", "Marty", "Sandy", "Wendy", "Holly",
    "Peggy", "Becky", "Dolly", "Polly", "Ruthie", "Gracie", "Ogle",
]

def main():
    matches_e1 = defaultdict(list)
    matches_e2 = defaultdict(list)
    matches_unknown = defaultdict(list)
    all_capitalized = defaultdict(list)

    with open(DEV, encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            idx = row["idx"]
            text = row.get("prem_es", "") + " || " + row.get("hyp_es", "")

            for name, equiv in E1_NAMES.items():
                if re.search(rf"\b{name}\b", text):
                    matches_e1[name].append((idx, equiv, text[:160]))

            for ref, equiv in E2_REFERENTS.items():
                if ref.lower() in text.lower():
                    matches_e2[ref].append((idx, equiv, text[:160]))

            for unk in GENERIC_NAMES_TO_FLAG_AS_UNKNOWN:
                if re.search(rf"\b{unk}\b", text):
                    matches_unknown[unk].append((idx, "?", text[:160]))

            for cap in re.findall(r"\b[A-Z][a-z]{2,12}\b", text):
                if cap not in {"Sin", "Las", "Los", "Una", "Uno", "Mi", "Su",
                               "Le", "El", "Del", "Bueno", "Pero", "Como",
                               "Todo", "Esto", "Eso", "Esa", "Esas", "Esos",
                               "Estos", "Estas", "Esta", "Cuando", "Después",
                               "Antes", "Texas", "Estados", "Unidos",
                               "España", "México", "Europa", "América",
                               "Africa", "China", "Italia", "Francia",
                               "Inglaterra", "París", "Londres",
                               "Madrid", "Buenos", "Aires"}:
                    all_capitalized[cap].append(idx)

    print("=" * 60)
    print("E.1 — NOMBRES ANGLO COMUNES (tabla cerrada del prompt v2)")
    print("=" * 60)
    for name, hits in sorted(matches_e1.items()):
        print(f"\n[{name} → {hits[0][1]}]  ({len(hits)} match{'es' if len(hits)>1 else ''})")
        for idx, equiv, snippet in hits[:5]:
            print(f"  idx {idx}: {snippet}")

    print("\n" + "=" * 60)
    print("E.2 — FESTIVIDADES/REFERENTES UNIVERSALES")
    print("=" * 60)
    for ref, hits in sorted(matches_e2.items()):
        print(f"\n[{ref} → {hits[0][1]}]  ({len(hits)} match{'es' if len(hits)>1 else ''})")
        for idx, equiv, snippet in hits:
            print(f"  idx {idx}: {snippet}")

    print("\n" + "=" * 60)
    print("Hipocorísticos anglo NO en tabla — candidatos a regla general E.1")
    print("(decisión humana: adaptar o marcar antroponimo_no_adaptable)")
    print("=" * 60)
    for name, hits in sorted(matches_unknown.items()):
        print(f"\n[{name}]  ({len(hits)} match{'es' if len(hits)>1 else ''})")
        for idx, _, snippet in hits[:5]:
            print(f"  idx {idx}: {snippet}")

    print("\n" + "=" * 60)
    print(f"E.1: {sum(len(v) for v in matches_e1.values())} ocurrencias en {len(set().union(*[{i for i,_,_ in v} for v in matches_e1.values()]))} idxs únicos")
    print(f"E.2: {sum(len(v) for v in matches_e2.values())} ocurrencias en {len(set().union(*[{i for i,_,_ in v} for v in matches_e2.values()]))} idxs únicos")
    print(f"Hipocorísticos no listados: {sum(len(v) for v in matches_unknown.values())} ocurrencias en {len(set().union(*[{i for i,_,_ in v} for v in matches_unknown.values()]) or [None])} idxs únicos")

if __name__ == "__main__":
    main()
