"""Model bake-off: same article, same prompt, same candidate words across providers.

Produces output/bakeoff/bakeoff.html with the rewrites blind-labeled A-D (judge
quality first!) and output/bakeoff/results.json with the letter->model mapping,
latency, tokens, and cost (open only after ranking).

Reads API keys from .env.local. Stdlib only; raw HTTP to all three providers so
latency measurement is symmetric.

Usage: python3 src/bakeoff.py
"""

import html as html_mod
import json
import os
import pathlib
import random
import re
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import store

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "output" / "bakeoff"

ARTICLE_TITLE_LIKE = "%gap in the archives%"

CANDIDATE_WORDS = [
    "squander", "eschew", "ubiquitous", "gravitas", "zeitgeist",
    "deft", "perfunctory", "windfall", "conundrum", "candor",
]

# $/1M tokens (input, output). Anthropic per skill docs 2026-06; OpenAI/Gemini
# per public pricing pages checked 2026-07-24 — treat as approximate.
MODELS = [
    {"provider": "anthropic", "model": "claude-haiku-4-5", "in": 1.00, "out": 5.00},
    {"provider": "anthropic", "model": "claude-sonnet-4-6", "in": 3.00, "out": 15.00},
    {"provider": "openai", "model": "gpt-5-mini", "in": 0.25, "out": 2.00},
    {"provider": "gemini", "model": "gemini-3.6-flash", "in": 1.50, "out": 7.50},
    {"provider": "openai_compat", "model": "kimi-k2.5", "in": 0.60, "out": 3.00,
     "base_url": "https://api.moonshot.ai/v1", "key_env": "KIMI_API_KEY"},
    {"provider": "openai", "model": "o3-mini", "in": 1.10, "out": 4.40},
    {"provider": "gemini", "model": "gemini-3.1-flash-lite", "in": 0.25, "out": 1.50},
]

# per-model request tweaks (reasoning models need effort setting + token headroom)
OPENAI_OVERRIDES = {
    "o3-mini": {"reasoning_effort": os.environ.get("O3_EFFORT", "low"),
                "max_completion_tokens": 24000},
}

MAX_OUTPUT_TOKENS = 4000
TIMEOUT = 240


def load_env() -> dict:
    env = {}
    for line in (ROOT / ".env.local").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def build_prompt() -> tuple:
    core = (ROOT / "prompts" / "core.md").read_text()
    news = (ROOT / "prompts" / "news.md").read_text()
    words = json.loads((ROOT / "data" / "words.json").read_text())["words"]
    defs = {w["word"]: w["definition"] for w in words}
    word_list = "\n".join(f"- {w}: {defs[w]}" for w in CANDIDATE_WORDS)

    con = store.connect()
    row = con.execute(
        "SELECT title, author, url, content_html FROM items WHERE title LIKE ?",
        (ARTICLE_TITLE_LIKE,),
    ).fetchone()
    text = re.sub(r"<[^>]+>", " ", row["content_html"])
    text = html_mod.unescape(re.sub(r"\s+", " ", text)).strip()

    system = f"{core}\n\n---\n\n{news}"
    user = (
        f"CANDIDATE TARGET WORDS (use 3-6, only where genuinely idiomatic):\n"
        f"{word_list}\n\n"
        f"SOURCE ARTICLE (title: {row['title']}):\n\n{text}"
    )
    return system, user, dict(row)


def post_json(url: str, headers: dict, body: dict) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", **headers}
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read())


def call_anthropic(model: str, system: str, user: str, key: str) -> dict:
    body = {
        "model": model,
        "max_tokens": MAX_OUTPUT_TOKENS,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    d = post_json(
        "https://api.anthropic.com/v1/messages",
        {"x-api-key": key, "anthropic-version": "2023-06-01"},
        body,
    )
    text = "".join(b["text"] for b in d["content"] if b["type"] == "text")
    u = d["usage"]
    return {"text": text, "tokens_in": u["input_tokens"], "tokens_out": u["output_tokens"]}


def call_openai(model: str, system: str, user: str, key: str) -> dict:
    body = {
        "model": model,
        "max_completion_tokens": MAX_OUTPUT_TOKENS,
        "reasoning_effort": "minimal",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        **OPENAI_OVERRIDES.get(model, {}),
    }
    try:
        d = post_json(
            "https://api.openai.com/v1/chat/completions",
            {"Authorization": f"Bearer {key}"}, body,
        )
    except urllib.error.HTTPError:
        body.pop("reasoning_effort", None)
        d = post_json(
            "https://api.openai.com/v1/chat/completions",
            {"Authorization": f"Bearer {key}"}, body,
        )
    u = d["usage"]
    return {
        "text": d["choices"][0]["message"]["content"],
        "tokens_in": u["prompt_tokens"],
        "tokens_out": u["completion_tokens"],
    }


def call_gemini(model: str, system: str, user: str, key: str) -> dict:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {
            "maxOutputTokens": MAX_OUTPUT_TOKENS,
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }
    try:
        d = post_json(url, {}, body)
    except urllib.error.HTTPError:
        del body["generationConfig"]["thinkingConfig"]
        d = post_json(url, {}, body)
    parts = d["candidates"][0]["content"]["parts"]
    u = d.get("usageMetadata", {})
    return {
        "text": "".join(p.get("text", "") for p in parts),
        "tokens_in": u.get("promptTokenCount", 0),
        "tokens_out": u.get("candidatesTokenCount", 0) + u.get("thoughtsTokenCount", 0),
    }


def make_openai_compat(base_url: str):
    def call(model: str, system: str, user: str, key: str) -> dict:
        d = post_json(
            f"{base_url}/chat/completions",
            {"Authorization": f"Bearer {key}"},
            {"model": model, "max_tokens": MAX_OUTPUT_TOKENS,
             "messages": [{"role": "system", "content": system},
                          {"role": "user", "content": user}]},
        )
        u = d["usage"]
        return {"text": d["choices"][0]["message"]["content"],
                "tokens_in": u["prompt_tokens"], "tokens_out": u["completion_tokens"]}
    return call


CALLERS = {"anthropic": call_anthropic, "openai": call_openai, "gemini": call_gemini}
KEY_NAMES = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY", "gemini": "GEMINI_API_KEY"}


def parse_output(text: str) -> dict:
    title_m = re.search(r"TITLE:\s*(.+)", text)
    words_m = re.search(r"WORDS_USED:\s*(.+)", text, re.S)
    # Robust body extraction: models vary in section ordering, so take the
    # actual <p> paragraphs wherever they appear rather than slicing between
    # BODY:/WORDS_USED: labels. Fall back to the label slice for non-<p> output.
    paragraphs = re.findall(r"<p>.*?</p>", text, re.S)
    if paragraphs:
        body = "\n".join(paragraphs)
    else:
        body_m = re.search(r"BODY:\s*(.*?)(?:WORDS_USED:|$)", text, re.S)
        body = (body_m.group(1).strip() if body_m else text).strip()
        body = re.sub(r"^```(?:html)?\s*|\s*```$", "", body).strip()
    return {
        "title": (title_m.group(1).strip() if title_m else "(no title parsed)"),
        "body": body,
        "words_used": (words_m.group(1).strip() if words_m else ""),
        "marks": len(re.findall(r"<mark>", body)),
        "word_count": len(re.sub(r"<[^>]+>", " ", body).split()),
    }


def render_html(pieces: list, source: dict) -> str:
    sections = []
    for p in pieces:
        sections.append(f"""
  <section>
    <div class="label">Version {p['letter']}</div>
    <h2>{html_mod.escape(p['title'])}</h2>
    {p['body']}
    <div class="meta">words embedded: {p['marks']} · length: {p['word_count']} words</div>
  </section>""")
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RetAIn · Model bake-off (blind)</title>
<style>
  body {{ font-family: Georgia, serif; background: #faf8f4; color: #26221c;
         margin: 0; padding: 2rem 1.25rem 4rem; line-height: 1.65; }}
  .sheet {{ max-width: 640px; margin: 0 auto; }}
  h1 {{ font-size: 1.4rem; font-family: -apple-system, sans-serif; }}
  h2 {{ font-size: 1.35rem; line-height: 1.3; }}
  section {{ border-top: 3px solid #8a6d3b; margin-top: 2.5rem; padding-top: .5rem; }}
  .label {{ font-family: -apple-system, sans-serif; font-size: .8rem; font-weight: 700;
            letter-spacing: .1em; text-transform: uppercase; color: #8a6d3b; }}
  p {{ margin: 0 0 1.1rem; font-size: 1.05rem; }}
  mark {{ background: linear-gradient(transparent 55%, #ffe08a 55%); padding: 0 .1em; }}
  .meta {{ font-family: -apple-system, sans-serif; font-size: .78rem; color: #6d675e;
           margin-top: 1rem; }}
  .intro {{ font-family: -apple-system, sans-serif; font-size: .9rem; color: #4c463d;
            background: #f1ead9; padding: .8rem 1rem; border-radius: 8px; }}
</style></head><body><div class="sheet">
<h1>Model bake-off — blind quality review</h1>
<p class="intro">Four rewrites of the same Global Voices article
("{html_mod.escape(source['title'])}"), same prompt, same 10 candidate words.
Read all four and rank them before opening results.json — the letters are
randomized. Judge: Would I read this? Does every highlighted word sound natural?
Are the facts intact vs <a href="{html_mod.escape(source['url'])}">the original</a>?</p>
{''.join(sections)}
</div></body></html>"""


def run() -> None:
    env = load_env()
    system, user, source = build_prompt()
    # optional CLI filter: `python3 src/bakeoff.py kimi` runs only matching models
    name_filter = sys.argv[1] if len(sys.argv) > 1 else ""
    models = [m for m in MODELS if name_filter in m["model"]]
    suffix = f"-{name_filter}" if name_filter else ""
    results = []
    for spec in models:
        # up to 2 attempts: a validation-failure retry mirrors the production
        # QC step, and attempt count is itself a reliability metric
        entry = {**spec, "ok": False, "attempts": 0}
        for attempt in (1, 2):
            entry["attempts"] = attempt
            t0 = time.monotonic()
            try:
                if spec["provider"] == "openai_compat":
                    caller, key = make_openai_compat(spec["base_url"]), env[spec["key_env"]]
                else:
                    caller, key = CALLERS[spec["provider"]], env[KEY_NAMES[spec["provider"]]]
                r = caller(spec["model"], system, user, key)
                elapsed = time.monotonic() - t0
                parsed = parse_output(r["text"])
                cost = r["tokens_in"] / 1e6 * spec["in"] + r["tokens_out"] / 1e6 * spec["out"]
                entry.update({**parsed, "seconds": round(elapsed, 1),
                              "tokens_in": r["tokens_in"], "tokens_out": r["tokens_out"],
                              "cost_usd": round(cost, 5), "ok": parsed["marks"] > 0})
                if entry["ok"]:
                    print(f"{spec['model']}: ok (attempt {attempt}), {elapsed:.1f}s, "
                          f"{parsed['marks']} words embedded")
                    break
                print(f"{spec['model']}: format fail on attempt {attempt} (no <mark> tags)")
            except Exception as exc:
                print(f"{spec['model']}: FAILED attempt {attempt} — {exc}")
                entry["error"] = str(exc)
        results.append(entry)

    good = [r for r in results if r.get("ok")]
    letters = list("ABCD")[: len(good)]
    random.shuffle(good)
    for letter, r in zip(letters, good):
        r["letter"] = letter
    good.sort(key=lambda r: r["letter"])

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"bakeoff{suffix}.html").write_text(render_html(good, source))
    (OUT_DIR / f"results{suffix}.json").write_text(json.dumps(
        {"source_article": source["title"],
         "results": [{k: v for k, v in r.items() if k != "body"} for r in results]},
        indent=2))
    print(f"\nwrote {OUT_DIR}/bakeoff.html ({len(good)} versions, blind)")
    print(f"wrote {OUT_DIR}/results.json (mapping + metrics — open AFTER ranking)")


if __name__ == "__main__":
    run()
