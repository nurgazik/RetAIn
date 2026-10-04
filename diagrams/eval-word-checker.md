# Eval: word checker

**Tests:** the WORD CHECKER in [flow-share-an-article.md](flow-share-an-article.md) — the live
yes/no gate that rejects a highlighted word used unidiomatically. Runs while building, never on a
user's request. Jev is a candidate here (PRD D54, backlog TD-21).

```mermaid
flowchart TD
    A["Article-rewrite eval runs<br/>(see eval-article-rewrite.md)"] --> S
    S[("Test set: highlighted words from those runs, each in its sentence<br/>no set of its own")] --> RUN
    K["Answer key: the grader's verdict per word<br/>(or the founder's blind label, when given)<br/>idiomatic · acceptable · wrong"] --> SC
    REG["Candidate from the model list<br/>(Jev to be added, TD-21)"] --> RUN
    RUN["Ask the candidate production's own checker question<br/>keep or reject each word?<br/>python src/evals judge &lt;model&gt;"] --> SC
    SC["Scored on: wrong words caught (the reader is protected)<br/>good words rejected (the reader loses a word)"] --> LB
    LB["Leaderboard<br/>python src/evals report"] --> P{"Founder picks"}
```

## Results so far

Against the grader's verdicts (100 wrong, 116 idiomatic words): production's Gemma caught 55% of
wrong words and rejected 2 good ones; gpt-6-luna caught 91% but rejected 17 good ones. Why this
step has the most to gain from a better or cheaper checker.

## Answer key

Borrowed from the article-rewrite eval: the grader's per-word verdicts. If the grader is wrong,
this eval inherits the error — the founder's blind labels are the check (none given yet).
