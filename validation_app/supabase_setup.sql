-- ============================================================
-- IDEMPOTENTE — se puede correr varias veces sin error.
-- DROP previo de instancias y reservas (NO toca Respuestas, que tiene datos).
-- ============================================================
DROP TABLE IF EXISTS public.reservas CASCADE;
DROP TABLE IF EXISTS public.instancias CASCADE;

-- ============================================================
-- 1. Tabla instancias
-- ============================================================
CREATE TABLE public.instancias (
  idx    INTEGER PRIMARY KEY,
  prem   TEXT    NOT NULL,
  hyp    TEXT    NOT NULL
);

-- RLS: cualquier anon puede leer, nadie puede escribir desde el cliente
ALTER TABLE public.instancias ENABLE ROW LEVEL SECURITY;
CREATE POLICY instancias_anon_read ON public.instancias
  FOR SELECT TO anon USING (true);

-- Datos: 90 instancias (batch 261-320 + 321-350, v2 rioplatense)
INSERT INTO public.instancias (idx, prem, hyp) VALUES
  (2078, 'Sofias, cerca de la estación de metro de Megaro Mousikis.', 'Sofias está a tiro de piedra de la estación de metro Megaro Mousikis.'),
  (4117, 'Cuando esta técnica funciona, obtenés una historia poderosa, aunque una cuyo tema no se revela hasta alrededor del tercer párrafo.', 'Esta técnica de escribir historias vale la pena cuando alcanzás el tercer párrafo.'),
  (59, 'Bueno, llegó hasta el punto en que hay dos o tres aeronaves que llegan en una semana y no sabía a dónde volaban.', 'Nunca llega ningún avión.'),
  (1619, 'Ha otorgado, según me han contado, la comisión del Rey a este hombre. Su propio tono traicionó la amargura de su rencor.', 'Usted ha concedido, según tengo entendido, la autorización del rey al hombre por su valentía.'),
  (4047, 'Sin embargo, hay un premio de consolación para la humanidad.', 'El premio de consolación es una licuadora de dos velocidades gratis para todos.'),
  (3446, 'Rababah, que había vivido en Connecticut, Nueva York, y en Nueva Jersey, dijo a los investigadores que había recomendado Paterson, en Nueva Jersey, como un lugar con una comunidad de habla árabe donde quizá Hazmi y Hanjour podrían querer asentarse.', 'Rababah recomendó que sólo permaneciesen en Nueva York.'),
  (90, '¡Y en realidad era ligera!', 'Comió mucha comida, pero no aumentó de peso.'),
  (1249, 'Los niños deberían llamar a la puerta de sus vecinos y', 'Los niños nunca pondrían un pie en la propiedad de sus vecinos.'),
  (2723, 'El tiempo desde la realización del pedido hasta la finalización de las actividades de puesta en marcha es de 46 semanas para ambas unidades.', 'Hay otras unidades que podrían completar estos pedidos más rápidamente por un precio más alto.'),
  (1754, 'Por fin le da un motivo de queja.', 'La muerte de un miembro de la familia le había causado mucha tristeza.'),
  (3877, '¿Buscás un poco de equilibrio?', 'Podemos ayudarte a conseguir equilibrio ahora mismo.'),
  (1335, 'Por tanto, a medida que aumenta la diversidad de objetos en la web, la diversidad de posibles nichos de nuevos bienes y servicios aumenta con más rapidez todavía.', 'Cuantos más objetos haya en la web, más difícil se hace la existencia de nichos de mercado.'),
  (2921, 'Retirada de bonos antes de fondos fiduciarios y fondos especiales (excepto los fondos fiduciarios rotatorios)', 'Los fideicomisos con fondos rotativos facilitan la obtención de tu dinero.'),
  (3652, ', clases más pequeñas, uso de tecnología), y pasar de una falta de espacio para apoyo a los estudiantes desde hace tiempo (casilleros, servicio de comidas, oficinas para organizaciones estudiantiles).', 'Hay muchos más casilleros de los que los estudiantes necesitarían en algún momento.'),
  (3661, 'En la celebración del 90º cumpleaños de la Escuela de Medicina de la Universidad de Indiana, vemos lo mucho que debemos a los soñadores y a sus sueños.', 'La Facultad de Medicina de la Universidad de Indiana debe mucho a los soñadores'),
  (3925, 'Con su membresía podrá acudir a actividades solo para miembros y tendrá credenciales completas para todas las sesiones de congresos oficiales.', 'Ingresará a los eventos sólo para miembros que se realizan cada dos semanas.'),
  (4556, 'No se sugiere que estos sujetos estén prohibidos, solo que es difícil, incluso después de veinte años de aculturización, que un forastero perciba mucho de lo que es divertido acerca de los suyos.', 'Estos temas son difíciles de entender para los forasteros.'),
  (3615, 'Los docentes con títulos de la Social Health Association ofrecen presentaciones en el colegio en tres', 'Todos los educadores tienen maestrías.'),
  (1310, 'Si Godzilla está mejor cuando se empareja con los ecovecinos de la primera especie que con esa especie, esa especie se extingue en su nicho y se ve reemplazada por Godzilla.', 'Es técnicamente imposible para una especie extinguirse.'),
  (4157, 'Rudolph Giuliani defiende su gestión en el manejo del tiroteo de Amadou Diallo en Newsweek. [El Departamento de Policía de Nueva York] no es el KKK, comenta.', 'Rudolph Giuliani hizo una declaración a la revista Newsweek sobre su manejo del tiroteo de Amadou Diallo.'),
  (1471, 'Tanto implícitamente como explícitamente, con trabajo modesto, el objeto del pistón puede descubrir que se encaja en el orificio del cilindro en el objeto del bloque del motor para crear un pistón completo en un cilindro.', 'El bloque del motor tiene un agujero en las motocicletas.'),
  (815, 'Bueno tengo una novia que tiene una hija adolescente y cada año antes de que empiece la escuela me pide que vaya con ella a comprar ropa porque discuten demasiado.', 'La hija de mi novia se niega a ir de compras conmigo.'),
  (4719, 'Él lo rimaba con pandemonium; a juzgar por las demandas que proliferan en los espacios de estacionamiento de condominio, barbacoas en el balcón y mascotas haciendo caca en los pasillos, podría haber tenido razón al usar el neologismo.', 'La convirtió en una palabra que rimaba.'),
  (2758, 'La siguiente figura ilustra las estructuras organizativas tradicionales centralizadas y descentralizadas, en comparación con la combinación híbrida utilizada hoy en día por las principales organizaciones.', 'Las organizaciones líderes usan un modelo híbrido.'),
  (4918, 'Parece ser una estación de paso entre el politeísmo y el monoteísmo, un concepto útil que representa un eslabón perdido en el proceso evolutivo.', 'Podría ser un intermedio entre el politeísmo y el monoteísmo.'),
  (954, 'sí, bueno, su nombre es Valen porque es acortamiento de Valentina y todo el mundo la trata como un tipo', 'Ella insiste en que todos usen su nombre completo.'),
  (2524, 'En consecuencia, los responsables de la toma de decisiones y los gerentes del gobierno están adoptando nuevas formas de pensar, considerando diferentes formas de lograr los objetivos y utilizando nueva información para guiar las decisiones.', 'Los representantes del gobierno intentan aumentar su poder pensando de manera diferente.'),
  (4075, 'Lawrence Singleton, un famoso violador que amputó los antebrazos de sus víctimas y luego pasó solo ocho años en prisión, fue detenido por apuñalar hasta la muerte de otra mujer en Florida.', 'Para todos era obvio que su tiempo en prisión lo había rehabilitado por completo.'),
  (4672, 'Todo el tiempo que estuve arrodillado con mi frente en la madera frente a mí, y estaba pensando en mí mientras rezaba, estaba un poco avergonzado.', 'Puse mi cabeza en el altar.'),
  (3261, 'Varios pisos de fuego hubieran superado la capacidad de extinción de incendios de las fuerzas disponibles', 'Todo el edificio podría haber ardido y hubiéramos podido extinguir los incendios.'),
  (3618, 'El año pasado, el 17 % del presupuesto de operaciones del museo vino de contribuciones de donantes leales.', 'El año pasado, menos de una cuarta parte del presupuesto operativo del museo provino de donaciones.'),
  (1603, 'Lo estuve buscando este año pasado.', 'Solo lo he estado siguiendo durante una semana.'),
  (3904, 'Incluso con la continua generosidad de los donantes, el museo tiene programas y operaciones que no reciben financiación todos los años.', 'Los museos no siempre obtienen todos los fondos que necesitan.'),
  (1254, 'No era una posición bicultural o binacional, sino una posición entre culturas, una posición que cuelga en el espacio.', 'Todo el mundo sabe que solo había una cultura.'),
  (1306, 'Por eso es tan desconcertante que el vestido y la decoración no combinen.', 'No es normal que el vestido y la decoración no estén en armonía.'),
  (2785, 'Un proveedor alemán de sistemas SCR, instaló SCR en una parte de la capacidad alemana dentro de los períodos de interrupción que constaban de menos de cuatro semanas.', 'Un sistema SCR alemán funciona en Alemania.'),
  (280, 'Su hermana pudo pasar por blanca, y de hecho pasó por blanca.', 'Generalmente se suponía que su hermana era blanca.'),
  (2090, 'El Teatro de Danza Folklórica Dora Stratou presenta interpretaciones de canciones, bailes y música tradicional griega en un auditorio de tipo folklórico tradicional en Philopappos Hill de mayo a septiembre, todos los días excepto los lunes.', 'Desde mayo hasta septiembre habrá actividades de danza en la colina Filopapos.'),
  (2601, 'Por ejemplo, una capital de estado que visitamos es el hogar de más de 600 compañías de software.', 'Las capitales son los mejores lugares para las compañías de software.'),
  (4722, 'Ella insistió en que él volara a casa, que significa que ella quería que volara a casa, aunque si lo hizo o no sería revelado en un capítulo posterior.', 'A pesar de que ella le dijo que volviera a casa, no está seguro si lo hizo o no.'),
  (3555, 'El acceso a nuestro recinto estará abierto a cualquier persona que disponga de una computadora y un módem.', 'La gente no necesita nada para acceder a los terrenos.'),
  (560, 'Acá están las cosas realmente mal, acaba de producirse un tiroteo en la autopista, a tres manzanas de nuestra casa.', 'Hubo un tiroteo cerca de mi casa, realmente no es bueno en esta área.'),
  (4223, 'Sospecho que parte de la respuesta es sociológica.', 'La cuestión está puramente basada en la psicología.'),
  (1842, 'Aunque incluso algunos de ellos deberían saberlo mejor, ya que todavía hay algunos en Barbados con nosotros, y se conocen con el Coronel Bishop, como vos y yo.', 'Ninguno de nosotros conoce al coronel Bishop.'),
  (4288, 'Ahora, estos no son problemas de los que los libertarios de torre de marfil harían caso.', 'Los libertarios de torre de marfil estarían interesados en estos temas.'),
  (1233, 'Sentado solo como juez de circuito, el Presidente Taney interpretó que la disposición constitucional requería autorización del Congreso para suspender el mandato.', 'Taney dijo que el Congreso podría detener la orden durante 10 minutos.'),
  (4641, 'Los oradores que quieren impresionar a sus audiencias saben que tienen que trasladar los puntos y los hechos clave, luego anunciarlos, repetirlos, dramatizarlos, explicarlos y embellecerlos.', 'La repetición es un elemento de las impresionantes técnicas del discurso.'),
  (3948, 'Si bien las cifras son impresionantes, las becas a menudo son críticas para reclutar a los mejores estudiantes con necesidades financieras.', 'Los mejores estudiantes con necesidades financieras se benefician de becas.'),
  (4348, 'Walcott se preparó para ser pintor (como su padre, maestro de escuela, que murió cuando Walcott era un bebé) y The Bounty es su libro más pictórico, en cuanto a método y tema.', 'El padre de Walcott prefirió su trabajo como pintor en vez de su trabajo como docente.'),
  (4409, 'La implicación más sorprendente de la teoría CMP es que la preocupación por la posición relativa desaparece en las sociedades donde las parejas son asignadas por mecanismos distintos a la riqueza.', 'La teoría de CMP es sobre cometas.'),
  (289, 'Y acá estoy pensando que va a venir como, ya sabés, para sacarlo conmigo, ya sabés, regañarme como si hubiera podido cambiarlo.', 'Pensé que venía para pelear.'),
  (1515, 'Ahí, a no más de tres millas de distancia, había tierra, una pared irregular de intenso color verde que llenaba el horizonte occidental.', 'Un paisaje exuberante estaba a la vista.'),
  (2633, 'La suspensión temporal de la representación legal durante la ausencia de un cliente buscando una continuación no es una alternativa viable para retirarse formalmente del caso.', 'No es bueno detener la representación legal.'),
  (3992, 'Por favor, dá ahora para que podamos seguir dándote a vos, a tus amigos y a tus vecinos.', 'Dejaremos de recaudar fondos si nos das 1000$ ahora.'),
  (493, 'Es lo suficientemente mayor como para ser mi papá.', 'Él es mucho más joven que yo.'),
  (4806, 'El tono de pulso no es un término técnico.', 'El manual técnico oficial indica que ''pulso-tono'' es el término correcto en este caso.'),
  (2452, 'El edificio une dos iglesias idénticas, la Franzoesischer Dom (o catedral francesa) al norte, construida para los inmigrantes hugonotes, y la Deutscher Dom (catedral alemana) al sur.', 'Ambas iglesias tienen agujas altas y grandes.'),
  (445, 'En cualquier caso, nos desplegamos, y puedo decir ahora que por este motivo nos desplegaron a Kadina, en Okinawa, y esto fue en 1968.', 'Nunca terminamos desplegando a nadie.'),
  (3242, 'La oficina legal del FBI en París se puso en contacto por primera vez con el Gobierno francés el 16 o 17 de agosto, poco después de hablar por teléfono con el agente del caso de Mineápolis.', 'El FBI abrió una oficina en París en 1925.'),
  (4111, 'Entonces, ¿por qué es mejor que convertirse en un abrigo de piel?', 'Si el animal ya está muerto y la piel se va a desechar o quemar si no se usa, ¿convertirla en una abrigo de piel es la mejor opción y una forma de reciclaje?'),
  (2496, 'Esto es nuevo para Hungría, y tendrás que ir manejando un rato por las afueras si querés jugar.', 'La ubicación de la obra está a una hora en auto.'),
  (3400, 'Antes del 9/11, ninguna agencia del gobierno de los E.U. analizó sistemáticamente las estrategias de viaje de los terroristas.', 'Las estrategias de viaje terrorista fueron una fuente importante de estudio del gobierno antes del 11 de septiembre.'),
  (4613, 'En los patios de las escuelas el ruido más fuerte-- bullicio --está cesando.', 'Hay mucho menos ruido en los patios de la escuela últimamente.'),
  (602, 'y ahora tengo una hermana en Alemania', 'Tengo una hermana que habla alemán.'),
  (2472, 'Bajo el altar, un disco de plata rodea un agujero que marca el lugar en el que, según la tradición, la cruz de Jesús se irguió junto con las de los dos ladrones a cada lado.', 'Los hombres al lado de Jesús eran malas personas.'),
  (580, 'sabés, todos mis hijos son geniales, muy buenos, y creo que no, aprende de los niños mayores también, pero', 'Estoy muy orgulloso de lo mucho que mis hijos saben.'),
  (952, 'sí, y cualquier momento en el que intentés ir al, este... los acomodadores siempre te dirían que volvieras', 'Los acomodadores no te dejan pasar al siguiente nivel del estadio.'),
  (4326, 'Para cantar que venga la buena fortuna a aquellos a los que temo,', 'Espero que esas personas a las que tengo miedo tengan buena suerte.'),
  (966, 'No consigo acordarme, solo hice esto una vez antes.', '¡Hice esto un millón de veces!'),
  (1800, 'Ya sabés, Pedro, que solo Lord Julian se ha interpuesto entre Bishop y su odio hacia vos.', 'Pedro es odiado por el Obispo.'),
  (4926, 'Pero, de hecho, estaría fingiendo ingenuidad al afirmar que ahora se entiende que al referirse a los ''hombres'', en general, se incluye también a las mujeres.', 'Los hombres sólo se refieren a lo masculino.'),
  (374, 'Y era como si rechazase quién era, de algún modo, por, ya sabés, la forma en que trataba, sabés, a los otros nietos.', 'Trataba a los otros nietos de forma diferente porque eran negros.'),
  (1221, 'El final del siglo XVIII fue de hecho un tiempo maravillosamente simplista.', 'Alguien recuerda finales del siglo XVIII.'),
  (1381, 'La mayoría de las casas tendrán un nacimiento preparado para las oraciones y los cantantes.', 'Las escenas de nacimientos son muy complejas.'),
  (2906, 'Los bomberos del condado de Baltimore no tienen un programa formal para proporcionar un impulso financiero a los bomberos y paramédicos que están lesionados y no pueden trabajar.', 'Debería existir un programa para compensar a estos funcionarios.'),
  (3742, '¡Es hora de la famosa ÚLTIMA LLAMADA!', '¡Es hora de la última llamada!'),
  (1645, 'Entonces solo fuiste un caballero desafortunado.', 'En el pasado eras un caballero desafortunado.'),
  (1626, 'Se dio cuenta de que tal vez ella misma había provocado su enojo.', 'Estaba enojado porque ella siempre habla demasiado.'),
  (266, 'El presidente Kennedy dice a los pilotos, dice, ''Caballeros, hacen buenas fotos''.', 'Kennedy habló con los pilotos.'),
  (155, 'Esta fue la primera vez que, eso había sucedido en 75 años, la legislatura de Texas había votado una unidad militar siendo Embajadores de Texas, por lo tanto, necesitaba embajadores de Texas.', 'La unidad militar fue llamada Embajadores TX.'),
  (1631, 'Siempre estaré agradecido.', 'Estaré por siempre lleno de malicia y odio.'),
  (419, 'No me importa cómo lo hagas.', 'Necesito saber exactamente cómo harás esto.'),
  (877, 'la mayor parte del tiempo cuando usted ve el colectivo uh usted sabe, los colectivos con el diésel, esto es uh aquellos son partículas de carbón y el dióxido de carbono uh y el vapor', 'Los colectivos funcionan con combustible diésel.'),
  (3351, 'En la lucha contra el terrorismo, estas distinciones parecen cada vez más artificiales.', 'Las distinciones parecen verdaderamente genuinas.'),
  (194, 'Se vive y se aprende, ya sabés, cuando probás, eh, avión.', 'Hacer pruebas en aviones te enseña a gestionar la presión.'),
  (2231, 'Los pescadores de río deben disponer de un permiso. Infórmese en la oficina de turismo más cercana para conseguirlo.', 'Tenés que tener un permiso para pescar peces de más de 6 pulgadas.'),
  (3930, '¿CUÁL ES EL DESAFÍO DE LOS MAYORES?', 'Hay un desafío para las personas mayores.'),
  (2755, '24 Estas características también serían apropiadas para los informes de responsabilidad del GMRA.', 'Hay otras características que también podrían usarse para los informes.'),
  (4817, 'En este caso, Skeat no ignorará esta nota y repetirá la ofensa en algún momento futuro.', 'Skeat estudiará la nota todos los días.'),
  (786, 'oh, ya veo, el estado no lo necesita, es como... es bastante... es bastante inusual, ¿no?', 'Incluso si no es obligatorio, debe hacerse.');

-- ============================================================
-- 2. Tabla reservas (anti-race-condition)
-- ============================================================
CREATE TABLE public.reservas (
  idx         INTEGER      PRIMARY KEY,
  anotador_id TEXT         NOT NULL,
  created_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- RLS: anon puede leer, insertar, actualizar y BORRAR solo reservas expiradas (>2h)
ALTER TABLE public.reservas ENABLE ROW LEVEL SECURITY;
CREATE POLICY reservas_anon_read ON public.reservas
  FOR SELECT TO anon USING (true);
CREATE POLICY reservas_anon_insert ON public.reservas
  FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY reservas_anon_update ON public.reservas
  FOR UPDATE TO anon USING (true);  -- la app controla el anotador_id
-- DELETE solo de reservas expiradas: cualquier cliente puede limpiar (>2h),
-- pero NO puede borrar reservas activas de otros anotadores.
CREATE POLICY reservas_anon_delete_expired ON public.reservas
  FOR DELETE TO anon USING (created_at < now() - interval '2 hours');

-- Índice para filtrar por created_at en queries de expiración
CREATE INDEX reservas_created_at_idx ON public.reservas (created_at);