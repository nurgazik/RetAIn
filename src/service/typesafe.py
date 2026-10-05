"""TypeSafe's Jev (D54): typed answers with probabilities, never text. POST /v1/systemone,
charged per input token, output free (docs.typesafe.ai/api, /models — read 2026-10-04).
Shared by the service and the evals, so an eval tests the call that ships."""
import hashlib
import json
import os
import time
import urllib.error
import urllib.request

URL = "https://api.typesafe.ai/v1/systemone"
MODEL = os.environ.get("RETAIN_JEV_MODEL", "jev-1.13.0")  # pinned: thresholds are tuned per version
PRICE_IN = 0.042  # $ per million input tokens; output free


def ask(state, questions: dict, key: str = None, model: str = None, tries: int = 3) -> dict:
    """state + {id: question} → {"answers", "model", "tokens_in", "ms"}. Retries 429 / 529."""
    key = key or os.environ.get("TYPESAFE_API_KEY", "")
    body = json.dumps({"model": model or MODEL, "state": state, "questions": questions}).encode()
    t0 = time.time()
    for attempt in range(tries):
        req = urllib.request.Request(URL, data=body, headers={
            "Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": "retain"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                d = json.loads(r.read())
            break
        except urllib.error.HTTPError as exc:
            if attempt == tries - 1 or exc.code not in (429, 529) and exc.code < 500:
                raise
            time.sleep(1.5 * 2 ** attempt)
    return {"answers": d["answers"], "model": d.get("model"), "tokens_in": d["usage"]["input_tokens"],
            "ms": int((time.time() - t0) * 1000)}


def cost(tokens_in: int) -> float:
    return tokens_in / 1e6 * PRICE_IN


# The sentence judge's verdict question (flow-write-a-sentence; eval-sentence-judge tests exactly this).
VERDICT_CRITERIA = {
    "natural": ("A careful native writer could have written this as is: the word has the right sense, a "
                "natural pairing with the words around it, a fitting tone and slant, and correct grammar."),
    "could-be-better": ("The word's meaning is right, but the phrasing is stiff, the tone is off for the "
                        "context, or a native writer would usually put it differently."),
    "wrong": ("The word is misused: wrong meaning, an unnatural pairing, the wrong positive/negative slant, "
              "or wrong form or grammar. Someone copying this sentence would learn wrong usage."),
}
VERDICT_Q = "How well is `word` (meaning: `definition`) used in `sentence`?"


def verdict_question() -> dict:
    return {"type": "choice", "instructions": VERDICT_Q, "criteria": VERDICT_CRITERIA}


def p_natural(word: str, definition: str, sentence: str) -> tuple:
    """Jev's probability that the sentence uses the word naturally → (p, call row for `calls`)."""
    q = verdict_question()
    out = ask({"word": word, "definition": definition, "sentence": sentence}, {"verdict": q})
    probs = out["answers"]["verdict"]["probabilities"]
    sha = hashlib.sha1(json.dumps(q, sort_keys=True).encode()).hexdigest()[:12]  # which question wording
    row = ("judge-jev", out["model"] or MODEL, out["tokens_in"], 0, out["ms"], cost(out["tokens_in"]),
           None, json.dumps(probs), sha)
    return probs["natural"], row
