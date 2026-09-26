# Quality benchmarks for a constrained English rewrite engine (as of 2026-09-26)


Method note: 24 tool calls. Several leaderboards (Artificial Analysis, EQ-Bench, Kaggle FACTS)
render their data with JavaScript, so the text fetcher could not pull their tables. Numbers below
come from pages whose text could be read. Fetches were summarised by a small model, so treat
single-digit differences as needing a manual check on the live page.

## 1. Which benchmarks measure the qualities this task needs

### Takeaway
No public benchmark measures "put vocabulary word X in only where it is idiomatic." The closest
proxies are: Vectara HHEM for faithfulness (it scores summaries, not rewrites), IFBench for
following constraints, and LMArena creative-writing or EQ-Bench for prose quality. Each tests a
neighbouring skill, so a private head-to-head on RetAIn's own texts is still required.

### Cited Findings
- Vectara Hallucination Leaderboard: the HHEM-2.3 classifier scores factual consistency of summaries of 7,700+ articles (50 to 24,000 words, across news, science, legal, medical and other domains). Prompt: "Summarize using only the information in the given passage. Do not infer." Temperature 0. — [Vectara leaderboard](https://github.com/vectara/hallucination-leaderboard)
- Its average summary length is about 55 to 250 words, much shorter than RetAIn's 300 to 3,000-word outputs. — [Vectara README](https://raw.githubusercontent.com/vectara/hallucination-leaderboard/main/README.md)
- IFBench: "precise instruction-following generalization on 58 diverse, verifiable out-of-domain constraints." — [Artificial Analysis IFBench](https://artificialanalysis.ai/evaluations/ifbench)
- AA-Omniscience hallucination rate: incorrect / (incorrect + partial + not attempted). It measures whether a model admits it does not know a knowledge question, not whether it stays grounded in a source. — [AA-Omniscience](https://artificialanalysis.ai/evaluations/omniscience)
- The FACTS suite covers grounding, parametric knowledge, search and multimodal. Gemini 3.1 Flash-Lite scores 40.6% overall; Gemini 3 Flash scores 50.4%. — [LayerLens](https://layerlens.ai/blog/gemini-3-1-flash-lite-benchmark-results-efficiency-model-comparison) (secondary source; the Kaggle leaderboard did not render: [Kaggle FACTS](https://www.kaggle.com/benchmarks/google/facts))
- EQ-Bench Creative Writing v3 is judged by an LLM using a rubric plus Elo. It adds a "slop" score (matches against a list of phrases LLMs overuse) and a repetition metric. — [EQ-Bench CW](https://eqbench.com/creative_writing.html)
- LMArena has a creative-writing category built from human pairwise votes. — [Arena creative writing](https://arena.ai/leaderboard/text/creative-writing)
- Lexical and collocation naturalness: I found only research datasets, no maintained leaderboard. Examples: the "English accent" corpus-level lexical/syntactic naturalness metrics (French and Chinese only) — [arXiv 2410.15956](https://arxiv.org/pdf/2410.15956); DICE for understanding idioms in context — [arXiv 2410.16069](https://arxiv.org/html/2410.16069); AlphaMWE on multiword-expression errors in translation — [arXiv 2609.06634](https://arxiv.org/html/2609.06634).

### Inferences
- The benchmark closest to RetAIn's "no invented attributions" failure is Vectara HHEM. It is still a proxy. Summaries compress and rewrites expand, and the known Flash-Lite failure (adding attributions) is an extrinsic addition, which HHEM is designed to flag.
- Word discipline (skip a word when it doesn't fit) is closest to IFBench-style constraint following combined with judgement. No benchmark rewards *declining* to use a word, so RetAIn's skip-rate finding cannot be predicted from public scores.

### Gaps
- I found no benchmark for placing target words idiomatically or for collocation correctness in English generation.
- I did not verify Multi-IF or IFEval standings for small models (not fetched).
- Scale SEAL: not checked.

## 2. Current standings of small/fast models

### Takeaway
On faithfulness (Vectara, 2026-09-22), GPT-5.4 nano (3.1%) and Gemini 2.5 Flash-Lite (3.3%) have the lowest hallucination rates. Gemini 3.1 Flash-Lite preview is mid-pack at 8.2%, and Claude Haiku 4.5 is at 9.8%. The Grok fast models are worst (18 to 20%). On human-rated creative writing (LMArena, 2026-09-25), a newer **gemini-3.5-flash-lite** leads the small models, ahead of 3.1 Flash-Lite, GPT-5.4 mini and Haiku 4.5.

### Cited Findings
Vectara HHEM leaderboard, last updated 2026-09-22 (hallucination rate, lower is better / answer rate) — [Vectara README](https://raw.githubusercontent.com/vectara/hallucination-leaderboard/main/README.md):
- openai/gpt-5.4-nano-2026-03-17: 3.1% / 100%
- google/gemini-2.5-flash-lite: 3.3% / 99.5%
- meta-llama/Llama-3.3-70B: 4.1%
- google/gemma-3-12b-it: 4.4%; gemma-4-26b-a4b-it: 5.2%; gemma-4-31b-it: 7.4%
- qwen/qwen3-8b: 4.8%; qwen3-4b: 5.7%; qwen3.5-flash-2026-02-23: 10.5%
- mistralai/mistral-small-2501: 5.1% (newer Ministral 3 models: 19.4 to 24.2%)
- deepseek V3.2-Exp: 5.3%; V3.2: 6.3% (answer rate 92.6%); V4-Pro: 8.6%. V4 Flash is not listed.
- openai/gpt-5.4-mini-2026-03-17: 5.5%
- google/gemini-2.5-flash: 7.8%
- **google/gemini-3.1-flash-lite-preview: 8.2% / 99.6%**
- MiniMax m2p5: 9.1%; m2p1: 11.8%; m2p7: 12.9%
- GLM-4.7-flash: 9.3% (answer rate 91.6%); glm-5: 10.1%
- **anthropic/claude-haiku-4-5-20251001: 9.8% / 99.5%**
- openai/gpt-5-nano: 10.5%; gpt-5-mini: 12.9%
- kimi-k2.6: 10.8%; Kimi-K2.5: 14.2%
- google/gemini-3-flash-preview: 13.5%
- openai/gpt-oss-120b: 14.2%
- xai grok-4-1-fast non-reasoning: 17.8%; reasoning: 19.2%; grok-4-fast: 19.7 to 20.2%
- Gemini 3.5 Flash / Flash-Lite do not appear in the rows I retrieved (unverified absence).

LMArena creative-writing category, last updated 2026-09-25 (score ± CI, votes) — [Arena](https://arena.ai/leaderboard/text/creative-writing):
- Top: claude-opus-5.5-high 1521±29; gemini-3.7-flash-high is #4 at 1492±10
- #60 gemini-3.5-flash-lite 1435±8 (6,786 votes)
- #85 gemini-3.1-flash-lite-preview 1413±7 (10,414)
- #102 gpt-5.4-mini-high 1402±7
- #113 gemini-2.5-flash 1394±5
- #130 claude-haiku-4-5 1387±5 (23,265)

IFBench (unverified, from a search snippet whose wording contradicted itself): GPT-5.4 nano 76%, Gemini 3.1 Flash-Lite preview 77%, Claude Haiku 4.5 54%. The snippet traces to an Artificial Analysis post that returned HTTP 402 when fetched. — [AA on X](https://x.com/ArtificialAnlys/status/2037043552405119395); the same post says "GPT-5.4 nano is the standout, scoring ahead of both Claude Haiku 4.5 and Gemini 3.1 Flash-Lite Preview with lower per token pricing" (search-result text). The AA IFBench page shows the top scores as Grok 4.3 at 83.3% and MiniMax-M3 at 82.9%. — [AA IFBench](https://artificialanalysis.ai/evaluations/ifbench)

EQ-Bench Creative Writing v3: the live table did not render. Per search-result summaries, Claude Opus 5 leads at Elo 2121, Kimi K3 is at 2071 and GPT-5.6 Sol at 1963, with no Haiku or Flash in the top ranks. — [EQ-Bench](https://eqbench.com/creative_writing.html) (unverified). The llm-stats mirror lists only 14 models, mostly Qwen, with no small Gemini, GPT or Haiku models. — [llm-stats CW v3](https://llm-stats.com/benchmarks/creative-writing-v3)

Google's model card for Gemini 3.1 Flash-Lite (March 2026) — [DeepMind model card](https://deepmind.google/models/model-cards/gemini-3-1-flash-lite/):
- Output speed: Flash-Lite 363 tok/s; GPT-5 mini 71; Haiku 4.5 108; Grok 4.1 Fast 145
- SimpleQA: Flash-Lite 43.3%, GPT-5 mini 9.5%, Haiku 5.5%. This measures stored world knowledge, not grounding in a source.
- GPQA Diamond: 86.9 / 82.3 / 73.0 / 84.3 (Flash-Lite / GPT-5 mini / Haiku / Grok)

### Inferences
- The Vectara data fits RetAIn's internal finding: Gemini 3.1 Flash-Lite needs a fact judge. It hallucinates at more than twice the rate of GPT-5.4 nano and 2.5 Flash-Lite in summarisation.
- Two candidates are untested internally and justify a bake-off slot: GPT-5.4 nano (best faithfulness, similar price) and gemini-3.5-flash-lite (best small-model prose preference). Gemini 3.5 Flash-Lite has no faithfulness data found.
- On creative writing, the gaps between small models are 20 to 50 points with CIs of ±5 to 8, so the ordering is real but modest. General creative-writing preference votes do not measure a constrained rewrite.
- A high SimpleQA score (stored knowledge) could make a model *more* willing to add outside facts during a rewrite. This is a hypothesis, not a finding.

### Gaps
- I could not extract per-model AA-Omniscience hallucination rates or a full IFBench table (the pages are JS-rendered).
- I found no small-model rows for Llama 4, gpt-oss-20b or DeepSeek V4 Flash on the writing leaderboards.

## 3. Artificial Analysis: intelligence vs price vs speed

### Takeaway
On AA Intelligence Index v4.3.2, Gemini 3.1 Flash-Lite scores 16, above the median of 13 for its price tier. Blended price is $0.22 per 1M tokens and output speed is about 340 tok/s. AA reported that GPT-5.4 nano scores above both Flash-Lite and Haiku 4.5 at a lower per-token price. The intelligence index is weighted toward reasoning and coding, so it is a weak predictor for this task.

### Cited Findings
- Gemini 3.1 Flash-Lite: index 16 (v4.3.2; tier median 13); $0.25 in / $1.50 out; blended $0.22; 339.7 tok/s; TTFT 5.98 s; released 2026-03-03. — [AA model page](https://artificialanalysis.ai/models/gemini-3-1-flash-lite-preview)
- GPT-5.4 nano costs $0.20 / $1.25 and mini costs $0.75 / $4.50, both released 2026-03-17. DeepSeek V4 Flash costs $0.14 / $0.28 and was released 2026-04-24 (MoE with 13B active parameters). — [DataCamp](https://www.datacamp.com/blog/deepseek-v4-flash-vs-gpt-5-4-mini-and-nano)
- Haiku 4.5 costs $1.00 / $5.00, which is 4 to 5 times Flash-Lite and nano. — [DeepMind model card](https://deepmind.google/models/model-cards/gemini-3-1-flash-lite/)
- The AA leaderboard top is Claude Opus 5.5 at 58. The top open-weights models are MiMo-V2.6-Pro (46), GLM-5.3 (45) and Kimi K3 (44). Gemini 2.5 Flash-Lite (non-reasoning) has the lowest TTFT at 0.30 s. — [AA models](https://artificialanalysis.ai/models)

### Inferences
- The 5.98 s TTFT is probably the reasoning configuration (inferred). Reasoning effort sets latency, so compare models at a fixed thinking budget.

### Gaps
- I could not extract AA index values for GPT-5.4 nano/mini, Haiku 4.5, Grok fast or Qwen small models.

## 4. LLM-as-judge reliability for the fact judge and the word-fit judge

### Takeaway
LLM judges are internally consistent, but they agree with humans less than with each other. They favour their own model family, even on binary rubric checks. RetAIn's fact judge should therefore come from a different family than the rewrite model and be calibrated against a small human-labelled set. A cheaper judge is acceptable only if that calibration shows adequate agreement.

### Cited Findings
- Study of 21 judges from 9 providers (~541k judgments): test-retest reliability above 0.95 coexists with position bias above 0.10. Exact-match agreement overstates reliability by 33 to 41 percentage points compared with Cohen's kappa. Judge rankings shift by up to 14 places across benchmarks. — [arXiv 2606.19544](https://arxiv.org/abs/2606.19544)
- In rubric-based binary checks, judges were more than 50% more likely to wrongly mark a criterion as satisfied on their own outputs, even with objective rubrics (IFEval). Ensembling judges reduces the bias but does not remove it. — [arXiv 2604.06996](https://arxiv.org/abs/2604.06996)
- Same-family lift in judge panels is 3.4 to 8.4 percentage points. Panel composition changes 18.5% of pairwise outcomes, and 55.4% of AB/BA pairs reverse when order is swapped. — [arXiv 2609.17857](https://arxiv.org/abs/2609.17857)
- Inter-LLM agreement (~0.35) exceeds LLM-human agreement (0.27 to 0.32). Calibration on a small human-anchored set helps smaller judges but does not reach human reliability. — [arXiv 2606.03043](https://arxiv.org/abs/2606.03043) (from a search summary; the abstract was not fetched)
- Stronger models' self-preference is partly justified by genuinely better outputs. — [arXiv 2504.03846](https://arxiv.org/html/2504.03846v2)

### Inferences
- Today, Gemini Flash-Lite judging Gemini Flash-Lite output (if that is the setup) is exposed to same-family leniency on "is this claim in the source?". A cross-family judge such as GPT-5.4 nano is a reasonable test: it is similarly priced and has the best Vectara faithfulness score. A dedicated classifier (HHEM-2.1-Open) is a free extra signal for faithfulness only.
- For word fit, a binary per-word verdict ("idiomatic: yes/no + reason") is easier to calibrate than a 1 to 10 score.

### Gaps
- I found no study of LLM judges rating collocation or idiomatic correctness specifically.

## 5. Bake-off design

### Takeaway
Use paired comparisons (every model rewrites the same texts), report uncertainty, and blind the human rater. Score each placed word with a binary rubric and a separate skip decision. Then validate any LLM judge against those human labels before trusting it at scale.

### Cited Findings
- Recommended statistics: paired differences between models on the same items, clustered standard errors when items share a source text, power/sample-size planning before running, and averaging over multiple generations per item. — [Miller, arXiv 2411.00640](https://arxiv.org/abs/2411.00640)
- Randomise or swap presentation order in pairwise comparisons, because position bias is large (55.4% of pairs reverse). — [arXiv 2609.17857](https://arxiv.org/abs/2609.17857)
- Report kappa, not raw agreement, when validating a judge. — [arXiv 2606.19544](https://arxiv.org/abs/2606.19544)

### Inferences (proposed design, my own synthesis)
- Unit of analysis: each target-word placement is clustered within its article. With about 20 to 30 real user texts × 4 to 6 words each, you get roughly 100 to 180 word decisions per model. That is enough to see large differences in misuse rate (for example 5% vs 15%), not small ones.
- Per-word rubric: (a) placed or skipped; (b) if placed: idiomatic / acceptable-but-marked / wrong collocation or sense; (c) if skipped: was there a natural slot (a missed opportunity)? Misuse carries the heaviest weight, per the product's quality bar.
- Per-text rubric: added facts, quotes or attributions (count them, verified against the source); reading level kept (not simplified); fluency.
- The founder rates blind, with the model hidden and the order shuffled. Double-rate about 20% of items to check self-consistency.
- Log latency and cost per piece at a fixed reasoning setting.

### Gaps
- I found no published sample-size guidance specific to judging idiomatic word placement. The numbers above are an inference.
