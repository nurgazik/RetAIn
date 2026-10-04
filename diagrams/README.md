# Diagrams

Drawings of RetAIn's major architecture and product/UX moments. Each is a Markdown file with a
[Mermaid](https://mermaid.js.org) diagram: plain text, so it diffs in git, and GitHub draws it.
Add one file per moment, link its PRD decision, and list it here.

| Diagram | What it shows | Decision |
|---|---|---|
| [word-capture-flow.md](word-capture-flow.md) | Where a word card comes from: shared list → Wiktionary → model → unverified | D48 |
| [model-call-routing.md](model-call-routing.md) | How every model call is answered fast: host order, Flash-Lite race | D49 |
| [user-day.md](user-day.md) | How each request works out the user's "today" (timezone, 4 am start, never back) | D51 |
| [model-evals.md](model-evals.md) | How a model earns a place: golden set, answer-key sources, runs, leaderboard, founder pick; Jev for every yes/no, choice, score step | D54 |
