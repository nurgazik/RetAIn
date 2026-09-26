# Near-zero-cost LLM options for the RetAIn rewrite engine (as of 2026-09-26)


Cost formula used throughout: cost/piece = 10,227 x in/1M + 1,594 x out/1M. Incumbent gemini-3.1-flash-lite = $0.00495/piece.
OpenRouter prices come from a live pull of https://openrouter.ai/api/v1/models on 2026-09-26 (458 models; 21 free). OpenRouter's listed price is the cheapest route; the first-party price may differ.

## 1. Upstart/indie labs: model IDs, prices, cost per piece, speed, quality evidence

### Takeaway
Many non-big-brand models cost $0.0003-$0.0025 per piece, 2-15x under the incumbent. The strongest candidates are Inception **mercury-2.5** (diffusion model, released 2026-09-24, $0.00065/piece at an 80%-off launch price of unknown duration, $0.00324 at list price, ~843-1,107 tok/s) and **NVIDIA nemotron-3.5-lightning** ($0.00114/piece, ~296 tok/s, 0.58s time to first token, also free on OpenRouter). None of them has English-writing-quality evidence equivalent to our bakeoff. Quality must be tested with src/bakeoff.py.

### Cited Findings
Per-piece cost from the OpenRouter pull (in/out per 1M; cached-read per 1M where listed):

| Model ID (OpenRouter) | Released on OR | In / Out | Cached in | $/piece | Reasoning param |
|---|---|---|---|---|---|
| inception/mercury-2.5 | 2026-09-08 (OR); official launch 2026-09-24 | 0.04 / 0.15 (promo) | 0.004 | 0.00065 | yes |
| inception/mercury-2 | 2026-03-04 | 0.25 / 0.75 | 0.025 | 0.00375 | yes |
| nvidia/nemotron-3.5-lightning (30B, 3B active MoE; MoE = mixture-of-experts, where only part of the model runs per token) | 2026-08-11 | 0.08 / 0.20 | 0.04 | 0.00114 | yes |
| nvidia/nemotron-3-nano-30b-a3b | 2025-12-14 | 0.05 / 0.20 | 0.03 | 0.00083 | yes |
| nvidia/nemotron-3-super-120b-a12b | 2026-03-11 | 0.08 / 0.45 | — | 0.00154 | yes |
| upstage/solar-mini4 (35B, 3B active) | 2026-09-23 | 0.05 / 0.20 | 0.005 | 0.00083 | yes |
| upstage/solar-pro4 | 2026-08-10 | 0.09 / 0.36 | 0.018 | 0.00149 | yes |
| ibm-granite/granite-4.2-8b | 2026-08-31 | 0.06 / 0.25 | 0.015 | 0.00101 | yes |
| ibm-granite/granite-4.0-h-micro | 2025-10-19 | 0.017 / 0.112 | — | 0.00035 | no |
| google/gemma-4-26b-a4b-it | 2026-04-03 | 0.068 / 0.225 | 0.0375 | 0.00105 | yes |
| google/gemma-4-31b-it | 2026-04-02 | 0.09 / 0.34 | 0.05 | 0.00146 | yes |
| mistralai/mistral-small-2603 | 2026-03-16 | 0.15 / 0.60 | 0.015 | 0.00249 | yes |
| mistralai/ministral-8b-2512 | 2025-12-02 | 0.15 / 0.15 | 0.015 | 0.00177 | no |
| mistralai/ministral-3b-2512 | 2025-12-02 | 0.10 / 0.10 | 0.01 | 0.00118 | no |
| mistralai/ministral-14b-2512 | 2025-12-02 | 0.20 / 0.20 | 0.02 | 0.00236 | no |
| mistralai/mistral-nemo | 2024-07-18 | 0.019 / 0.03 | — | 0.00024 | no |
| cohere/command-r7b-12-2024 | 2024-12-13 | 0.037 / 0.15 | — | 0.00062 | no |
| cohere/command-a-plus | 2026-09-22 | 0.30 / 1.50 | 0.15 | 0.00546 (**over the incumbent's cost, so ruled out**) | yes |
| amazon/nova-micro-v1 | 2024-12-05 | 0.035 / 0.14 | — | 0.00058 | no |
| amazon/nova-lite-v1 | 2024-12-05 | 0.06 / 0.24 | — | 0.00100 | no |
| microsoft/phi-4 (16k context) | 2025-01-09 | 0.07 / 0.14 | — | 0.00094 | no |
| rekaai/reka-flash-3 | 2025-03-12 | 0.10 / 0.20 | — | 0.00134 | yes |
| rekaai/reka-edge (16k context) | 2026-03-20 | 0.10 / 0.10 | — | 0.00118 | no |
| arcee-ai/trinity-large-thinking | 2026-04-01 | 0.25 / 0.80 | 0.06 | 0.00383 | yes (thinking model) |
| poolside/laguna-xs-2.1 / laguna-s-2.1 (coding-focused) | 2026-07 | 0.06/0.12 ; 0.09/0.18 | 0.03 ; 0.009 | 0.00080 ; 0.00121 | yes |
| inclusionai/ling-3.0-flash (Ant Group, **Chinese; excluded by brief**) | 2026-07-23 | 0.021 / 0.063 | 0.0042 | 0.00032 | yes |
| meta/muse-spark-1.3-contributor (Meta, **big-brand; listed for reference only**) | 2026-09-02 | 0.10 / 0.20 | 0.002 | 0.00134 | yes |
Source for all rows: [OpenRouter models API](https://openrouter.ai/api/v1/models)

- Mercury 2.5: diffusion LLM (it generates and refines many tokens in parallel instead of one at a time). Released 2026-09-24. List price $0.20/$0.75. The launch price is 80% off at $0.04/$0.15, **with no end date stated**. It claims 1,107 tok/s, a 260K context, "tunable reasoning", 100M free tokens for testing, and a 40% intelligence gain over Mercury 2. — [Inception blog](https://www.inceptionlabs.ai/blog/introducing-mercury-2-5)
- Mercury 2.5's API model ID is `mercury-2.5`. Examples use `"reasoning_effort": "medium"`. The docs don't list the other values or say whether reasoning can be turned off completely. Cached input costs $0.004/1M at the promo price ($0.02 at list). — [Inception docs](https://docs.inceptionlabs.ai/get-started/models)
- Artificial Analysis measured Mercury 2.5 at 843 tok/s with a **3.08s time to first token (TTFT)** on Inception's API, and an Intelligence Index of 12 against a peer median of 13. — [Artificial Analysis](https://artificialanalysis.ai/models/mercury-2-5)
- Nemotron 3.5 Lightning: Intelligence Index 13 (peer median 8), 296.4 tok/s, 0.58s TTFT (median across providers). — [Artificial Analysis](https://artificialanalysis.ai/models/nemotron-3-5-lightning)
- Vectara hallucination leaderboard (updated 2026-09-22; lower is better), which measures hallucination rate when a model summarizes a document. That is the closest public proxy for "don't invent facts while rewriting". gemini-2.5-flash-lite 3.3%; Phi-4 3.7%; mistral-small-2501 5.1%; gemma-4-26b-a4b 5.2%; granite-4.0-h-small 5.2%; jamba-mini-2 5.3%; nova-micro 5.5%; nova-lite 6.1%; ministral-3b-2410 7.3%; gemma-4-31b 7.4%; ministral-8b-2410 7.4%; **gemini-3.1-flash-lite-preview (incumbent) 8.2%**; Nemotron-3-Nano-30B-A3B 9.6%; granite-3.3-8b 10.6%; **mercury-2 12.3%**; gpt-oss-120b 14.2%. — [Vectara leaderboard](https://github.com/vectara/hallucination-leaderboard)

### Inferences
- Mercury 2.5's speed comes from output throughput, not first-token latency. With ~700 output tokens, generation takes under 1s, but the 3.08s TTFT (probably measured with reasoning on) means the total rewrite time may not beat the incumbent's ~3.7s by much unless reasoning can be turned lower or off. Mercury 2 was the second-worst hallucinator in the list above, which is a warning for a fact-preserving rewrite. At list price ($0.00324) it is still cheaper than the incumbent, so it passes the founder's cost rule even after the promo ends.
- Nemotron 3.5 Lightning looks like the best-balanced upstart option: very fast first token, cheap, and a free OpenRouter variant exists.
- Several older models (nova-micro, command-r7b, mistral-nemo, phi-4) cost almost nothing and do well on Vectara, but they date from 2024 or early 2025. Their idiomatic writing quality at an advanced reading level is untested. Phi-4's 16k context fits our ~2.6k-token rewrite call.
- The Vectara figures for Ministral and Mistral Small are for older versions (2410/2501), not the 2512/2603 models priced above.

### Gaps
- No AI21 Jamba entry appeared in the OpenRouter list under $0.006/piece. Current Jamba pricing was not verified. Liquid LFM is only available as a free 2.6B model (see section 2). Allen AI OLMo and Nous Hermes did not appear under the cost cutoff, and their hosted prices were not checked.
- IFBench (an instruction-following benchmark) and LMArena creative-writing scores were not retrieved for any of these models.
- Whether Mercury 2.5 accepts reasoning_effort "none" or "instant": unverified.
- Tokens/sec and TTFT were retrieved only for Mercury 2.5 and Nemotron 3.5 Lightning.
- Data-use terms of first-party APIs (Inception, Upstage, IBM, NVIDIA paid): not checked.

## 2. Free tiers for a solo founder's MVP at low volume

### Takeaway
Free tiers are real but come with training or data caveats. The Gemini API free tier covers the incumbent model itself (gemini-3.1-flash-lite), plus 2.5-flash-lite and Gemma 4, but Google says free-tier content **is used to improve its products** (outside the EU/UK/EEA). OpenRouter `:free` allows 50 requests/day, or 1,000/day after buying $10 of credits. At 3-4 calls per piece, that is roughly 12 or 250 pieces/day. Mistral's free tier requires opting into training.

### Cited Findings
- Gemini API pricing lists a free tier for gemini-3.1-flash-lite, gemini-3.5-flash-lite, gemini-2.5-flash-lite, gemini-3.x-flash, gemini-2.5-flash/pro, and Gemma 4 (Gemma 4 is free only, with no paid tier on the Gemini API). For every free-tier model, the "used to improve our products" column says **Yes**. — [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing)
- Gemini's rate-limit page does not publish free-tier numbers; it points to AI Studio. — [Gemini rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)
- Secondary sources give Flash-Lite at about 15-30 RPM and 500-1,000 RPD. They conflict with each other, and one notes Google cut free quotas by 50-80% on 2025-12-07. — [aipromptshub](https://aipromptshub.co/blog/gemini-api-free-tier-rate-limits); [tokenmix](https://tokenmix.ai/blog/gemini-api-free-tier-limits) (**unverified; check AI Studio**)
- Google AI Studio free prompts may be used for training "unless you're in the EU, UK, or EEA". — [OpenRouter blog, 2026-06-15](https://openrouter.ai/blog/tutorials/free-llm-apis-compared/)
- OpenRouter `:free` models: 20 RPM; 50 requests/day, or 1,000/day once $10 or more of credits have been purchased. — [OpenRouter limits docs](https://openrouter.ai/docs/api/reference/limits)
- OpenRouter free models live on 2026-09-26: nvidia/nemotron-3.5-lightning:free, nvidia/nemotron-3-super-120b-a12b:free, nvidia/nemotron-3-ultra-550b-a55b:free, google/gemma-4-26b-a4b-it:free, google/gemma-4-31b-it:free, thinkingmachines/inkling:free and inkling-small:free (Thinking Machines Lab; 276B total/12B active MoE for small), liquid/lfm-2.5-2.6b:free, poolside/laguna-xs/s-2.1:free, cohere/north-mini-code:free, dots-studio/dots-3-note-preview:free, stealth/space-bunny-alpha (anonymous, released 2026-09-23), qwen/qwen3.8-27b:free and inclusionai ling variants (Chinese, excluded), and the router openrouter/free. — [OpenRouter models API](https://openrouter.ai/api/v1/models)
- Groq: 30 RPM / 6,000 TPM / 1,000 RPD on most models. Cerebras: about 1M tokens/day and 30 RPM, but it reportedly switched to a $5 card-required trial. Mistral Experiment tier: about 1B tokens/month but **requires opting into data training**. GitHub Models: 15 RPM, 150-1,000 RPD. NVIDIA NIM: about 1,000 RPD. Cloudflare Workers AI: about 10K neurons/day. — [ianlpaterson.com](https://ianlpaterson.com/blog/free-llm-api-2026/); [OpenRouter blog](https://openrouter.ai/blog/tutorials/free-llm-apis-compared/) (secondary; **unverified against official pages**)
- Mercury 2.5 comes with 100M free tokens for testing, which is about 8,500 pieces at our token mix. — [Inception blog](https://www.inceptionlabs.ai/blog/introducing-mercury-2-5)

### Inferences
- Groq's 6,000 TPM would cap us at about 0.6 pieces/minute (10.2k input tokens per piece). That works for the founder testing alone and nothing more.
- For an MVP where users' own reading passes through the model, the free tiers of Gemini, Mistral, and anonymous stealth models have a data-use problem: the provider may train on user text. Google's paid tier (the incumbent route) does not have this issue. A $10 OpenRouter top-up plus nemotron-3.5-lightning:free is the most practical near-zero route, pending a check of the provider's logging policy.
- Mercury's 100M free tokens could make its first ~8,500 pieces free.

### Gaps
- Official free-tier numbers for Gemini (AI Studio), Groq, Cerebras, GitHub Models, NVIDIA NIM, and Cloudflare were not verified on first-party pages.
- Logging and training policies of the providers behind each OpenRouter `:free` model were not retrieved (OpenRouter shows these per provider on the model page).

## 3. Cheapest paid routes: batch/flex and cached input

### Takeaway
Batch and flex are 50% off on Gemini, but batch is asynchronous, which doesn't fit a streamed reading flow. Flex may add latency; this was not checked. Caching matters more for our repeated system prompts. Among upstart models, cached-read prices run 10-50% of the base input price. Mercury 2.5's promo cached price ($0.004) is the lowest seen.

### Cited Findings
- Gemini: Batch and Flex are both 50% off. For example, gemini-3.1-flash-lite drops to about $0.125/$0.75, which is ~$0.0025/piece. Context caching costs $0.01/1M for 2.5-flash-lite, plus storage. gemini-3.5-flash-lite at $0.30/$2.50 comes to $0.00705/piece, **over the incumbent's cost, so ruled out**. — [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing)
- OpenRouter lists `:batch` variants: gpt-oss-20b:batch $0.024/$0.112, mistral-small-2603:batch $0.075/$0.30 ($0.00125/piece), ministral-8b-2512:batch $0.075/$0.075 ($0.00089). — [OpenRouter models API](https://openrouter.ai/api/v1/models)
- Cached-read prices are in the section 1 table (for example mercury-2.5 $0.004, solar-mini4 $0.005, mistral-small-2603 $0.015, granite-4.2-8b $0.015, nemotron-3.5-lightning $0.04).

### Inferences
- These illustrative figures assume 50% of input tokens are cacheable system prompt; the real share is unmeasured. Mercury 2.5 promo would go from $0.00065 to ~$0.00046/piece. Nemotron 3.5 Lightning would go from $0.00114 to ~$0.00093. Mistral-small-2603 would go from $0.00249 to ~$0.00180. At these prices, caching saves fractions of a tenth of a cent. Output tokens and model choice matter far more.
- Batch pricing only helps offline work such as re-scoring or evals, not the live streamed rewrite.

### Gaps
- Minimum cacheable prompt length and cache lifetime per provider (Gemini implicit caching, Inception, Mistral, NVIDIA) were not retrieved.
- Whether Gemini Flex adds latency or queuing: not checked.
