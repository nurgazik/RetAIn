"""Founder's blind labels: the ground truth the grader is checked against.
`label` writes output/evals/label.html — highlighted words from graded runs, model names
hidden, order shuffled; answers save in the browser and export as labels.json.
`labels <file>` imports them. `report` shows grader-vs-founder agreement (Cohen's kappa:
agreement corrected for chance; ~0.6+ is usually read as substantial)."""
import html as html_mod
import json
import pathlib
import random
from collections import Counter

from . import dataset, results

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
PAGE = ROOT / "output" / "evals" / "label.html"
VERDICTS = ("idiomatic", "acceptable", "wrong")


def latest_runs(con) -> list:
    """Latest finished run per model on the current dataset version."""
    return con.execute("SELECT max(id) id, model_name FROM runs WHERE dataset=? AND finished_at IS NOT NULL "
                       "GROUP BY model_name", (dataset.version(),)).fetchall()


def write_page(n: int = 150) -> None:
    con = results.connect()
    runs = latest_runs(con)
    per_run = max(1, n // max(1, len(runs)))
    rng = random.Random(7)
    items = []
    for run in runs:
        rows = con.execute("SELECT run_id, piece_id, n, word, sentence FROM marks "
                           "WHERE run_id=? AND verdict IS NOT NULL AND human IS NULL", (run["id"],)).fetchall()
        items += rng.sample(rows, min(per_run, len(rows)))
    rng.shuffle(items)
    defs = {w["word"][:6].lower(): w["definition"] for w in dataset.load_words()}
    cards = []
    for r in items:
        key = f"{r['run_id']}:{r['piece_id']}:{r['n']}"
        word = html_mod.escape(r["word"])
        sentence = html_mod.escape(r["sentence"]).replace(word, f"<mark>{word}</mark>", 1)
        definition = html_mod.escape(defs.get(r["word"][:6].lower(), ""))
        cards.append(f'<div class="card" data-key="{key}"><p>{sentence}</p>'
                     f'<div class="def"><b>{word}</b>: {definition}</div><div class="btns">'
                     + "".join(f'<button data-v="{v}">{i + 1} · {v}</button>' for i, v in enumerate(VERDICTS))
                     + "</div></div>")
    PAGE.parent.mkdir(parents=True, exist_ok=True)
    PAGE.write_text(f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Word labels</title>
<style>
:root {{ --bg:#faf8f4; --fg:#26221c; --muted:#6d675e; --card:#fff; --line:#ddd5c8; --hl:#ffe08a; --on:#8a6d3b; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#1c1a17; --fg:#eee8dd; --muted:#a39c90; --card:#26231f;
  --line:#3a352e; --hl:#7a6420; --on:#d7b36a; }} }}
body {{ font-family: Georgia, serif; background:var(--bg); color:var(--fg); margin:0; padding:1.5rem 16px 5rem; }}
.wrap {{ max-width: 680px; margin: 0 auto; }}
h1 {{ font: 600 1.2rem -apple-system, sans-serif; }}
.intro, .def, .bar {{ font-family: -apple-system, sans-serif; color: var(--muted); font-size: .88rem; }}
.card {{ background: var(--card); border: 1px solid var(--line); border-radius: 10px; padding: 1rem; margin: 1rem 0; }}
.card.done {{ opacity: .55; }}
.card p {{ font-size: 1.08rem; line-height: 1.6; margin: 0 0 .6rem; }}
mark {{ background: linear-gradient(transparent 55%, var(--hl) 55%); color: inherit; }}
.btns {{ display: flex; gap: .5rem; flex-wrap: wrap; margin-top: .7rem; }}
button {{ font: .9rem -apple-system, sans-serif; padding: .45rem .8rem; border-radius: 8px;
  border: 1px solid var(--line); background: transparent; color: var(--fg); cursor: pointer; }}
button.on {{ background: var(--on); color: var(--bg); border-color: var(--on); }}
.bar {{ position: fixed; bottom: 0; left: 0; right: 0; background: var(--bg); border-top: 1px solid var(--line);
  padding: .7rem 16px; display: flex; justify-content: space-between; align-items: center; }}
</style></head><body><div class="wrap">
<h1>Blind word labels ({len(cards)})</h1>
<p class="intro">Each card is one highlighted word from some model's output; models are hidden and
shuffled. <b>idiomatic</b>: exactly how a careful native writer would put it. <b>acceptable</b>:
correct but a bit forced. <b>wrong</b>: a learner copying it would learn wrong usage.
Keys 1/2/3 label the next open card. Answers save in this browser; press Export when done.</p>
{''.join(cards)}
</div><div class="bar"><span id="count"></span><button id="export">Export labels.json</button></div>
<script>
const K = 'retain-labels'; let L = {{}};
try {{ L = JSON.parse(localStorage.getItem(K) || '{{}}'); }} catch (e) {{}}
const save = () => {{ try {{ localStorage.setItem(K, JSON.stringify(L)); }} catch (e) {{}} }};
const cards = [...document.querySelectorAll('.card')];
function paint() {{
  cards.forEach(c => {{ const v = L[c.dataset.key]; c.classList.toggle('done', !!v);
    c.querySelectorAll('button').forEach(b => b.classList.toggle('on', b.dataset.v === v)); }});
  document.getElementById('count').textContent = Object.keys(L).length + ' / ' + cards.length + ' labelled';
}}
cards.forEach(c => c.querySelectorAll('button').forEach(b => b.onclick = () => {{ L[c.dataset.key] = b.dataset.v; save(); paint(); }}));
document.addEventListener('keydown', e => {{
  const v = {{'1':'idiomatic','2':'acceptable','3':'wrong'}}[e.key]; if (!v) return;
  const c = cards.find(c => !L[c.dataset.key]); if (!c) return;
  L[c.dataset.key] = v; save(); paint(); c.scrollIntoView({{block: 'center'}});
}});
document.getElementById('export').onclick = () => {{
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([JSON.stringify(L, null, 1)], {{type: 'application/json'}}));
  a.download = 'labels.json'; a.click();
}};
paint();
</script></body></html>""")
    print(f"[label] wrote {PAGE} ({len(cards)} words from {len(runs)} runs)")


def import_labels(path: str) -> None:
    con = results.connect()
    labels = json.loads(pathlib.Path(path).read_text())
    for key, v in labels.items():
        run_id, piece_id, n = key.split(":", 2)
        if v in VERDICTS:
            con.execute("UPDATE marks SET human=? WHERE run_id=? AND piece_id=? AND n=?",
                        (v, int(run_id), piece_id, int(n)))
    con.commit()
    print(f"[label] imported {len(labels)} labels")


def kappa(pairs: list) -> float:
    """Cohen's kappa for (a, b) label pairs."""
    if not pairs:
        return None
    n = len(pairs)
    observed = sum(a == b for a, b in pairs) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    expected = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return 1.0 if expected == 1 else (observed - expected) / (1 - expected)


def agreement(con) -> dict:
    pairs = [(r["human"], r["verdict"]) for r in con.execute(
        "SELECT human, verdict FROM marks WHERE human IS NOT NULL AND verdict IS NOT NULL")]
    wrong = [(a == "wrong", b == "wrong") for a, b in pairs]
    return {"n": len(pairs), "exact": pairs and sum(a == b for a, b in pairs) / len(pairs),
            "kappa": kappa(pairs), "kappa_wrong": kappa(wrong)}
