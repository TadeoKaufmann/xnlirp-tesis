"""
Genera HTML lado a lado para revisión manual cómoda.
Filtros por tipo, estado y Levenshtein.
"""
import argparse
import html
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = REPO_ROOT / "results"


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def diff_highlight(es: str, rp: str) -> tuple[str, str]:
    """Resalta diferencias palabra a palabra muy ingenuamente."""
    es_words = es.split()
    rp_words = rp.split()
    es_html, rp_html = [], []
    # Diff naive por longest common subsequence aproximado: marcamos lo que difiere posicionalmente.
    # Para una visualización útil, mejor usar SequenceMatcher.
    from difflib import SequenceMatcher
    sm = SequenceMatcher(None, es_words, rp_words)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        es_seg = " ".join(es_words[i1:i2])
        rp_seg = " ".join(rp_words[j1:j2])
        if tag == "equal":
            es_html.append(html.escape(es_seg))
            rp_html.append(html.escape(rp_seg))
        elif tag == "replace":
            es_html.append(f"<span class='del'>{html.escape(es_seg)}</span>")
            rp_html.append(f"<span class='ins'>{html.escape(rp_seg)}</span>")
        elif tag == "delete":
            es_html.append(f"<span class='del'>{html.escape(es_seg)}</span>")
        elif tag == "insert":
            rp_html.append(f"<span class='ins'>{html.escape(rp_seg)}</span>")
    return " ".join(es_html), " ".join(rp_html)


def render_html(rows: list[dict], review_lookup: dict, title: str, storage_key: str = "") -> str:
    import re as _re
    if not storage_key:
        storage_key = "xnliNotes_" + _re.sub(r"[^a-zA-Z0-9_]", "_", title)[:60]

    css = """
    <style>
      body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 24px; background:#fafafa; color:#111; }
      h1 { margin-bottom: 8px; }
      .filters { background:#fff; padding:12px 16px; border-radius:8px; margin-bottom:16px; box-shadow:0 1px 3px rgba(0,0,0,0.06); position:sticky; top:0; z-index:10; display:flex; align-items:center; flex-wrap:wrap; gap:8px; }
      .filters label { margin-right: 4px; font-size: 14px; }
      .export-btn { margin-left:auto; padding:6px 14px; background:#1a73e8; color:#fff; border:none; border-radius:6px; font-size:13px; font-weight:600; cursor:pointer; }
      .export-btn:hover { background:#1558b0; }
      .card { background:#fff; border-radius:10px; padding:16px 20px; margin-bottom:14px; box-shadow:0 1px 3px rgba(0,0,0,0.06); }
      .card[data-has-note='1'] { border-left:3px solid #fbbc04; }
      .meta { font-size:12px; color:#555; margin-bottom:8px; display:flex; gap:14px; flex-wrap:wrap; }
      .badge { padding:2px 8px; border-radius:10px; background:#eef; font-weight:600; font-size:11px; text-transform:uppercase; }
      .badge.A { background:#e0e0e0; }
      .badge.B { background:#cfe8ff; }
      .badge.C { background:#ffe0b2; }
      .badge.D { background:#ffcdd2; }
      .badge.OK { background:#c8e6c9; }
      .badge.REVIEW { background:#fff59d; }
      .badge.ERROR { background:#ef9a9a; }
      .grid { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
      .col h3 { margin: 0 0 6px 0; font-size:13px; color:#444; text-transform:uppercase; letter-spacing:0.05em; }
      .text { font-size:15px; line-height:1.5; }
      .del { background:#ffd6d6; text-decoration:line-through; }
      .ins { background:#d6f5d6; font-weight:500; }
      .changes { font-size:12px; color:#444; margin-top:10px; }
      .changes ul { margin:4px 0 0 18px; padding:0; }
      .cc { font-size:12px; color:#7a4a00; background:#fff3e0; padding:6px 10px; border-radius:6px; margin-top:8px; }
      .notes-section { margin-top:10px; }
      .notes-ta { width:100%; box-sizing:border-box; min-height:38px; padding:7px 10px; font-size:13px; font-family:inherit; border:1px solid #ddd; border-radius:6px; background:#fffde7; resize:vertical; color:#333; }
      .notes-ta:focus { outline:none; border-color:#fbbc04; box-shadow:0 0 0 2px rgba(251,188,4,0.2); }
      .notes-ta::placeholder { color:#bbb; }
      .hidden { display:none; }
    </style>
    """

    js = f"""
    <script>
      const STORAGE_KEY = {json.dumps(storage_key)};

      function getNotes() {{
        try {{ return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{{}}'); }}
        catch {{ return {{}}; }}
      }}

      function saveNote(ta) {{
        const notes = getNotes();
        const idx = ta.dataset.idx;
        if (ta.value.trim()) {{ notes[idx] = ta.value; }} else {{ delete notes[idx]; }}
        localStorage.setItem(STORAGE_KEY, JSON.stringify(notes));
        ta.closest('.card').dataset.hasNote = ta.value.trim() ? '1' : '0';
        updateNoteCount();
      }}

      function loadNotes() {{
        const notes = getNotes();
        document.querySelectorAll('.notes-ta').forEach(ta => {{
          const v = notes[ta.dataset.idx] || '';
          ta.value = v;
          ta.closest('.card').dataset.hasNote = v.trim() ? '1' : '0';
          autoResize(ta);
        }});
        updateNoteCount();
      }}

      function autoResize(ta) {{
        ta.style.height = 'auto';
        ta.style.height = ta.scrollHeight + 'px';
      }}

      function updateNoteCount() {{
        const n = Object.keys(getNotes()).filter(k => getNotes()[k].trim()).length;
        document.getElementById('noteCount').textContent = n > 0 ? n + ' nota' + (n > 1 ? 's' : '') : '';
      }}

      function exportNotes() {{
        const notes = getNotes();
        const cards = {{}};
        document.querySelectorAll('.card').forEach(c => {{
          cards[c.dataset.idx] = {{ type: c.dataset.type, lev: c.dataset.lev }};
        }});
        const entries = Object.entries(notes)
          .filter(([, v]) => v.trim())
          .sort(([a], [b]) => parseInt(a) - parseInt(b))
          .map(([idx, note]) => JSON.stringify({{
            idx: parseInt(idx),
            type: (cards[idx] || {{}}).type || '?',
            note: note.trim()
          }}));
        if (!entries.length) {{ alert('No hay notas para exportar.'); return; }}
        const blob = new Blob([entries.join('\\n')], {{type: 'application/json'}});
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = 'corrections_{storage_key}.jsonl';
        a.click();
      }}

      function applyFilters() {{
        const t = document.getElementById('typeFilter').value;
        const s = document.getElementById('statusFilter').value;
        const lev = parseInt(document.getElementById('levFilter').value || '0', 10);
        const onlyNotes = document.getElementById('notesOnlyFilter').checked;
        document.querySelectorAll('.card').forEach(c => {{
          const ct = c.dataset.type;
          const cs = c.dataset.status;
          const cl = parseInt(c.dataset.lev, 10);
          const hn = c.dataset.hasNote === '1';
          let show = true;
          if (t !== 'all' && ct !== t) show = false;
          if (s !== 'all' && cs !== s) show = false;
          if (lev > 0 && cl < lev) show = false;
          if (onlyNotes && !hn) show = false;
          c.classList.toggle('hidden', !show);
        }});
      }}

      window.addEventListener('DOMContentLoaded', () => {{
        document.querySelectorAll('select, input[type=number]').forEach(el => el.addEventListener('change', applyFilters));
        document.getElementById('notesOnlyFilter').addEventListener('change', applyFilters);
        loadNotes();
      }});
    </script>
    """

    cards = []
    for row in rows:
        idx = row["idx"]
        t = row.get("type", "?")
        review = review_lookup.get(idx, {})
        if review.get("status") == "MISSING":
            status = "ERROR"
        elif review.get("status", "").startswith("⚠️"):
            status = "REVIEW"
        elif review.get("status", "").startswith("❌"):
            status = "ERROR"
        else:
            status = "OK"

        prem_html_es, prem_html_rp = diff_highlight(row.get("prem_es", ""), row.get("prem_rp", ""))
        hyp_html_es, hyp_html_rp = diff_highlight(row.get("hyp_es", ""), row.get("hyp_rp", ""))
        lev_total = row.get("lev_total", 0)

        changes_html = ""
        if row.get("changes"):
            items = "".join(f"<li>{html.escape(c)}</li>" for c in row["changes"])
            changes_html = f"<div class='changes'><strong>Cambios:</strong><ul>{items}</ul></div>"

        cc_html = ""
        if row.get("cultural_candidates"):
            cc_items = "".join(
                f"<div>• <code>{html.escape(c.get('original',''))}</code> → "
                f"<code>{html.escape(str(c.get('suggestion','—') or '—'))}</code> "
                f"<em>[{html.escape(c.get('category',''))}]</em></div>"
                for c in row["cultural_candidates"]
            )
            cc_html = f"<div class='cc'><strong>Cultural candidates:</strong>{cc_items}</div>"

        cards.append(f"""
        <div class='card' data-type='{t}' data-status='{status}' data-lev='{lev_total}' data-idx='{idx}' data-has-note='0'>
          <div class='meta'>
            <span><strong>idx {idx}</strong></span>
            <span>label: <code>{html.escape(row.get('label','?'))}</code></span>
            <span class='badge {t}'>{t}</span>
            <span class='badge {status}'>{status}</span>
            <span>lev: {lev_total}</span>
          </div>
          <div class='grid'>
            <div class='col'>
              <h3>ES (origen)</h3>
              <div class='text'><strong>P:</strong> {prem_html_es}</div>
              <div class='text'><strong>H:</strong> {hyp_html_es}</div>
            </div>
            <div class='col'>
              <h3>RP (adaptado)</h3>
              <div class='text'><strong>P:</strong> {prem_html_rp}</div>
              <div class='text'><strong>H:</strong> {hyp_html_rp}</div>
            </div>
          </div>
          {changes_html}
          {cc_html}
          <div class='notes-section'>
            <textarea class='notes-ta' data-idx='{idx}' placeholder='Nota / corrección (se guarda automáticamente)...' oninput='autoResize(this); saveNote(this)'></textarea>
          </div>
        </div>
        """)

    return f"""<!doctype html>
<html lang='es'><head><meta charset='utf-8'><title>{html.escape(title)}</title>{css}{js}</head>
<body>
  <h1>{html.escape(title)}</h1>
  <div class='filters'>
    <label>Tipo: <select id='typeFilter'>
      <option value='all'>Todos</option><option>A</option><option>B</option><option>C</option><option>D</option>
    </select></label>
    <label>Estado: <select id='statusFilter'>
      <option value='all'>Todos</option><option>OK</option><option>REVIEW</option><option>ERROR</option>
    </select></label>
    <label>Lev mínimo: <input type='number' id='levFilter' value='0' min='0' style='width:60px'></label>
    <label><input type='checkbox' id='notesOnlyFilter'> Solo con notas</label>
    <span style='font-size:12px;color:#666'>Total: {len(rows)} instancias</span>
    <span id='noteCount' style='font-size:12px;color:#e67e00;font-weight:600;margin-left:4px'></span>
    <button class='export-btn' onclick='exportNotes()'>&#8595; Exportar correcciones</button>
  </div>
  {''.join(cards)}
</body></html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Visualización HTML lado a lado.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--eval-md", type=Path, default=None,
                        help="Opcional: path a eval_*.md para extraer estados de revisión.")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--title", default="XNLIrp — Comparación ES vs RP")
    args = parser.parse_args()

    rows = load_jsonl(args.input)

    review_lookup = {}
    if args.eval_md and args.eval_md.exists():
        # Parseo simple: buscamos secciones "### idx N — STATUS"
        import re
        text = args.eval_md.read_text(encoding="utf-8")
        for m in re.finditer(r"### idx (\d+) — (.+)", text):
            review_lookup[int(m.group(1))] = {"status": m.group(2).strip()}

    out_path = args.out or (RESULTS_DIR / f"compare_{args.input.stem}.html")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_html(rows, review_lookup, args.title), encoding="utf-8")
    print(f"HTML escrito en: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
