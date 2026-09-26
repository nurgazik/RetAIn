# Open-weight LLMs (non-Chinese labs) and fast inference hosts as RetAIn rewrite-engine candidates

> Research date: 2026-09-26. About 16 tool calls. Several official pricing pages (groq.com/pricing, cerebras.ai/pricing) render prices by JavaScript and could not be read. Where a price comes from a docs page it is marked official; where it comes from an aggregator (Artificial Analysis, OpenRouter, pricepertoken, morphllm) it is marked as such.
> Cost formula used throughout: 2,500 input + 1,200 output tokens per rewrite call. Incumbent gemini-3.1-flash-lite = ~$0.0017/call, ~3 s for ~600 words (project figure, not re-verified here).

## Which open-weight models from non-Chinese labs are current candidates?

### Takeaway
The non-Chinese open-weight field in late September 2026 is led by OpenAI gpt-oss (20b/120b, Aug 2025), Google Gemma 4 (Apr–Jun 2026, Apache 2.0) and Mistral Small 4 (Mar 2026, Apache 2.0). Meta's Llama line has not produced a clearly verified newer open release than Llama 4 (Apr 2025) in the sources found. The strongest open-weight models overall are Chinese (Qwen3.8, GLM-5.3, DeepSeek V4, Kimi K3).

### Cited Findings
- **OpenAI gpt-oss-120b**: 117B-parameter MoE (mixture of experts: only part of the network runs per token), 5.1B active parameters, released 2025-08-05, 131K context, configurable reasoning depth, knowledge cutoff June 2024 — [OpenRouter model page](https://openrouter.ai/openai/gpt-oss-120b)
- gpt-oss-20b and 120b are both in Ollama (`gpt-oss:20b`) — [PromptQuorum 2026 releases](https://www.promptquorum.com/local-llms/local-llm-model-updates-2026)
- **Google Gemma 4**: released 2026-04-02 in four sizes (E2B, E4B, 26B MoE, 31B dense), Apache 2.0 licence (a change from earlier Gemma terms, broadening commercial use); a 12B "Unified" multimodal model added 2026-06-03 — [gHacks](https://www.ghacks.net/2026/04/06/google-releases-gemma-4-in-four-model-sizes-under-apache-2-0-license/); [Google model card](https://ai.google.dev/gemma/docs/core/model_card_4) (card URL surfaced in search; not fetched)
- Gemma 4 31B: 30.7B dense, 262K context, configurable reasoning mode, 140+ languages — [OpenRouter Gemma 4 31B](https://openrouter.ai/google/gemma-4-31b-it/providers)
- Gemma 4 26B-A4B (MoE, ~4B active) available in Ollama as `gemma4:26b`; E2B needs ~2 GB RAM — [PromptQuorum](https://www.promptquorum.com/local-llms/local-llm-model-updates-2026) (this source dates 26B-A4B to June 2026, conflicting with gHacks' April 2 date for the 26B MoE; unresolved)
- **Mistral Small 4**: March 2026, 119B MoE with 6.5B active, Apache 2.0, merges instruction following, reasoning, vision and agentic coding in one checkpoint — [Thunder Compute, Sept 2026](https://www.thundercompute.com/blog/best-open-source-llms); [Serenities AI](https://serenitiesai.com/articles/mistral-ai-models-2026-complete-guide)
- **Mistral Large 3**: Dec 2025, 675B MoE (41B active), Apache 2.0 — [Thunder Compute](https://www.thundercompute.com/blog/best-open-source-llms)
- Mistral Small 3.2 (improved instruction following) listed as Feb 2026 — [PromptQuorum](https://www.promptquorum.com/local-llms/local-llm-model-updates-2026) (date looks doubtful; Mistral Small 3.2 is widely known as a mid-2025 release — treat as unverified)
- **Meta Llama 4**: Maverick (400B, 17B active) and Scout (109B, 17B active), April 2025, Llama 4 Community licence (custom, not OSI open source) — [Thunder Compute](https://www.thundercompute.com/blog/best-open-source-llms)
- One guide claims "Llama 5 uses Meta's custom community license… commercial deployment at scale still needs legal review" — [search snippet, aiunpacking.com](https://aiunpacking.com/guides/open-source-ai-models-2026-llama-mistral-deepseek/) (not fetched; no primary Meta source found confirming a Llama 5 open-weight release)
- **NVIDIA Nemotron 3 Super 120B** (12B active, late 2025) and Nemotron Ultra 253B (dense, Apr 2025), NVIDIA Open Model licence — [Thunder Compute](https://www.thundercompute.com/blog/best-open-source-llms)
- **Microsoft Phi**: sources mention only Phi-4 family; "Phi-4 Mini (3.8B)" listed; no Phi-5 found — [PromptQuorum](https://www.promptquorum.com/local-llms/local-llm-model-updates-2026)
- Other non-Chinese 2026 release: Poolside Laguna XS 2.1 (33B/3B-active MoE, coding-focused, OpenMDW-1.1 licence, July 2026) — [PromptQuorum](https://www.promptquorum.com/local-llms/local-llm-model-updates-2026); Apertus (Swiss) exists — [Wikipedia](https://en.wikipedia.org/wiki/Apertus_(LLM)) (not fetched)
- Chinese open-weight context (not researched in depth): Qwen3.8 Max leads a Sept 2026 open-weight ranking (71.8), GLM-5.3 second (65.6), DeepSeek V4 Pro 0813 third (63.5); GLM-5.3-Flash weights released 2026-08-26; Kimi K3 (2.8T MoE, ~50B active) 2026-07-16 — [Thunder Compute / BenchLM via search](https://benchlm.ai/best/open-source); Qwen3.8-27B released 2026-08-14, Apache 2.0 — [PromptQuorum](https://www.promptquorum.com/local-llms/local-llm-model-updates-2026)

### Inferences
- For English prose rewriting the realistic non-Chinese shortlist is gpt-oss-120b, gpt-oss-20b, Gemma 4 31B / 26B-A4B, and Mistral Small 4. Llama 3.3 70B and Llama 4 are older and (see hosts) no longer cheap or widely hosted as production models.
- gpt-oss is a reasoning model: it emits hidden/visible reasoning tokens before the answer. That adds latency and billed output tokens, and matters because the incumbent has no hidden thinking. Its reasoning effort can be set low, which should be the setting to test.
- Gemma 4 comes from the same lab as the incumbent (Gemini) under Apache 2.0, which makes it the lowest-licence-risk candidate.

### Gaps
- No primary source fetched for gpt-oss licence text (widely reported as Apache 2.0; unverified here) or for its reasoning-effort levels (low/medium/high; unverified here beyond "configurable reasoning depth").
- Could not confirm whether any Llama 5 open weights exist; no Meta source found.
- Nothing found on AI2 OLMo 3/4, IBM Granite 4/5, Cohere, Liquid, Arcee 2026 releases in the budget available.
- Magistral / Ministral / Devstral 2026 versions not covered.

## Which hosts serve these models, at what price and speed, and what does a rewrite call cost?

### Takeaway
On price, gpt-oss-120b on budget hosts (DeepInfra, CoreWeave, ~$0.0003/call) is about one-sixth of the incumbent. On speed, Cerebras gpt-oss-120b (~1,650–3,000 tok/s) roughly matches the incumbent's cost ($0.0018/call) while generating 1,200 tokens in under a second. Groq gpt-oss-120b sits in the middle ($0.0011/call, ~500 tok/s). Reasoning tokens will raise all of these figures by an unmeasured amount.

### Cited Findings
Prices per 1M tokens (input / output), computed cost per rewrite call (2,500 in + 1,200 out, excluding reasoning tokens):

| Host | Model | $ in / out | Cost/call | Speed | Source |
|---|---|---|---|---|---|
| Groq | gpt-oss-120b | 0.15 / 0.60 | $0.00110 | 500 tok/s (Groq); 474 tok/s, TTFT 4.89 s (AA) | [Groq docs](https://console.groq.com/docs/models) (official); [Artificial Analysis](https://artificialanalysis.ai/models/gpt-oss-120b/providers) |
| Groq | gpt-oss-20b | 0.075 / 0.30 | $0.00055 | 1,000 tok/s | [Groq docs](https://console.groq.com/docs/models) (official) |
| Groq | Llama 3.1 8B / Llama 3.3 70B | "Enterprise" pricing only | — | 560 / 280 tok/s | [Groq docs](https://console.groq.com/docs/models) |
| Groq (preview) | Qwen3.8-27B | 0.80 / 4.00 | $0.00680 | 450 tok/s | [Groq docs](https://console.groq.com/docs/models); preview models "should not be used in production" |
| Cerebras | gpt-oss-120b | 0.35 / 0.75 | $0.00178 | ~3,000 tok/s (Cerebras docs); 1,655 tok/s, TTFT 1.68 s (AA) | price: [Morph](https://www.morphllm.com/cerebras-pricing) (aggregator, "as of July 2026"); speed: [Cerebras docs](https://inference-docs.cerebras.ai/models/overview), [AA](https://artificialanalysis.ai/models/gpt-oss-120b/providers) |
| Cerebras | qwen-3.8-27b | not shown | — | ~1,850 tok/s | [Cerebras docs](https://inference-docs.cerebras.ai/models/overview) |
| SambaNova | gpt-oss-120b | not found | — | 703 tok/s, TTFT 3.98 s | [AA](https://artificialanalysis.ai/models/gpt-oss-120b/providers) |
| DeepInfra | gpt-oss-120b | 0.04 / 0.17 | $0.00030 | not captured | [AA](https://artificialanalysis.ai/models/gpt-oss-120b/providers) |
| CoreWeave | gpt-oss-120b | 0.03 / 0.17 | $0.00028 | not captured | [AA](https://artificialanalysis.ai/models/gpt-oss-120b/providers) |
| Crusoe | gpt-oss-120b | 0.06 / 0.20 | $0.00039 | not captured | [AA](https://artificialanalysis.ai/models/gpt-oss-120b/providers) |
| OpenRouter (cheapest route) | gpt-oss-120b | 0.03 / 0.17 | $0.00028 | not shown | [OpenRouter](https://openrouter.ai/openai/gpt-oss-120b) |
| Together | gpt-oss-120b | 0.15 / 0.60 | $0.00110 | — | [Together pricing](https://www.together.ai/pricing) (official) |
| Together | Gemma 4 31B | 0.39 / 0.97 | $0.00214 | — | [Together pricing](https://www.together.ai/pricing) |
| OpenRouter (cheapest route) | Gemma 4 31B | 0.08 / 0.30 | $0.00056 | not shown | [OpenRouter](https://openrouter.ai/google/gemma-4-31b-it/providers) |
| Together | Llama 3.3 70B | 1.04 / 1.04 | $0.00385 | — | [Together pricing](https://www.together.ai/pricing) |
| Together | Qwen3.8 Flash (CN) | 0.09 / 0.28 | $0.00056 | — | [Together pricing](https://www.together.ai/pricing) |
| Together | GLM-5.3-Flash (CN) | 0.15 / 0.50 | $0.00098 | — | [Together pricing](https://www.together.ai/pricing) |
| Together | DeepSeek V4.1 Flash (CN) | 0.30 / 1.20 | $0.00219 | — | [Together pricing](https://www.together.ai/pricing) |
| Together | Qwen3.7-Plus (CN) | 0.32 / 1.28 | $0.00234 | — | [Together pricing](https://www.together.ai/pricing) |
| Together | Kimi K3 (CN) | 3.00 / 15.00 | $0.02550 | — | [Together pricing](https://www.together.ai/pricing) |

- Artificial Analysis tracks 18 providers for gpt-oss-120b; fastest output speed Cerebras 1,655 tok/s, SambaNova 703, Groq 474; lowest TTFT Cerebras 1.68 s. Its measurements are for gpt-oss-120b at **high** reasoning, so TTFT includes thinking time — [Artificial Analysis](https://artificialanalysis.ai/models/gpt-oss-120b/providers)
- Groq's AA output price ($0.52) differs slightly from Groq's own docs ($0.60) — [AA](https://artificialanalysis.ai/models/gpt-oss-120b/providers) vs [Groq docs](https://console.groq.com/docs/models); prefer the official $0.60.
- Cerebras: gpt-oss-120b is "the only production-sanctioned model on Cerebras's public rate card" — [Morph](https://www.morphllm.com/cerebras-pricing) (aggregator). Cerebras docs list only gpt-oss-120b and qwen-3.8-27b as shared models; others via Dedicated Inference — [Cerebras docs](https://inference-docs.cerebras.ai/models/overview)
- Cerebras says shared-inference models are "the original, unpruned versions", with weight-only quantization in storage and full precision for activations, attention and KV cache — [Cerebras docs](https://inference-docs.cerebras.ai/models/overview)
- Together's pricing page does not list gpt-oss-20b, Llama 4, Mistral Small or Nemotron as serverless models — [Together pricing](https://www.together.ai/pricing)

**Data retention**
- Groq: does not retain customer data by default except for reliability/abuse monitoring; does not train on inputs/outputs; any customer can switch on Zero Data Retention (ZDR: the provider keeps no copy of prompts or outputs) self-serve in Data Controls, which also removes the abuse-monitoring retention — [Groq "Your Data"](https://console.groq.com/docs/your-data) (via search summary)
- OpenRouter: tracks each endpoint's data policy; a privacy setting restricts routing to ZDR endpoints; can be enforced globally, per model group or per request — [OpenRouter ZDR docs](https://openrouter.ai/docs/guides/features/zdr) (via search summary)

### Inferences
- Speed winner: Cerebras gpt-oss-120b. 1,200 output tokens at ~1,650 tok/s is ~0.7 s plus TTFT; even with reasoning, total should beat the incumbent's ~3 s. Cost is roughly equal to the incumbent.
- Cost winner: gpt-oss-120b on DeepInfra/CoreWeave via OpenRouter, ~5–6x cheaper than the incumbent before reasoning tokens; speed of these hosts was not captured and is likely far slower than Cerebras/Groq.
- Balanced: Groq gpt-oss-120b (~35% cheaper than incumbent, ~2.4 s generation) or Groq gpt-oss-20b (~3x cheaper, ~1.2 s) if 20b quality holds.
- Gemma 4 31B via cheap OpenRouter routes (~$0.00056) is the closest "Google-style" non-reasoning option at a third of incumbent cost; speed unknown.
- The two short judge calls would cost a small fraction of the rewrite on any of these hosts.

### Gaps
- Fireworks, DeepInfra (official page), SambaNova (price), Google Vertex AI and AWS Bedrock open-model prices were not fetched within the call budget.
- Official Cerebras rate card not readable (JS); $0.35/$0.75 is from an aggregator.
- No measured throughput/TTFT for Gemma 4 or Mistral Small 4 on any host.
- ZDR terms for Cerebras, Together, Fireworks, DeepInfra, SambaNova not verified.
- Reasoning-token overhead of gpt-oss at low effort for this task is unmeasured; must be measured in `src/bakeoff.py`.

## Can a Mac mini self-host a rewrite model fast enough (~1,200 tokens in under ~10 s)?

### Takeaway
Probably not at acceptable quality. The best measured figure found is gpt-oss-20b at ~73 tok/s on an M4 Pro (MLX), which needs ~16 s for 1,200 tokens before counting prompt processing and reasoning tokens. Base M4 16 GB machines can only run small (2–5B effective) models, which are unlikely to meet the idiomatic-English bar.

### Cited Findings
- gpt-oss-20b (mxfp4, MLX) on M4 Pro: 73.24 tok/s generation (512-token prompt → 128 output) — [search summary citing Rapid-MLX / benchmarks](https://github.com/raullenchai/Rapid-MLX) (exact source page not isolated; treat as indicative)
- Gemma-4-12B 4-bit on MLX: 31.87 tok/s (chip not stated in snippet) — [search summary](https://www.marketcalls.in/llm-models/open-source-ai-is-catching-up-fast-gemma-4-just-proved-it.html)
- A user reported Gemma 4 31B at 40–50 tok/s on "a MacBook with similar specs" — same search summary; this looks implausible for a 31B dense model on M4 Pro memory bandwidth and is treated as unreliable.
- Base Mac mini M4 16 GB in production: Gemma 4 E2B (7.2 GB on disk) did a classification in 1.9 s; Gemma 4 E4B (9.6 GB) took ~50–60 s per summarisation task; Qwen 3.5 35B MoE (3B active) at IQ3_XXS quantisation (13 GB) ran at 17.3 tok/s via llama.cpp with mmap paging experts from SSD — [jock.pl, "Running a 35B Local LLM on a Mac Mini"](https://thoughts.jock.pl/p/local-llm-35b-mac-mini-gemma-swap-production-2026)
- MLX has day-one Gemma 4 support; a 16 GB M4 can run Gemma 4 E4B at 8-bit — [search summary](https://www.marketcalls.in/llm-models/open-source-ai-is-catching-up-fast-gemma-4-just-proved-it.html)
- Relevant 2026 papers exist but were not read: [SiliconBench (speed/memory/fidelity on unified-memory desktops)](https://arxiv.org/pdf/2609.19169), [BaseRT native Metal inference](https://arxiv.org/pdf/2607.00501), [GreenBench Apple Silicon](https://arxiv.org/pdf/2608.28667)

### Inferences
- RAM fit (inferred from parameter counts at ~4-bit ≈ 0.5–0.6 GB per billion parameters plus OS/KV-cache headroom; not measured):
  - 16 GB: Gemma 4 E2B/E4B, Phi-4 Mini, 8B-class models. gpt-oss-20b (~12–13 GB in mxfp4) is marginal.
  - 24 GB: gpt-oss-20b comfortably; Gemma 4 12B; Gemma 4 26B-A4B at 4-bit is tight.
  - 32 GB: Gemma 4 26B-A4B and 31B at 4-bit; Mistral Small 3.x 24B.
  - 64 GB (M4 Pro only): gpt-oss-120b (~60+ GB in mxfp4) does not fit with headroom; Mistral Small 4 (119B) at 4-bit (~60 GB) also marginal. Everything ≤ 32B fits.
- Speed: generation speed on Apple Silicon is bounded by memory bandwidth divided by active-weight bytes, so MoE models with few active parameters (gpt-oss-20b 3.6B active — figure from general knowledge, unverified; Gemma 4 26B-A4B ~4B active) are the only ones plausibly near 10 s for 1,200 tokens, and only on M4 Pro. Base M4 has roughly half the M4 Pro bandwidth (from general knowledge, unverified), so expect about half the speed.
- Even at best, self-hosting would be ~5x slower than the incumbent and would load the same Mac mini that runs the FastAPI service, with one request at a time. It saves ~$0.0017/call, which is negligible at founder-only usage.
- Quality risk: the project's own bakeoff found word-discipline and idiom quality sensitive to model deliberation; small (2–5B effective) models are the most likely to force awkward collocations, which the rewrite bar treats as worse than nothing.

### Gaps
- The actual Mac mini spec is unknown; no benchmark found for Gemma 4 26B-A4B or Mistral Small on M4/M4 Pro.
- Prompt-processing (prefill) speed for a 2,500-token input on Mac was not found; it adds seconds.
- No idiom-quality evidence for small models on this specific task.

## What evidence exists on quality (English writing, instruction following, faithfulness)?

### Takeaway
No task-relevant quality evidence was found within budget. Published claims for these models focus on reasoning, coding and maths benchmarks, which do not predict idiomatic word placement or factual faithfulness in rewriting. The project's own bakeoff harness is the right instrument.

### Cited Findings
- Gemma 4 31B marketed for "coding, reasoning, and document analysis" — [OpenRouter](https://openrouter.ai/google/gemma-4-31b-it/providers)
- Gemma 4 26B-A4B: 89% AIME 2026; Qwen3.8-27B: 89.2% GPQA Diamond — [PromptQuorum](https://www.promptquorum.com/local-llms/local-llm-model-updates-2026) (maths/science, not writing)
- gpt-oss described as "o3-mini reasoning level" — [PromptQuorum](https://www.promptquorum.com/local-llms/local-llm-model-updates-2026)
- A browser-agent team tested Cerebras gpt-oss-120b and chose not to use it (reason not read) — [humanbrowser.cloud](https://humanbrowser.cloud/blog/cerebras-gpt-oss-browser-agent-2026) (title only)

### Inferences
- gpt-oss's June 2024 knowledge cutoff is irrelevant for rewriting user-supplied text, but its reasoning style may help word discipline (consistent with the project's dose-response finding) at a latency cost.
- Recommend adding to the bakeoff: Cerebras gpt-oss-120b (low and medium effort), Groq gpt-oss-20b (low), Gemma 4 31B (cheap OpenRouter route, ZDR-only), and Mistral Small 4 if a host is found.

### Gaps
- No creative-writing, instruction-following (IFEval-style) or hallucination/faithfulness leaderboard numbers were retrieved for gpt-oss, Gemma 4 or Mistral Small 4.
