# Diagrams

Drawings of RetAIn's main user flows, the evals that test them, and the machinery underneath.
Each is a Markdown file with a [Mermaid](https://mermaid.js.org) diagram: plain text, so it diffs
in git, and GitHub draws it (in VS Code: the "Markdown Preview Mermaid Support" extension, then
Cmd+Shift+V). One file per flow, one per eval; link its PRD decision and list it here.

**Naming:** `flow-` = something the user does · `eval-` = a test we run while building ·
`infra-` = machinery under every flow.

## User flows — where models run for the user

In every flow, blue boxes are a model writing text, orange boxes a model answering yes/no or
choosing (a live quality gate), dashed grey boxes plain code.

| Diagram | What the user does | Models in it | Decision | Status |
|---|---|---|---|---|
| [flow-share-an-article.md](flow-share-an-article.md) | Shares or pastes something they're reading, reads it back with their words | writer · word checker · fact checker | D40, D41 | live |
| [flow-save-a-word.md](flow-save-a-word.md) | Saves a word (share sheet, Siri, word list) and gets its card | example writer · "real word?" check | D48, D50 | live |
| [flow-fill-in-the-word.md](flow-fill-in-the-word.md) | Fills the blank in a sentence | sentence writer (daily prep only); the answer is checked by code | D53 | designed |
| [flow-write-a-sentence.md](flow-write-a-sentence.md) | Writes a sentence with a word, gets a verdict | judge · feedback writer | D53 | designed |

## Evals — tests we run while building, never on a user's request

Each eval tests one model step from a flow above against a frozen set of known answers, to pick
the model for that step (and re-check it when instructions or models change). Every yes/no,
choice or score step also gets a Jev run (D54).

| Diagram | Tests which step | Status |
|---|---|---|
| [eval-article-rewrite.md](eval-article-rewrite.md) | share-an-article → writer | built |
| [eval-word-checker.md](eval-word-checker.md) | share-an-article → word checker | built; Jev next (TD-21) |
| [eval-sentence-judge.md](eval-sentence-judge.md) | write-a-sentence → judge | built (TD-20); Jev tested (TD-21) |
| [eval-sentence-feedback.md](eval-sentence-feedback.md) | write-a-sentence → feedback writer | built 2026-10-04 (D55) |
| — | share-an-article → fact checker | **missing** |
| — | save-a-word → example writer, "real word?" check | **missing** |
| — | fill-in-the-word → sentence writer | **missing** (needed before it ships) |

## Infrastructure — under every flow

| Diagram | What it shows | Decision |
|---|---|---|
| [infra-model-fallback.md](infra-model-fallback.md) | How any model call stays fast: fixed host order, a backup model races a slow one | D49 |
| [infra-user-day.md](infra-user-day.md) | How each request works out the user's "today" (timezone, 4 am start, never back) | D51 |
