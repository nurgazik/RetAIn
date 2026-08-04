"""Generate a digest piece from a pantry item via the production model (D5: Haiku).

Builds the prompt (core + wrapper + candidate words), calls claude-haiku-4-5,
records the result in generated_pieces, and renders reader HTML with
tap-to-reveal word highlights.

Usage:
  python3 src/generate.py <item_id_substring> <wrapper.md> <word1,word2,...> [out.html]
"""

import html as html_mod
import json
import pathlib
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import store
from bakeoff import load_env, parse_output, call_anthropic, call_gemini

ROOT = pathlib.Path(__file__).resolve().parent.parent

# D5 (2026-07-26): Flash-Lite primary, Haiku fallback on provider failure
PRIMARY = {"model": "gemini-3.1-flash-lite", "call": call_gemini, "key": "GEMINI_API_KEY"}
FALLBACK = {"model": "claude-haiku-4-5", "call": call_anthropic, "key": "ANTHROPIC_API_KEY"}

CSS = """
  body { font-family: Georgia, 'Times New Roman', serif; background: #faf8f4;
         color: #26221c; margin: 0; padding: 2rem 1.25rem 4rem; line-height: 1.65; }
  .sheet { max-width: 640px; margin: 0 auto; }
  .kicker { font-family: -apple-system, sans-serif; font-size: .75rem;
            letter-spacing: .12em; text-transform: uppercase; color: #8a6d3b;
            margin-bottom: .5rem; }
  h1 { font-size: 1.7rem; line-height: 1.25; margin: 0 0 1.25rem; }
  p { margin: 0 0 1.1rem; font-size: 1.06rem; }
  mark { background: linear-gradient(transparent 55%, #ffe08a 55%);
         padding: 0 .1em; cursor: pointer; border-radius: 2px; }
  #pop { position: absolute; display: none; z-index: 10; max-width: 280px;
         padding: .6rem .8rem; background: #26221c; color: #faf8f4;
         border-radius: 8px; font-family: -apple-system, sans-serif;
         font-size: .85rem; line-height: 1.45; }
  #pop b { color: #ffd76e; }
  .attrib { margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #ddd5c8;
            font-family: -apple-system, sans-serif; font-size: .8rem; color: #6d675e; }
  .attrib a { color: #8a6d3b; }
"""

POP_JS = """
  const pop = document.getElementById('pop');
  document.querySelectorAll('mark, .pill[data-def]').forEach(m => {
    m.addEventListener('click', e => {
      e.stopPropagation();
      pop.innerHTML = '<b>' + m.textContent.trim() + '</b> — ' + m.dataset.def;
      pop.style.display = 'block';
      const r = m.getBoundingClientRect();
      pop.style.left = Math.min(r.left + window.scrollX, window.innerWidth - 300) + 'px';
      pop.style.top = (r.bottom + window.scrollY + 8) + 'px';
    });
  });
  document.addEventListener('click', () => { pop.style.display = 'none'; });
"""


def format_ok(parsed: dict) -> bool:
    """Cheap mechanical checks the prompt demands: marks present, HTML body, no markdown."""
    return (parsed["marks"] > 0 and "<p>" in parsed["body"]
            and "**" not in parsed["body"])


def density_low(parsed: dict) -> bool:
    """D28 floor: at least one embedded word per ~100 words of body."""
    return parsed["word_count"] > 0 and parsed["marks"] / parsed["word_count"] < 0.01


def unlisted_marks(body: str, defs: dict) -> list:
    """Marked words that aren't on the candidate list — nothing to reveal on tap."""
    stems = [re.sub(r"<[^>]+>", "", s).strip().lower()
             for s in re.findall(r"<mark>(.*?)</mark>", body, flags=re.S)]
    return [s for s in stems
            if not any(s.startswith(w[:6].lower()) for w in defs)]


def invented_numbers(item, parsed: dict) -> list:
    """Numbers in the piece that appear nowhere in the source — a cheap
    hallucination tripwire for fact-bearing wrappers. (Numbers the source
    spells out in words can false-positive; that only costs a retry.)"""
    def nums(text):
        return set(re.findall(r"\d+(?:[.,]\d+)*", re.sub(r"<[^>]+>", " ", text)))
    return sorted(nums(parsed["body"]) - nums(item["content_html"] or ""))


def normalize_bc_years(body: str) -> str:
    """The wrapper wants '30 BC'; models sometimes emit '-30' or '-30 BC'."""
    return re.sub(r"<b>-(\d+)(?:\s*BC)?</b>", r"<b>\1 BC</b>", body)


def missing_years(item, parsed: dict) -> list:
    """Coverage check for calendar sources: every <h3>year</h3> event in the
    source must surface as a bolded year block in the piece."""
    years = re.findall(r"<h3>(-?\d+)</h3>", item["content_html"] or "")
    want = [f"{y[1:]} BC" if y.startswith("-") else y for y in years]
    return [y for y in want if f"<b>{y}</b>" not in parsed["body"]]


QC_SYSTEM = """You are a native-English-speaker usage checker for an advanced ESL reading app.
You receive reader-facing text in which target vocabulary words are wrapped in <mark> tags,
plus the word list with definitions.

Judge each MARKED word's usage on two tests:
1. Idiomatic fit: is this exactly how an educated native writer would use the word in this
   sentence — natural collocation, correct meaning, correct register? Marginal, strained, or
   nonstandard usage fails (an awkward collocation teaches the learner wrong usage).
2. Placement taste: is the word embedded in a passage recounting tragedy, atrocity, or
   violence? If so it fails regardless of grammar.

Output STRICT JSON only — no prose, no code fences:
{"verdicts": [{"word": "<marked word as it appears>", "ok": true},
              {"word": "...", "ok": false, "reason": "<short reason>"}]}
Every marked word gets exactly one verdict. When genuinely unsure, fail it — the app
silently un-highlights failed words; a false demotion costs little, a bad usage costs trust."""


def qc_gate(body: str, defs: dict, env: dict) -> list:
    """D19 gate: per-word native-writer check (~$0.0005/piece). Returns marked
    words to demote. Fails open — a judge error demotes nothing."""
    word_list = "\n".join(f"- {w}: {d}" for w, d in defs.items())
    try:
        raw, _ = call_model(QC_SYSTEM, f"WORD LIST:\n{word_list}\n\nTEXT:\n{body}", env)
        raw = re.sub(r"^```(json)?\s*|\s*```$", "", raw.strip(), flags=re.M).strip()
        bad = [v for v in json.loads(raw)["verdicts"] if not v.get("ok")]
        for v in bad:
            print(f"[qc] demote '{v['word']}': {v.get('reason', 'no reason given')}")
        return [v["word"] for v in bad]
    except Exception as exc:
        print(f"[warn] QC gate failed open ({exc}); no demotions")
        return []


def demote_marks(body: str, words: list) -> str:
    """Unwrap <mark> tags for demoted words — text stays, highlight goes
    (demote-don't-delete)."""
    lowers = {w.strip().lower() for w in words}
    def repl(m):
        inner = re.sub(r"<[^>]+>", "", m.group(1)).strip().lower()
        return m.group(1) if inner in lowers else m.group(0)
    return re.sub(r"<mark>(.*?)</mark>", repl, body, flags=re.S)


def call_model(system: str, user: str, env: dict) -> tuple:
    """Primary model with automatic fallback (D5). Returns (text, model_name)."""
    try:
        r = PRIMARY["call"](PRIMARY["model"], system, user, env[PRIMARY["key"]])
        return r["text"], PRIMARY["model"]
    except Exception as exc:
        print(f"[warn] {PRIMARY['model']} failed ({exc}); falling back to {FALLBACK['model']}")
        r = FALLBACK["call"](FALLBACK["model"], system, user, env[FALLBACK["key"]])
        return r["text"], FALLBACK["model"]


def annotate_marks(body: str, defs: dict) -> str:
    """Attach data-def tooltips to <mark>word</mark> tags."""
    def repl(m):
        word = m.group(1)
        stem = re.sub(r"<[^>]+>", "", word).lower()
        definition = next((d for w, d in defs.items() if stem.startswith(w[:6].lower())), "")
        if not definition:  # unlisted mark survived the retry: unwrap, never show an empty popup
            return word
        return f'<mark data-def="{html_mod.escape(definition)}">{word}</mark>'
    return re.sub(r"<mark>(.*?)</mark>", repl, body, flags=re.S)


def render(kicker: str, title: str, body: str, attrib: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RetAIn · {html_mod.escape(title)}</title><style>{CSS}</style></head>
<body><div class="sheet">
  <div class="kicker">{html_mod.escape(kicker)}</div>
  <h1>{html_mod.escape(title)}</h1>
  {body}
  <div class="attrib">{attrib}</div>
</div><div id="pop"></div><script>{POP_JS}</script></body></html>"""


def attribution_for(item) -> str:
    url = html_mod.escape(item["url"])
    if item["source"] == "wikipedia_onthisday":
        return (f'Adapted from <a href="{url}">Wikipedia\'s On This Day</a> '
                f"(CC BY-SA 4.0); this adaptation is likewise shared under CC BY-SA.")
    if item["source"] == "stack_exchange":
        return (f'Adapted from "<a href="{url}">{html_mod.escape(item["title"])}</a>" '
                f'on {html_mod.escape(item["section"])}.stackexchange.com — '
                f'{html_mod.escape(item["author"])} (CC BY-SA 4.0); this adaptation '
                f"is likewise shared under CC BY-SA.")
    if item["source"] == "chronicling_america":
        return (f'Source: {html_mod.escape(item["author"])}, {item["published"]} — '
                f'public domain, via <a href="{url}">Chronicling America</a> '
                f"(Library of Congress).")
    return (f'Adapted from "<a href="{url}">{html_mod.escape(item["title"])}</a>" '
            f'by {html_mod.escape(item["author"] or "unknown")} ({item["license"]}).')


def generate_piece(con, item, wrapper_file: str, chosen: list, env: dict,
                   digest_date: str = None) -> dict:
    """Full pipeline for one piece: prompt build, validation retry, QC with
    regeneration (D29), annotation. Records the piece; returns it."""
    words = json.loads((ROOT / "data" / "words.json").read_text())["words"]
    defs = {w["word"]: w["definition"] for w in words if w["word"] in chosen}

    system = ((ROOT / "prompts" / "core.md").read_text() + "\n\n---\n\n"
              + (ROOT / "prompts" / wrapper_file).read_text())
    source_text = re.sub(r"<[^>]+>", " ", item["content_html"])
    source_text = html_mod.unescape(re.sub(r"[ \t]+", " ", source_text)).strip()

    def build_user(menu: dict, avoid: list = ()) -> str:
        # D28: density instruction lives HERE, not in the wrapper — A/B showed
        # the user message is what the model actually obeys (3-trial study 08-01)
        word_list = "\n".join(f"- {w}: {d}" for w, d in menu.items())
        ban = (f"FORBIDDEN WORDS — do not use these anywhere in the piece, in any "
               f"form, marked or unmarked: {', '.join(avoid)}.\n\n") if avoid else ""
        return (f"{ban}CANDIDATE TARGET WORDS — embed one in EVERY event block or "
                f"paragraph where one sits naturally (two per block is fine when "
                f"both are genuinely idiomatic; never force an awkward fit). "
                f"EXCEPTION: any passage recounting tragedy, atrocity, or violence "
                f"must contain NO candidate words at all:\n{word_list}\n\n"
                f"SOURCE (title: {item['title']}):\n\n{source_text}")

    user = build_user(defs)

    def attempt_score(parsed):
        """Rank attempts: format first, then coverage, clean marks, facts, density, marks."""
        return (format_ok(parsed), not missing_years(item, parsed),
                not unlisted_marks(parsed["body"], defs),
                not invented_numbers(item, parsed),
                not density_low(parsed), parsed["marks"])

    def parse(raw: str) -> dict:
        p = parse_output(raw)
        p["body"] = normalize_bc_years(p["body"])
        return p

    print(f"[gen] {item['id']} via {PRIMARY['model']}...")
    raw, model_used = call_model(system, user, env)
    parsed = parse(raw)
    if not all(attempt_score(parsed)[:5]):
        # one validation retry, mirroring pipeline QC; keep the better attempt
        print(f"[gen] validation failed on attempt 1 (marks={parsed['marks']}, "
              f"missing years={missing_years(item, parsed) or 'none'}, "
              f"unlisted={unlisted_marks(parsed['body'], defs) or 'none'}, "
              f"invented numbers={invented_numbers(item, parsed) or 'none'}, "
              f"density_low={density_low(parsed)}), retrying once...")
        raw2, model2 = call_model(system, user, env)
        parsed2 = parse(raw2)
        if attempt_score(parsed2) > attempt_score(parsed):
            parsed, model_used = parsed2, model2
    missing = missing_years(item, parsed)
    unlisted = unlisted_marks(parsed["body"], defs)
    if missing:
        print(f"[warn] piece still missing source events after retry: {missing}")
    if unlisted:
        print(f"[warn] unlisted marks after retry (will unwrap): {unlisted}")
    invented = invented_numbers(item, parsed)
    if invented:
        print(f"[warn] numbers not found in source after retry (verify by hand): "
              f"{invented}")
    if density_low(parsed):
        print(f"[warn] density below floor after retry: {parsed['marks']} marks "
              f"in {parsed['word_count']} words")

    # D19 gate + D29 UX: a QC-rejected word must not appear in the text at all —
    # the reader knows their words, so unhighlighted misuse still teaches wrong
    # usage AND confuses. Regenerate without the failed words; un-highlighting
    # is only the last-resort floor.
    demoted = qc_gate(parsed["body"], defs, env)
    if demoted:
        print(f"[qc] regenerating without {demoted}...")
        keep = {w: d for w, d in defs.items()
                if not any(s.strip().lower().startswith(w[:6].lower())
                           for s in demoted)}
        raw2, model2 = call_model(system, build_user(keep, avoid=demoted), env)
        parsed2 = parse(raw2)
        stems = [s.strip().lower()[:6] for s in demoted]
        reappeared = any(st in parsed2["body"].lower() for st in stems)
        if (format_ok(parsed2) and not missing_years(item, parsed2)
                and not invented_numbers(item, parsed2) and not reappeared):
            parsed, model_used, defs = parsed2, model2, keep
            residual = qc_gate(parsed["body"], defs, env)
            if residual:
                print(f"[warn] QC failures persist ({residual}); "
                      f"un-highlighting as last resort")
                parsed["body"] = demote_marks(parsed["body"], residual)
        else:
            why = ([] if format_ok(parsed2) else ["format"]) \
                + ([f"missing years {missing_years(item, parsed2)}"]
                   if missing_years(item, parsed2) else []) \
                + ([f"invented numbers {invented_numbers(item, parsed2)}"]
                   if invented_numbers(item, parsed2) else []) \
                + (["demoted word reappeared"] if reappeared else [])
            print(f"[warn] regeneration failed validation ({'; '.join(why)}); "
                  f"keeping original, un-highlighting {demoted} as last resort")
            parsed["body"] = demote_marks(parsed["body"], demoted)
        parsed["marks"] = len(re.findall(r"<mark>", parsed["body"]))

    # D31: calendar event blocks render only if a highlight survived QC — the
    # model still covers every event (no incentive to force words); the filter
    # is purely at render time
    if item["source"] == "wikipedia_onthisday":
        blocks = re.findall(r"<p><b>[^<]+</b><br>.*?</p>", parsed["body"], flags=re.S)
        kept = [b for b in blocks if "<mark>" in b]
        if blocks and kept:
            dropped = len(blocks) - len(kept)
            if dropped:
                print(f"[render] dropped {dropped} wordless event block(s) (D31)")
            parsed["body"] = "\n".join(kept)
            parsed["marks"] = len(re.findall(r"<mark>", parsed["body"]))

    title = re.sub(r"[*#]+", "", parsed["title"]).strip()
    body = annotate_marks(parsed["body"], defs)

    # record the words actually marked in the final body (post-QC), not the
    # model's self-declaration — the scheduler's serving stats depend on this
    marked = [re.sub(r"<[^>]+>", "", m).strip().lower()
              for m in re.findall(r"<mark>(.*?)</mark>", parsed["body"], flags=re.S)]
    used = sorted({w for w in defs
                   if any(m.startswith(w[:6].lower()) for m in marked)})

    con.execute(
        "INSERT INTO generated_pieces (item_id, created_at, model, words_used, "
        "title, body_html, digest_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (item["id"], datetime.now(timezone.utc).isoformat(), model_used,
         json.dumps(used), title, body, digest_date))
    store.set_status(con, item["id"], "selected",
                     f"generated {datetime.now(timezone.utc).date()}")
    print(f"[ok] {parsed['marks']} words embedded, {parsed['word_count']} words long")
    return {"item": item, "title": title, "body": body, "model": model_used,
            "marks": parsed["marks"], "words_used": used}


def run() -> None:
    item_like, wrapper_file, words_csv = sys.argv[1], sys.argv[2], sys.argv[3]
    out_path = ROOT / "output" / (sys.argv[4] if len(sys.argv) > 4
                                  else f"{item_like}.html")
    con = store.connect()
    item = con.execute("SELECT * FROM items WHERE id LIKE ?",
                       (f"%{item_like}%",)).fetchone()
    if not item:
        print(f"[error] no pantry item matching '{item_like}'")
        return
    piece = generate_piece(con, item, wrapper_file,
                           [w.strip() for w in words_csv.split(",")], load_env())
    kicker = f"Daily Digest · {datetime.now().strftime('%B %d')}"  # reader-local date
    out_path.write_text(render(kicker, piece["title"], piece["body"],
                               attribution_for(item)))
    print(f"[ok] wrote {out_path}")


if __name__ == "__main__":
    run()
