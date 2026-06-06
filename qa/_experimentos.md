# Experimentos QA — ideas a explorar

## Contexto ET

20 cuentos del corpus tienen datos de eye-tracking (ET), 10 no tienen.

**Con ET:** Ahora debería reírme, Buenos Aires, Cómo funciona caminar en la nieve, Cómo funcionan los bolsillos, Educar para escalar y bucear, El almohadón de plumas, El espejo, El golpe de gracia, Embarrar la magia, La canción que cantábamos todos los días, La de la Obsesión por la Patineta, La gallina degollada, La lluvia de fuego, La máscara de la Muerte Roja, La noche de los feos, La salud de los enfermos, Las fotografías, Rubí y el lago danzante, Una rosa para Emilia, Wakefield

**Sin ET:** Axolotl, Bienvenido Bob, Carta a una señorita en París, Carta abierta, El loco cansino, El negro de París, El origen de las especies, Rebeca, Sombras sobre vidrio esmerilado 1, Sombras sobre vidrio esmerilado 2

---

## Experimentos posibles

### 1. ET vs no-ET en generalización
- Train: solo cuentos ET → Test: cuentos no-ET
- Hipótesis: el modelo entrenado en textos con ET generaliza peor a textos sin ET (distribución distinta)

### 2. Augmentación ET en cuentos con ET
- Train: cuentos ET sin augmentación → Test: cuentos ET
- Train: cuentos ET + augmentación ET → Test: cuentos ET
- Hipótesis central de la tesis: augmentación ET mejora el rendimiento en cuentos ET

### 3. Augmentación ET en cuentos sin ET
- Train: cuentos no-ET + augmentación ET de otros cuentos → Test: cuentos no-ET
- Hipótesis: si la augmentación ET ayuda en cuentos sin ET, el efecto es de regularización general, no específico al cuento

### 4. Low-resource (K-shot)
- Para K = 200, 500, 1000 instancias de train: ¿cuánto ayuda la augmentación ET?
- Esperado: mayor beneficio relativo en K bajo

### 5. Split ET/no-ET en test
- El test actual ya tiene 4 cuentos ET + 1 no-ET (Bienvenido Bob)
- Reportar métricas separadas: accuracy en ET vs no-ET dentro del mismo test set
- Campo `is_et` en cada instancia facilita este análisis (agregar en build_dataset.py)

---

## Notas de diseño

- Split actual: TEST tiene 4 ET + 1 no-ET → permite comparación directa
- El campo `is_et` se agrega en `build_dataset.py` al momento de ensamblar
- Para experimentos 1-3 se necesitan splits alternativos (no tocar el split canónico)
