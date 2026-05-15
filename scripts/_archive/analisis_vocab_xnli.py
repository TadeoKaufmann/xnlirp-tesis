"""
Extrae todas las palabras únicas del XNLI ES, las cruza contra:
  - EsPal latinoamericana (subconjunto Fermín, 8.5k palabras)
  - wordfreq español general (Zipf 0-7)
Marca las que ya están en la lista B y sugiere candidatos nuevos.
"""
import json, re, sys
from collections import Counter
from pathlib import Path
import pandas as pd
from wordfreq import zipf_frequency

sys.stdout.reconfigure(encoding='utf-8')

XNLI_PATH  = Path("data/raw/xnli/xnli_full_7500.jsonl")
ESPAL_PATH = Path(r"C:\Users\tadeo\Desktop\Tesis\proj fermin\metadata\texts_properties\words_freq.csv")

# Lista B vigente (formas peninsulares que ya manejamos)
LISTA_B_ES = {
    "aquí","allí","coche","autobús","piso","coger","ordenador","móvil",
    "conducir","enfadado","vestíbulo","coste","ello","bachillerato",
    "repleto","recoger","enviar","pequeño","padre","madre","joven",
    "recordar","vale","carretera","jersey","tío","vosotros",
    # formas morfológicas frecuentes
    "aquí","allí","allá","acá",
    "coches","autobuses","pisos","cogió","cogemos","coges","cogen",
    "ordenadores","móviles","conduce","conducen","enfadados","enfadada",
    "costes","ellos","bachilleratos","repleta","repletos","repletas",
    "recoge","recogen","recogió","enviaron","envió","enviamos",
    "pequeña","pequeños","pequeñas","padres","madres","jóvenes",
    "recuerdo","recuerda","recuerdan","carreteras","jerseys","tíos",
}

STOPWORDS_ES = {
    "de","la","el","en","y","a","los","las","del","se","un","una","es","por",
    "con","no","al","lo","le","más","pero","su","sus","o","si","ya","hay",
    "me","te","que","como","mi","tu","su","nos","os","les","les","ser","estar",
    "ha","han","he","hemos","había","habían","fue","fueron","era","eran","tiene",
    "tienen","tenía","tenían","hace","hacen","hacía","este","esta","estos","estas",
    "ese","esa","esos","esas","uno","dos","tres","son","muy","todo","todos","toda",
    "todas","para","sobre","también","cuando","donde","quien","qué","cómo","cuándo",
    "porque","aunque","hasta","desde","entre","sin","ante","bajo","contra","durante",
    "mediante","según","tras","bien","así","aún","antes","después","siempre","nunca",
    "aqui","aca","ahi","alla","donde","aquí","acá","ahí","allá","allí",
}

def tokenize(text):
    return re.findall(r'\b[a-záéíóúüñ]+\b', text.lower())

# Cargar corpus
print("Cargando XNLI...")
word_counter = Counter()
with open(XNLI_PATH, encoding='utf-8') as f:
    for line in f:
        r = json.loads(line)
        for campo in [r['prem_es'], r['hyp_es']]:
            word_counter.update(tokenize(campo))

total_tokens = sum(word_counter.values())
print(f"  {total_tokens:,} tokens, {len(word_counter):,} palabras únicas")

# Cargar EsPal
freq_df = pd.read_csv(ESPAL_PATH)
espal_dict = dict(zip(freq_df['word'].str.lower(), freq_df['cnt']))

# Analizar palabras con ≥ 5 ocurrencias en XNLI, excluyendo stopwords
MIN_XNLI = 5
candidatos = [
    (word, cnt) for word, cnt in word_counter.items()
    if cnt >= MIN_XNLI and word not in STOPWORDS_ES and len(word) > 3
]
candidatos.sort(key=lambda x: -x[1])

print(f"\n  {len(candidatos):,} palabras con ≥{MIN_XNLI} ocurrencias (sin stopwords)\n")

# Tabla completa
print(f"{'PALABRA':<20} {'XNLI':>6} {'ESPAL_LA':>10} {'ZIPF_ES':>8}  {'EN_B':>5}  SEÑAL")
print("-" * 70)

no_en_espal = []
for word, cnt in candidatos[:200]:  # top 200
    espal = espal_dict.get(word)
    zipf  = zipf_frequency(word, 'es')
    en_b  = "✓" if word in LISTA_B_ES else ""

    # Señal de sospecha: alta frecuencia en XNLI + baja en LA
    if espal is not None:
        if espal <= 100:
            senal = "RARO_LA"
        elif espal <= 1000:
            senal = "bajo_LA"
        else:
            senal = ""
    else:
        no_en_espal.append((word, cnt, zipf))
        if zipf < 3.0:
            senal = "?_raro_ES"
        elif zipf < 3.8:
            senal = "?_medio"
        else:
            senal = "no_en_Fermín"

    espal_str = f"{espal:,}" if espal else "—"
    print(f"{word:<20} {cnt:>6} {espal_str:>10} {zipf:>8.2f}  {en_b:>5}  {senal}")

# Palabras que no están en EsPal pero sí aparecen mucho en XNLI
# ordenadas por zipf bajo (más sospechosas)
print(f"\n{'='*70}")
print(f"PALABRAS NO EN SUBCONJUNTO ESPAL — ordenadas por menor frecuencia general")
print(f"(candidatos a peninsularismos o tecnicismos poco usados en LA)")
print(f"{'='*70}")
no_en_espal.sort(key=lambda x: x[2])  # menor zipf primero
print(f"{'PALABRA':<20} {'XNLI':>6} {'ZIPF_ES':>8}  {'EN_B':>5}")
print("-" * 45)
for word, cnt, zipf in no_en_espal[:60]:
    en_b = "✓" if word in LISTA_B_ES else ""
    print(f"{word:<20} {cnt:>6} {zipf:>8.2f}  {en_b:>5}")
