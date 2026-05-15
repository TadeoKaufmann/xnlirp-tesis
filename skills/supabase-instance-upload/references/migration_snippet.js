// === Migración del app validation_app/index.html ===
// Reemplazar la const INSTANCES hardcoded por carga desde Supabase.
// Aplicar una sola vez. Después, todos los uploads de instancias son via SQL.

// 1. Reemplazar la declaración `const INSTANCES = [...]` por:
let INSTANCES = [];

// 2. Agregar función de carga (cerca de createClient):
async function loadInstances() {
  const { data, error } = await sb
    .from('instancias')
    .select('idx, prem, hyp');
  if (error) {
    console.error('Error cargando instancias desde Supabase:', error);
    throw error;
  }
  INSTANCES = data || [];
  console.log(`Cargadas ${INSTANCES.length} instancias desde Supabase`);
}

// 3. Antes del flujo principal (init/boot), llamar await loadInstances():
async function init() {
  try {
    await loadInstances();
    // resto del flujo de inicialización
  } catch (e) {
    document.getElementById('welcome-stats').textContent = 'Error cargando instancias — recargá';
  }
}

// 4. Eliminar el array literal (~60-300 líneas según batch).
