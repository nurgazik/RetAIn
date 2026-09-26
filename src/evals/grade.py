"""Quality grading of finished pieces by one fixed grader model (registry "grader").
Separate from the production judges, which are part of the pipeline under test: the
grader never changes between runs, so scores stay comparable across months.
Per highlighted word: idiomatic / acceptable / wrong. Per piece: invented claims and
false notes. Its agreement with the founder's blind labels (label.py) says how far to
trust it."""
import hashlib
import html as html_mod
import json
import pathlib
import re
from datetime import datetime, timezone

import generate as G
from bakeoff import load_env

from . import dataset, results

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

GRADER_SYSTEM = """You grade an app for advanced ESL readers. The app takes a SOURCE text the
reader chose and returns an ADAPTATION that places the reader's target vocabulary words where
they fit. Highlighted words appear as [n]word[/n]. Paragraphs starting "NOTE:" and inline
"(NOTE: …)" passages are short context notes the app adds on purpose (allowed; they are not
from the source).

1. Grade EVERY highlighted word, strictly, as a careful native editor would:
   - "idiomatic": exactly how an educated native writer would use this word here — right
     sense, natural collocation, right register, grammatical.
   - "acceptable": correct and clear, but slightly forced or unusual; an editor might change it.
   - "wrong": wrong sense, unnatural collocation, wrong register or ungrammatical — a
     learner copying it would learn wrong usage.
2. List INVENTIONS in the adapted text (ignore NOTE passages): new facts, numbers,
   dates, names, events or examples absent from the source; words, opinions, motives or
   manner attributed to a named person or organisation that the source does not attribute;
   any change inside quotation marks. Rewording, transitions and evaluative colour about
   things are NOT inventions.
3. List NOTE PROBLEMS: a NOTE that is factually wrong, misleading, or presented as if the
   source said it.

Output STRICT JSON only, no prose, no code fences:
{"marks": [{"n": 1, "verdict": "idiomatic|acceptable|wrong", "reason": "<short>"}],
 "inventions": [{"sentence": "<verbatim>", "why": "<short>"}],
 "note_problems": [{"note": "<verbatim>", "why": "<short>"}]}"""

MARK_RE = re.compile(r"<mark[^>]*>(.*?)</mark>", re.S)


def plain(t: str) -> str:
    return re.sub(r"\s+", " ", html_mod.unescape(re.sub(r"<[^>]+>", "", t))).strip()


def extract_marks(body: str, words: list) -> tuple:
    """Body HTML → (grader text with [n]word[/n], [{n, word, target, definition, sentence, in_note}])."""
    marks, blocks = [], []
    # D40 inline notes → "(NOTE: …)" text; their marks are flagged as in_note
    body = re.sub(r'<span class="note[^"]*"[^>]*>(.*?)</span>',
                  lambda m: "(NOTE: " + m.group(1).replace("<mark", '<mark data-note="1"') + ")", body, flags=re.S)
    for tag, inner in re.findall(r"<(p|aside)[^>]*>(.*?)</\1>", body, re.S):
        sentences = []
        for s in G.split_sentences(inner):
            def number(m, s=s):
                shown = plain(m.group(1))
                target = next((w for w in words if shown.lower().startswith(w["word"][:6].lower())), None)
                marks.append({"n": len(marks) + 1, "word": shown,
                              "target": target and target["word"],
                              "definition": target and target["definition"],
                              "sentence": plain(s), "in_note": tag == "aside" or "data-note" in m.group(0)})
                return f"[{len(marks)}]{shown}[/{len(marks)}]"
            sentences.append(plain(MARK_RE.sub(number, s)))
        blocks.append(("NOTE: " if tag == "aside" else "") + " ".join(sentences))
    return "\n\n".join(blocks), marks


def store_grade(con, run_id: int, piece_id: str, grader: str, marks: list, g: dict, raw: str, cost: float) -> dict:
    verdicts = {v.get("n"): v for v in g.get("marks", [])}
    for m in marks:
        v = verdicts.get(m["n"], {})
        con.execute("INSERT INTO marks (run_id, piece_id, n, word, sentence, grader, verdict, reason) "
                    "VALUES (?,?,?,?,?,?,?,?) ON CONFLICT (run_id, piece_id, n) DO UPDATE SET "
                    "word=excluded.word, sentence=excluded.sentence, grader=excluded.grader, "
                    "verdict=excluded.verdict, reason=excluded.reason",
                    (run_id, piece_id, m["n"], m["word"], m["sentence"], grader,
                     v.get("verdict"), v.get("reason")))
    con.execute("INSERT OR REPLACE INTO grades VALUES (?,?,?,?,?,?,?,?)",
                (run_id, piece_id, grader, json.dumps(g.get("inventions", [])),
                 json.dumps(g.get("note_problems", [])), raw, cost, datetime.now(timezone.utc).isoformat()))
    con.commit()
    return verdicts


BATCHES = ROOT / "output" / "evals" / "grading"


def export_batch(run_ids: list) -> pathlib.Path:
    """Blind grading packets for grading outside the API (e.g. Claude Code on the founder's plan):
    runs are mixed and renamed, so the grader can't tell which model wrote what.
    The id→(run, piece) key sits in _key.json; graders must not open it."""
    words = dataset.load_words()
    texts = {p["id"]: p["text"] for p in dataset.load()}
    con = results.connect()
    batch = BATCHES / f"runs-{'-'.join(map(str, run_ids))}"
    batch.mkdir(parents=True, exist_ok=True)
    key = {}
    for run_id in run_ids:
        for r in con.execute("SELECT piece_id, body FROM results WHERE run_id=? AND ok=1", (run_id,)):
            text, marks = extract_marks(r["body"], words)
            blind = hashlib.sha1(f"{run_id}:{r['piece_id']}".encode()).hexdigest()[:8]
            key[blind] = [run_id, r["piece_id"]]
            (batch / f"{blind}.json").write_text(json.dumps({
                "id": blind, "source": texts[r["piece_id"]], "adaptation": text,
                "highlighted": [{k: m[k] for k in ("n", "word", "target", "definition")} for m in marks]},
                indent=1, ensure_ascii=False))
    (batch / "_key.json").write_text(json.dumps(key, indent=1))
    (batch / "_rubric.md").write_text(GRADER_SYSTEM + "\n\nWrite your answer for packet X to X.verdict.json.\n")
    print(f"[grade] {len(key)} blind packets in {batch}")
    return batch


def import_batch(batch: str, grader: str) -> None:
    """Load <id>.verdict.json files (same JSON as the API grader returns) into the results db."""
    batch = pathlib.Path(batch)
    key = json.loads((batch / "_key.json").read_text())
    words = dataset.load_words()
    con = results.connect()
    done = 0
    for blind, (run_id, piece_id) in key.items():
        f = batch / f"{blind}.verdict.json"
        if not f.exists():
            print(f"[grade] missing verdict for {blind}")
            continue
        raw = f.read_text()
        body = con.execute("SELECT body FROM results WHERE run_id=? AND piece_id=?", (run_id, piece_id)).fetchone()[0]
        _, marks = extract_marks(body, words)
        store_grade(con, run_id, piece_id, grader, marks, json.loads(raw), raw, 0.0)
        done += 1
    print(f"[grade] imported {done}/{len(key)} verdicts as {grader}")


def grade_run(run_id: int, redo: bool = False) -> None:
    reg = results.registry()
    gspec = results.spec(reg["grader"])
    grader = results.primary_for(gspec)
    env = load_env()
    words = dataset.load_words()
    texts = {p["id"]: p["text"] for p in dataset.load()}
    con = results.connect()
    rows = con.execute("SELECT * FROM results WHERE run_id=? AND ok=1", (run_id,)).fetchall()
    total = 0.0
    for i, r in enumerate(rows, 1):
        if not redo and con.execute("SELECT 1 FROM grades WHERE run_id=? AND piece_id=? AND grader=?",
                                    (run_id, r["piece_id"], gspec["name"])).fetchone():
            continue
        text, marks = extract_marks(r["body"], words)
        mark_list = "\n".join(f"[{m['n']}] {m['word']} — target word '{m['target']}': {m['definition']}"
                              for m in marks) or "(no highlighted words)"
        user = (f"SOURCE:\n{texts.get(r['piece_id'], '')}\n\nADAPTATION:\n{text}\n\n"
                f"HIGHLIGHTED WORDS:\n{mark_list}")
        try:
            out = grader["call"](grader["model"], GRADER_SYSTEM, user, env[grader["key"]], grader["params"])
            raw = re.sub(r"^```(json)?\s*|\s*```$", "", out["text"].strip(), flags=re.M).strip()
            g = json.loads(raw)
        except Exception as exc:
            print(f"[grade] {r['piece_id']}: grader failed ({exc}); skipped")
            continue
        cost = results.call_cost(gspec, out["tokens_in"], out["tokens_out"], out.get("cost"))
        total += cost
        verdicts = store_grade(con, run_id, r["piece_id"], gspec["name"], marks, g, raw, cost)
        wrong = sum(v.get("verdict") == "wrong" for v in verdicts.values())
        print(f"[grade] {i}/{len(rows)} {r['piece_id']}: {len(marks)} marks, {wrong} wrong, "
              f"{len(g.get('inventions', []))} inventions (${cost:.4f})")
    print(f"[grade] run {run_id} graded by {gspec['name']}: ${total:.3f}")
