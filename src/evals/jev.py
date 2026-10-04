"""TypeSafe's Jev as an eval candidate (D54, TD-21). Jev returns typed answers (Noul = P(yes),
Choice, Score) with probabilities, never text: POST /v1/systemone, charged per input token,
output free (docs.typesafe.ai/api, /models — read 2026-10-04). Plain HTTP, no SDK."""
import json
import urllib.request

from bakeoff import load_env

from . import results

URL = "https://api.typesafe.ai/v1/systemone"


def ask(state, questions: dict, spec: dict, key: str = None) -> dict:
    """One request: state + {id: question} → {"answers": {...}, "cost": usd, "model": versioned id}.
    Every question sees the same state and is answered independently, so batch them."""
    key = key or load_env()[spec.get("key_env", "TYPESAFE_API_KEY")]
    body = {"model": spec["model"], "state": state, "questions": questions}

    def post(_):
        req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={
            "Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": "retain-evals"})
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    d = results.with_retry(post)(None)  # 429 / 529 overloaded → backoff, as the docs ask
    return {"answers": d["answers"], "model": d.get("model"),
            "cost": results.call_cost(spec, d["usage"]["input_tokens"], d["usage"].get("output_tokens", 0), None)}


WORD_QUESTION = {
    "type": "noul",
    "instructions": ("Is `{w}` used the way a careful, educated native English writer would use it in "
                     "`{s}`, given its meaning in `{d}`?"),
    "criteria": {
        "true": ("Yes: the right sense of the word, a natural collocation (the words it is paired with), "
                 "a register that fits the sentence, and correct grammar for the word."),
        "false": ("No: any of these is off — wrong sense, an unnatural pairing, a register clash, a "
                  "connotation that doesn't fit, or wrong grammar for the word. A reader copying the "
                  "sentence would learn wrong usage."),
    },
}


def word_questions(marks: list) -> tuple:
    """Highlighted words → (state, questions): one Noul per word, all over one state (one call per piece)."""
    state = {"items": [{"word": m["word"], "definition": m["definition"], "sentence": m["sentence"]} for m in marks]}
    qs = {}
    for i in range(len(marks)):
        q = dict(WORD_QUESTION)
        q["instructions"] = WORD_QUESTION["instructions"].format(
            w=f"items[{i}].word", s=f"items[{i}].sentence", d=f"items[{i}].definition")
        qs[f"w{i}"] = q
    return state, qs


# --- sentence judge (D53): one call per sentence, every variant asked at once ------------------

VERDICT_CRITERIA = {
    "natural": ("A careful native writer could have written this as is: the word has the right sense, a "
                "natural pairing with the words around it, a fitting tone and slant, and correct grammar."),
    "could-be-better": ("The word's meaning is right, but the phrasing is stiff, the tone is off for the "
                        "context, or a native writer would usually put it differently."),
    "wrong": ("The word is misused: wrong meaning, an unnatural pairing, the wrong positive/negative slant, "
              "or wrong form or grammar. Someone copying this sentence would learn wrong usage."),
}
VERDICT_Q = "How well is `word` (meaning: `definition`) used in `sentence`?"
DIMENSIONS = {  # one property each, combined in code (the docs' "atomic questions")
    "meaning": "Is `word` used in `sentence` with a meaning that matches `definition`?",
    "collocation": ("Are the words paired with `word` in `sentence` (its verbs, nouns, prepositions) ones a "
                    "native writer would naturally combine with it?"),
    "register": "Does `word` fit the tone of `sentence`, formal or casual?",
    "connotation": "Does the positive or negative slant of `word` fit what `sentence` describes?",
    "grammar": ("Is `word` used with correct grammar in `sentence`: the right word form, articles, "
                "prepositions and objects?"),
}
# fixed before the first run (2026-10-04), not tuned on results: weakest dimension decides
NATURAL_AT, WRONG_BELOW = 0.8, 0.5


def sentence_questions() -> dict:
    fwd = {"type": "choice", "instructions": VERDICT_Q, "criteria": VERDICT_CRITERIA}
    rev = {"type": "choice", "instructions": VERDICT_Q, "criteria": dict(reversed(list(VERDICT_CRITERIA.items())))}
    qs = {"choice": fwd, "choice_reversed": rev}
    qs.update({f"dim_{k}": {"type": "noul", "instructions": v} for k, v in DIMENSIONS.items()})
    return qs


def questions_hash() -> str:
    import hashlib
    return "jev:" + hashlib.sha1(json.dumps([sentence_questions(), NATURAL_AT, WRONG_BELOW],
                                            sort_keys=True).encode()).hexdigest()[:8]


def dims_verdict(answers: dict) -> tuple:
    weakest = min(answers[f"dim_{k}"]["noul"] for k in DIMENSIONS)
    v = "natural" if weakest >= NATURAL_AT else "wrong" if weakest < WRONG_BELOW else "could-be-better"
    return v, weakest
