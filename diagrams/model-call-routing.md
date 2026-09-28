# Model call routing: how every model call gets answered fast

Decision: PRD D49 (2026-09-28). Code: `src/generate.py` (`PRIMARY`, `FALLBACK`, `HEDGE_AFTER`,
`call_model`). Watch it: `python -m service.speed [days]` (run from `src/`).

```mermaid
flowchart TD
    A([Model call<br/>rewrite · check · word card]) --> B["Gemma 4 26B via OpenRouter<br/>zero-retention hosts only<br/>try in order: Makora → Venice → DeepInfra<br/>then any other zero-retention host"]
    B --> C{Answered within<br/>10 s rewrite / 5 s other?}
    C -- yes --> OK([Use Gemma's answer])
    C -- "error" --> F["Gemini Flash-Lite<br/>direct from Google, thinking off"]
    C -- "still running" --> R["Start Flash-Lite too<br/>(race)"]
    R --> W{First to answer}
    W -- Gemma --> OK
    W -- Flash-Lite --> OK2([Use Flash-Lite's answer<br/>the Gemma call still bills])
    F --> OK2
    OK --> L[("calls table: model, host, ms, cost")]
    OK2 --> L
```

## Why

- OpenRouter's default host pick is weighted towards the cheapest host, not the fastest. The
  same rewrite took 10–118 s across hosts (probe, 2026-09-28), and fast hosts sometimes refuse
  with "too many requests".
- Sorting by throughput made things slower (runs 41/42), so the order is set from our own
  measurements instead.
- A fixed host order still depends on those hosts having capacity; the race with Flash-Lite
  caps the wait when they don't.
- Not permanent (founder): the model market moves weekly. Re-check with the speed report and
  `src/evals`, and change the order or the models when the numbers say so.
