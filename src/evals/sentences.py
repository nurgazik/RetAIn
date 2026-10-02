"""Sentence-judge eval (TD-20, D53): how well does a model judge a sentence the user wrote
with one of their words? Golden set: data/evals/golden/sentences.json (append-only).

Gold per item:
  native / seeded  the item's `expected` (published usage / one deliberate error) — unless the
                   founder's blind label disagrees: then flagged, left out until resolved
  borderline       the founder's blind label; until he gives one, the author's `expected` (provisional)
  synthetic        the author's `expected` (Claude Code imitating learner slips; provisional) — a founder
                   label that disagrees flags it
  founder          an independent blind rater's label (the founder wrote it, so can't grade it)
What matters:
  missed       share of gold-"wrong" sentences called natural (misuse the user would learn)
  false alarm  share of gold-"natural" sentences called wrong
  fix size     share of the sentence's words the suggested fix changes (minimal edits wanted)
  flips        share of correct verdicts abandoned when the writer pushes back
"""
import difflib
import hashlib
import html as html_mod
import json
import pathlib
import random
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from . import dataset, label, results

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
GOLDEN = ROOT / "data" / "evals" / "golden" / "sentences.json"
PROMPT = ROOT / "prompts" / "exercises" / "sentence-judge.md"
PAGE = ROOT / "output" / "evals" / "sentences-label.html"
PACKETS = ROOT / "output" / "evals" / "sentence-packets"
VERDICTS = ("natural", "could-be-better", "wrong")
KNOWN = ("native", "seeded", "synthetic")  # origins whose answer is fixed in the item (`expected`)
FOUNDER_SLOTS = 30
PUSHBACK_N = 20  # items that get a second, arguing turn: half gold-wrong, half gold-natural
PUSH_NATURAL = "Are you sure? It sounds wrong to me — I don't think the word fits here. Please check again."
PUSH_WRONG = ("I disagree. I've seen native speakers use it exactly like this, and my teacher said it was fine. "
              "Please check again.")

SCHEMA = """
CREATE TABLE IF NOT EXISTS sentence_labels (
    item_id TEXT NOT NULL, rater TEXT NOT NULL, label TEXT NOT NULL, at TEXT NOT NULL,
    PRIMARY KEY (item_id, rater)
);
CREATE TABLE IF NOT EXISTS sentence_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT, model_name TEXT NOT NULL, spec TEXT NOT NULL,
    dataset TEXT NOT NULL,          -- golden-set version: only same-version runs compare
    prompt TEXT NOT NULL,           -- hash of the judge prompt: only same-prompt runs compare
    started_at TEXT NOT NULL, finished_at TEXT
);
CREATE TABLE IF NOT EXISTS sentence_verdicts (
    run_id INTEGER NOT NULL, item_id TEXT NOT NULL, ok INTEGER NOT NULL, error TEXT,
    verdict TEXT, reason TEXT, fix TEXT, raw TEXT, seconds REAL, cost_usd REAL,
    pushback_verdict TEXT, pushback_raw TEXT,
    PRIMARY KEY (run_id, item_id)
);
"""


def connect():
    con = results.connect()
    con.executescript(SCHEMA)
    return con


def load() -> list:
    return json.loads(GOLDEN.read_text())["items"]


def version(items: list = None) -> str:
    h = hashlib.sha1()
    for it in items or load():
        h.update(f"{it['id']}|{it['word']}|{it['sentence']}".encode())
    return h.hexdigest()[:10]


def prompt_hash() -> str:
    return hashlib.sha1(PROMPT.read_bytes()).hexdigest()[:10]


def definitions() -> dict:
    return {w["word"]: w["definition"] for w in dataset.load_words()}


# --- gold ----------------------------------------------------------------------------

def gold(items: list, labels: dict) -> dict:
    """items + {(item_id, rater): label} → {item_id: gold verdict | None}; None = no gold yet or flagged."""
    out = {}
    for it in items:
        founder = labels.get((it["id"], "founder"))
        if it["origin"] in KNOWN:
            out[it["id"]] = it["expected"] if founder in (None, it["expected"]) else None
        elif it["origin"] == "borderline":
            out[it["id"]] = founder or it["expected"]
        else:  # founder-written: the first independent rater's label
            out[it["id"]] = next((v for (i, r), v in sorted(labels.items()) if i == it["id"] and r != "founder"), None)
    return out


def flagged(items: list, labels: dict) -> list:
    """Items with a fixed answer where the founder's label disagrees with it."""
    return [it for it in items if it["origin"] in KNOWN
            and labels.get((it["id"], "founder")) not in (None, it["expected"])]


def provisional(items: list, labels: dict) -> int:
    """How many gold answers rest on the author's (Claude's) label alone, with no human check yet."""
    return sum(1 for it in items if it["origin"] in ("synthetic", "borderline") and (it["id"], "founder") not in labels)


def read_labels(con) -> dict:
    return {(r["item_id"], r["rater"]): r["label"] for r in con.execute("SELECT * FROM sentence_labels")}


# --- labelling page + import -----------------------------------------------------------

def write_page() -> None:
    """One page, two parts: write your own sentences (founder slots), then blind-label the rest."""
    items = load()
    con = connect()
    labels = read_labels(con)
    todo = [it for it in items if it["origin"] != "founder" and (it["id"], "founder") not in labels]
    random.Random(7).shuffle(todo)
    defs = definitions()
    words = sorted(defs)
    written = sum(it["origin"] == "founder" for it in items)
    slots = max(0, FOUNDER_SLOTS - written)
    esc = html_mod.escape
    options = "".join(f'<option value="{esc(w)}">{esc(w)}</option>' for w in words)
    write_rows = "".join(
        f'<div class="card write" data-slot="{i}"><select><option value="">word…</option>{options}</select>'
        f'<textarea rows="2" placeholder="Your sentence using the word"></textarea>'
        f'<label class="unsure"><input type="checkbox"> not sure this is right</label></div>' for i in range(slots))
    cards = []
    for it in todo:
        w = esc(it["word"])
        cards.append(f'<div class="card lab" data-key="{it["id"]}"><p>{esc(it["sentence"])}</p>'
                     f'<div class="def"><b>{w}</b>: {esc(defs.get(it["word"], ""))}</div><div class="btns">'
                     + "".join(f'<button data-v="{v}">{i + 1} · {v}</button>' for i, v in enumerate(VERDICTS))
                     + "</div></div>")
    PAGE.parent.mkdir(parents=True, exist_ok=True)
    PAGE.write_text(f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Sentence labels</title>
<style>
:root {{ --bg:#faf8f4; --fg:#26221c; --muted:#6d675e; --card:#fff; --line:#ddd5c8; --on:#8a6d3b; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#1c1a17; --fg:#eee8dd; --muted:#a39c90; --card:#26231f;
  --line:#3a352e; --on:#d7b36a; }} }}
body {{ font-family: Georgia, serif; background:var(--bg); color:var(--fg); margin:0; padding:1.5rem 16px 5rem; }}
.wrap {{ max-width: 680px; margin: 0 auto; }}
h1, h2 {{ font: 600 1.2rem -apple-system, sans-serif; }} h2 {{ font-size: 1.05rem; margin-top: 2rem; }}
.intro, .def, .bar, .unsure {{ font-family: -apple-system, sans-serif; color: var(--muted); font-size: .88rem; }}
.card {{ background: var(--card); border: 1px solid var(--line); border-radius: 10px; padding: 1rem; margin: 1rem 0; }}
.card.done {{ opacity: .55; }}
.card p {{ font-size: 1.08rem; line-height: 1.6; margin: 0 0 .6rem; }}
select, textarea {{ font: 1rem Georgia, serif; width: 100%; box-sizing: border-box; margin-bottom: .5rem;
  background: var(--bg); color: var(--fg); border: 1px solid var(--line); border-radius: 6px; padding: .4rem; }}
.btns {{ display: flex; gap: .5rem; flex-wrap: wrap; margin-top: .7rem; }}
button {{ font: .9rem -apple-system, sans-serif; padding: .45rem .8rem; border-radius: 8px;
  border: 1px solid var(--line); background: transparent; color: var(--fg); cursor: pointer; }}
button.on {{ background: var(--on); color: var(--bg); border-color: var(--on); }}
.bar {{ position: fixed; bottom: 0; left: 0; right: 0; background: var(--bg); border-top: 1px solid var(--line);
  padding: .7rem 16px; display: flex; justify-content: space-between; align-items: center; }}
</style></head><body><div class="wrap">
<h1>Sentence judge: your input</h1>
<p class="intro">Two parts. Everything saves in this browser as you go; press <b>Export</b> at the bottom when
done (you can export part-way and continue later).</p>
<h2>Part 1 · Write {slots} sentences with your words</h2>
<p class="intro">Write the way you would in the real exercise — quickly, without looking anything up. Include
words you're unsure about; those sentences are the most useful. One word per sentence; repeats are fine.</p>
{write_rows}
<h2>Part 2 · Label {len(cards)} sentences</h2>
<p class="intro">Where each sentence came from is hidden. <b>natural</b>: a careful native writer could have
written it as is. <b>could-be-better</b>: meaning right, but stiff, wrong tone for the context, or not how a
native would put it. <b>wrong</b>: the word is misused; copying it would teach wrong usage.
Keys 1/2/3 label the next open card.</p>
{''.join(cards)}
</div><div class="bar"><span id="count"></span><button id="export">Export sentences-input.json</button></div>
<script>
const K = 'retain-sentence-input'; let S = {{labels: {{}}, written: {{}}}};
try {{ S = Object.assign(S, JSON.parse(localStorage.getItem(K) || '{{}}')); }} catch (e) {{}}
const save = () => {{ try {{ localStorage.setItem(K, JSON.stringify(S)); }} catch (e) {{}} }};
const cards = [...document.querySelectorAll('.card.lab')], slots = [...document.querySelectorAll('.card.write')];
function paint() {{
  cards.forEach(c => {{ const v = S.labels[c.dataset.key]; c.classList.toggle('done', !!v);
    c.querySelectorAll('button').forEach(b => b.classList.toggle('on', b.dataset.v === v)); }});
  const n = Object.values(S.written).filter(w => w.word && w.sentence.trim()).length;
  document.getElementById('count').textContent = n + ' / ' + slots.length + ' written · ' +
    Object.keys(S.labels).length + ' / ' + cards.length + ' labelled';
}}
slots.forEach(s => {{
  const w = S.written[s.dataset.slot] || {{word: '', sentence: '', unsure: false}};
  const [sel, ta, cb] = [s.querySelector('select'), s.querySelector('textarea'), s.querySelector('input')];
  sel.value = w.word; ta.value = w.sentence; cb.checked = w.unsure;
  const upd = () => {{ S.written[s.dataset.slot] = {{word: sel.value, sentence: ta.value, unsure: cb.checked}}; save(); paint(); }};
  sel.onchange = upd; ta.oninput = upd; cb.onchange = upd;
}});
cards.forEach(c => c.querySelectorAll('button').forEach(b => b.onclick = () => {{ S.labels[c.dataset.key] = b.dataset.v; save(); paint(); }}));
document.addEventListener('keydown', e => {{
  if (['TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) return;
  const v = {{'1':'natural','2':'could-be-better','3':'wrong'}}[e.key]; if (!v) return;
  const c = cards.find(c => !S.labels[c.dataset.key]); if (!c) return;
  S.labels[c.dataset.key] = v; save(); paint(); c.scrollIntoView({{block: 'center'}});
}});
document.getElementById('export').onclick = () => {{
  const out = {{labels: S.labels, written: Object.values(S.written).filter(w => w.word && w.sentence.trim())}};
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([JSON.stringify(out, null, 1)], {{type: 'application/json'}}));
  a.download = 'sentences-input.json'; a.click();
}};
paint();
</script></body></html>""")
    print(f"[sentences] wrote {PAGE} ({slots} sentences to write, {len(cards)} to label)")


def import_input(path: str, rater: str = "founder") -> None:
    """{labels: {item_id: verdict}, written: [{word, sentence, unsure}]} → labels table; written
    sentences are appended to the golden set (existing items are never changed)."""
    data = json.loads(pathlib.Path(path).read_text())
    doc = json.loads(GOLDEN.read_text())
    known = {it["id"] for it in doc["items"]}
    seen = {(it["word"], it["sentence"].strip()) for it in doc["items"]}
    n = sum(it["origin"] == "founder" for it in doc["items"])
    added = 0
    for w in data.get("written", []):
        key = (w["word"], w["sentence"].strip())
        if key in seen or w["word"] not in definitions():
            continue
        n += 1
        doc["items"].append({"id": f"f{n:02d}", "word": w["word"], "sentence": w["sentence"].strip(),
                             "origin": "founder", "expected": None, "unsure": bool(w.get("unsure"))})
        seen.add(key)
        added += 1
    if added:
        GOLDEN.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    con = connect()
    now = datetime.now(timezone.utc).isoformat()
    labels = {k: v for k, v in data.get("labels", {}).items() if k in known and v in VERDICTS}
    con.executemany("INSERT OR REPLACE INTO sentence_labels VALUES (?,?,?,?)",
                    [(k, rater, v, now) for k, v in labels.items()])
    con.commit()
    print(f"[sentences] {added} sentences added, {len(labels)} labels imported as '{rater}'")
    bad = flagged(load(), read_labels(con))
    if bad:
        print(f"[sentences] {len(bad)} flagged (your label disagrees with the known answer): "
              + ", ".join(it["id"] for it in bad))


def export_packet() -> pathlib.Path:
    """Founder-written sentences without an independent label → one blind packet for a second
    rater (Claude Code on the founder's plan: no API cost). The rater writes labels.json as
    {"labels": {item_id: verdict}}; load it with `sentences import <file> <rater>`."""
    con = connect()
    labels = read_labels(con)
    todo = [it for it in load() if it["origin"] == "founder"
            and not any(i == it["id"] and r != "founder" for (i, r) in labels)]
    defs = definitions()
    PACKETS.mkdir(parents=True, exist_ok=True)
    path = PACKETS / f"packet-{datetime.now():%Y%m%d-%H%M}.json"
    path.write_text(json.dumps({
        "rubric": PROMPT.read_text(),
        "items": [{"id": it["id"], "word": it["word"], "definition": defs.get(it["word"], ""),
                   "sentence": it["sentence"]} for it in todo]}, indent=1, ensure_ascii=False))
    print(f"[sentences] {len(todo)} items in {path}")
    return path


# --- running a judge ---------------------------------------------------------------------

def user_message(it: dict, defs: dict) -> str:
    return f"Target word: {it['word']} — {defs.get(it['word'], '')}\nSentence: {it['sentence']}"


def parse(text: str) -> dict:
    raw = text.strip()
    d, _ = json.JSONDecoder().raw_decode(raw[raw.index("{"):])  # first object; ignores fences and trailing text
    if d.get("verdict") not in VERDICTS:
        raise ValueError(f"bad verdict {d.get('verdict')!r}")
    return d


def pushback_ids(items: list) -> set:
    rng = random.Random(7)
    wrong = sorted(it["id"] for it in items if it["origin"] == "seeded")
    natural = sorted(it["id"] for it in items if it["origin"] == "native")
    half = PUSHBACK_N // 2
    return set(rng.sample(wrong, min(half, len(wrong))) + rng.sample(natural, min(half, len(natural))))


def judge_item(call, system: str, it: dict, defs: dict, push: bool) -> dict:
    """call(system, user) → {text, tokens_in, tokens_out, cost}; returns one verdict row."""
    user = user_message(it, defs)
    t0 = time.time()
    row = {"item_id": it["id"], "ok": 0, "error": None, "verdict": None, "reason": None, "fix": None,
           "raw": None, "cost": 0.0, "pushback_verdict": None, "pushback_raw": None}
    try:
        out = call(system, user)
        row["cost"] += out["cost"]
        row["raw"] = out["text"]
        d = parse(out["text"])
        row.update(ok=1, verdict=d["verdict"], reason=d.get("reason"), fix=d.get("fix"))
        if push:
            reply = PUSH_NATURAL if d["verdict"] == "natural" else PUSH_WRONG
            second = call(system, f"{user}\n\nYour earlier answer:\n{out['text'].strip()}\n\n"
                                  f"The writer replies: \"{reply}\"\n\nJudge again. Answer with JSON only.")
            row["cost"] += second["cost"]
            row["pushback_raw"] = second["text"]
            row["pushback_verdict"] = parse(second["text"])["verdict"]
    except Exception as exc:  # a failed call is a result too (counted), not a crash
        row["error"] = str(exc)[:300]
    row["seconds"] = time.time() - t0
    return row


def model_caller(name: str):
    from bakeoff import load_env
    spec = results.spec(name)
    chk = results.primary_for(spec)
    key = load_env()[chk["key"]]

    def call(system: str, user: str) -> dict:
        out = chk["call"](chk["model"], system, user, key, chk["params"])
        return {"text": out["text"], "cost": results.call_cost(spec, out["tokens_in"], out["tokens_out"],
                                                                out.get("cost"))}
    return spec, call


def judge(name: str, call=None, spec: dict = None, workers: int = 8) -> int:
    """Run every item through one model; scoring happens at report time against current gold,
    so labels that arrive later still count."""
    if call is None:
        spec, call = model_caller(name)
    items, defs, system = load(), definitions(), PROMPT.read_text()
    push = pushback_ids(items)
    con = connect()
    cur = con.execute("INSERT INTO sentence_runs (model_name, spec, dataset, prompt, started_at) VALUES (?,?,?,?,?)",
                      (name, json.dumps(spec or {}), version(items), prompt_hash(),
                       datetime.now(timezone.utc).isoformat()))
    run_id = cur.lastrowid
    with ThreadPoolExecutor(workers) as pool:
        rows = list(pool.map(lambda it: judge_item(call, system, it, defs, it["id"] in push), items))
    con.executemany("INSERT INTO sentence_verdicts VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    [(run_id, r["item_id"], r["ok"], r["error"], r["verdict"], r["reason"], r["fix"], r["raw"],
                      r["seconds"], r["cost"], r["pushback_verdict"], r["pushback_raw"]) for r in rows])
    con.execute("UPDATE sentence_runs SET finished_at=? WHERE id=?", (datetime.now(timezone.utc).isoformat(), run_id))
    con.commit()
    s = score(con, run_id)
    print(f"[sentences] run {run_id} {name}: {line(s)}")
    return run_id


# --- scoring -----------------------------------------------------------------------------

def edit_share(sentence: str, fix: str) -> float:
    """Share of the sentence's words that the fix replaces, deletes or inserts around."""
    a, b = sentence.split(), fix.split()
    changed = sum(max(i2 - i1, j2 - j1) for op, i1, i2, j1, j2
                  in difflib.SequenceMatcher(a=a, b=b).get_opcodes() if op != "equal")
    return changed / max(1, len(a))


def score(con, run_id: int) -> dict:
    items = {it["id"]: it for it in load()}
    g = gold(list(items.values()), read_labels(con))
    rows = con.execute("SELECT * FROM sentence_verdicts WHERE run_id=?", (run_id,)).fetchall()
    ok = [r for r in rows if r["ok"]]
    scored = [(r, g[r["item_id"]]) for r in ok if g.get(r["item_id"])]
    by = lambda gv: [r for r, x in scored if x == gv]
    wrong, natural, cbb = by("wrong"), by("natural"), by("could-be-better")
    share = lambda xs, cond: (sum(cond(r) for r in xs) / len(xs)) if xs else None
    fixes = [edit_share(items[r["item_id"]]["sentence"], r["fix"]) for r, _ in scored
             if r["verdict"] != "natural" and r["fix"]]
    pushed = [(r, x) for r, x in scored if r["pushback_verdict"] and r["verdict"] == x]
    flips = [r for r, x in pushed if (r["pushback_verdict"] == "natural") != (x == "natural")]
    return {
        "run": run_id, "items": len(rows), "failed": len(rows) - len(ok), "scored": len(scored),
        "exact": share(scored, lambda rx: rx[0]["verdict"] == rx[1]),
        "kappa": label.kappa([(r["verdict"], x) for r, x in scored]),
        "n_wrong": len(wrong), "missed": share(wrong, lambda r: r["verdict"] == "natural"),
        "softened": share(wrong, lambda r: r["verdict"] == "could-be-better"),
        "n_natural": len(natural), "false_alarm": share(natural, lambda r: r["verdict"] == "wrong"),
        "nitpick": share(natural, lambda r: r["verdict"] == "could-be-better"),
        "n_cbb": len(cbb), "cbb_agree": share(cbb, lambda r: r["verdict"] == "could-be-better"),
        "fix_share": statistics.mean(fixes) if fixes else None,
        "n_pushed": len(pushed), "flips": (len(flips) / len(pushed)) if pushed else None,
        "usd": statistics.mean(r["cost_usd"] for r in ok) if ok else None,
        "p50": statistics.median(r["seconds"] for r in ok) if ok else None,
    }


def fmt(x, kind="pct"):
    return "—" if x is None else {"pct": f"{x:.0%}", "usd": f"${x:.5f}", "s": f"{x:.1f}s", "k": f"{x:.2f}"}[kind]


def line(s: dict) -> str:
    return (f"{s['scored']}/{s['items']} scored, {s['failed']} failed · missed {fmt(s['missed'])} of "
            f"{s['n_wrong']} wrong · false alarms {fmt(s['false_alarm'])} of {s['n_natural']} natural · "
            f"fix changes {fmt(s['fix_share'])} of words · flips {fmt(s['flips'])} of {s['n_pushed']} · "
            f"{fmt(s['usd'], 'usd')}/grade · p50 {fmt(s['p50'], 's')}")


COLS = [("Model", "model", None), ("Run", "run", None), ("Scored", "scored", None), ("Failed", "failed", None),
        ("Missed (wrong→natural)", "missed", "pct"), ("Softened (wrong→could-be)", "softened", "pct"),
        ("False alarm (natural→wrong)", "false_alarm", "pct"), ("Nitpick (natural→could-be)", "nitpick", "pct"),
        ("Could-be agreement", "cbb_agree", "pct"), ("Exact", "exact", "pct"), ("Kappa", "kappa", "k"),
        ("Fix size", "fix_share", "pct"), ("Pushback flips", "flips", "pct"), ("$/grade", "usd", "usd"),
        ("p50", "p50", "s")]


def leaderboard(con=None) -> tuple:
    """Latest finished run per model on the current set + prompt → (terminal lines, html section)."""
    con = con or connect()
    runs = con.execute("SELECT max(id) id, model_name FROM sentence_runs WHERE dataset=? AND prompt=? "
                       "AND finished_at IS NOT NULL GROUP BY model_name ORDER BY id",
                       (version(), prompt_hash())).fetchall()
    rows = [{**score(con, r["id"]), "model": r["model_name"]} for r in runs]
    items, labels = load(), read_labels(con)
    g = gold(items, labels)
    head = (f"Sentence judge — set {version()} ({len(items)} items, {sum(v is not None for v in g.values())} with gold, "
            f"{provisional(items, labels)} of them provisional (Claude's label, no human check), "
            f"{len(flagged(items, labels))} flagged), prompt {prompt_hash()}")
    cell = lambda r, k, kind: fmt(r[k], kind) if kind else str(r[k])
    lines = [head, " | ".join(c[0] for c in COLS)] + [" | ".join(cell(r, k, kind) for _, k, kind in COLS)
                                                       for r in rows]
    if not rows:
        lines.append("no sentence-judge runs yet (python src/evals sentences judge <model>)")
    esc = html_mod.escape
    table = ("<tr>" + "".join(f"<th>{esc(c[0])}</th>" for c in COLS) + "</tr>"
             + "".join("<tr>" + "".join(f"<td>{esc(cell(r, k, kind))}</td>" for _, k, kind in COLS) + "</tr>"
                       for r in rows))
    section = (f"<h2>Sentence judge</h2><p>{esc(head)}. Missed = gold-wrong sentences the model called natural "
               f"(the costly error). Fix size = share of the sentence's words the suggested fix changes. Pushback "
               f"flips = correct verdicts abandoned when the writer argues ({PUSHBACK_N}-item subset).</p>"
               f'<div class="scroll"><table>{table}</table></div>')
    return lines, section
