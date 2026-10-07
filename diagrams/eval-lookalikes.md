# Eval: lookalike writer (fill-in hint)

**Tests:** the LOOKALIKE WRITER for the fill-in hint (PRD D58): three words that look like the word but mean
something very different. Required by PRD D55. Record: `docs/model-bakeoff.md` "Lookalike writer".

```mermaid
flowchart TD
    S[("Test set: the 51 golden words + part of speech + meaning<br/>data/evals/golden/words.json")] --> RUN
    REG["Candidate from the model list"] --> RUN
    RUN["Candidate writes 5 lookalikes per word<br/>(prompts/exercises/lookalikes.md)<br/>python src/evals look run &lt;model&gt;"] --> CODE
    CODE["Code: real dictionary word? same part of speech?<br/>not a form of the target? keep the first 3"] --> PK
    PK["Blind packet: each lookalike next to the word's fill-in sentence<br/>python src/evals look export &lt;runs&gt;"] --> GR
    GR["Grader: looks similar? · very different meaning? ·<br/>could it fill the blank? (today: Claude Code)"] --> SC
    JEV["Jev: P(natural) of each lookalike in the blank<br/>python src/evals look jev &lt;runs&gt;"] --> JR
    GR --> JR["Does Jev catch the ones that fit? per cut-off<br/>python src/evals look jev-report"]
    SC["Scored: words with 3 good lookalikes · fits · $ and s per word<br/>python src/evals look report"] --> P{"Founder picks"}
    JR --> P
```
