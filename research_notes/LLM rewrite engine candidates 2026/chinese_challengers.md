# Chinese challenger LLMs for the RetAIn rewrite engine (as of 2026-09-26)


Cost formula used throughout: per piece = 10,227 x in/1M + 1,594 x out/1M. Incumbent gemini-3.1-flash-lite ($0.25/$1.50) = $0.00495/piece. Cost figures are my arithmetic on the cited list prices, without caching.

## 1. Xiaomi MiMo: which new model, and does it qualify?

### Takeaway
The new release is the **MiMo-V2.6 series**, announced 2026-09-21/22: V2.6-Pro, V2.6-Flash and V2.6-Pro-UltraSpeed, with Pro and Flash under the MIT licence. **MiMo-V2.6-Flash** ($0.14/$0.28) comes to about **$0.00188/piece (38% of the incumbent)**, and thinking can be switched off. Pro ($0.00584) and UltraSpeed are over the cap.

### Cited Findings
- The series was released 2026-09-22 per Xiaomi's changelog (V2.6-Pro, V2.6-Flash, V2.6-Pro-UltraSpeed). The changelog calls Flash a "Full-modality, high-intelligence, low-cost reasoning model" — [Xiaomi MiMo docs](https://mimo.mi.com/docs/en-US/updates/model); [SiliconANGLE](https://siliconangle.com/2026/09/22/xiaomi-introduces-mimo-v2-6-series-open-source-ai-model-family/)
- VentureBeat gives the Flash release date as 2026-09-21. It lists official API pricing of $0.14 in / $0.28 out / $0.0028 cached input per 1M, and says the model is aimed at "high-frequency calls and large-scale tasks" — [VentureBeat](https://venturebeat.com/technology/better-than-deepseek-xiaomis-mimo-v2-6-pro-debuts-as-the-top-open-weights-model-in-the-world-alongside-cheaper-v2-6-flash)
- OpenRouter prices: Pro $0.435/$0.87 (cache $0.0036). Flash $0.14/$0.28 (cache $0.0028). Pro-UltraSpeed $4.35/$8.70, marketed as "up to 20 times Pro's output speed". The models are served by the Xiaomi API, OpenRouter, DeepInfra (Pro and Flash) and OpenCode — [WinBuzzer](https://winbuzzer.com/2026/09/24/xiaomi-mimo-v2-6-downloadable-ai-low-cost-apis-a004-xcxwbn/)
- The model ID on OpenRouter is `xiaomi/mimo-v2.6-flash` — [OpenRouter](https://openrouter.ai/xiaomi/mimo-v2.6-flash). It is also listed on the Vercel AI Gateway — [Vercel](https://vercel.com/ai-gateway/models/mimo-v2.6-flash)
- Flash has 309B total / 15B active parameters (MoE, meaning only part of the network runs per token), a 1M context, the MIT licence and open weights. The published weights repo is `XiaomiMiMo/MiMo-V2.6-Flash-RL` — [Hugging Face](https://huggingface.co/XiaomiMiMo/MiMo-V2.6-Flash-RL)
- **Thinking toggle, first-party API:** send `extra_body={"thinking": {"type": "disabled"}}` — search-result summary of Xiaomi/aggregator docs ([mimo.mi.com model page](https://mimo.mi.com/models/en-US/mimo-v2.6-flash)). Not verified on the page itself.
- **Thinking toggle, self-hosted:** thinking is ON by default in the chat template and is switched off with `enable_thinking: false` (vLLM/MLX/exllama `chat_template_kwargs`) — [vLLM recipe](https://recipes.vllm.ai/XiaomiMiMo/MiMo-V2.6-Flash-RL); [HF community quant](https://huggingface.co/mlx-community/MiMo-V2.6-Flash-RL-mxfp4-q8)
- **Speed:** Artificial Analysis lists a "MiMo-V2.6-Flash (Non-reasoning)" variant, with Xiaomi's API the fastest provider at **146.3 tokens/s** — search snippet of [Artificial Analysis](https://artificialanalysis.ai/models/mimo-v2-6-pro/providers). No time-to-first-token (TTFT) figure was found.
- Pro scored 46 on the AA Intelligence Index, the highest open-weights score — [Unite.AI](https://www.unite.ai/xiaomis-new-flagship-model-leads-open-weight-rankings-with-a-score-of-46/). Flash trails Pro on Terminal Bench (28.8 vs 34.9) — [WinBuzzer](https://winbuzzer.com/2026/09/24/xiaomi-mimo-v2-6-downloadable-ai-low-cost-apis-a004-xcxwbn/)
- **Free period:** OpenCode made Flash free for one week from its announcement on 2026-09-21, so it ends around 2026-09-28. Rate limits and data-training terms were not stated — [WinBuzzer](https://winbuzzer.com/2026/09/24/xiaomi-mimo-v2-6-downloadable-ai-low-cost-apis-a004-xcxwbn/)
- The model card's benchmarks are all agentic or coding (DeepSWE, Toolathlon, OSWorld, CyberGym). It reports **no writing, IFEval/IFBench, hallucination or creative-writing scores** — [Hugging Face](https://huggingface.co/XiaomiMiMo/MiMo-V2.6-Flash-RL)

### Inferences
- MiMo-V2.6-Flash is the strongest "new and cheap" candidate: $0.00188/piece, with thinking that can be disabled and weights we could self-host. With caching on the shared system prompt the cost would be lower still.
- Output at about 146 t/s non-reasoning makes a 700-token rewrite take roughly 5 s, plus TTFT.
- Nothing published supports English idiomatic quality. Only our own bake-off can settle it.

### Gaps
- Could not load Xiaomi's official pricing page or its data-privacy / training-use terms. **Unverified.**
- No TTFT figure, and no Vectara, EQ-Bench or LMArena creative-writing entry was found for V2.6-Flash.
- DeepInfra's Flash price was not retrieved.

## 2. Other lesser-known labs (Meituan, StepFun, Ant inclusionAI, Baidu, iFlytek, others)

### Takeaway
Under the cap with thinking that can be switched off: **Ant Ling-3.0-flash** (about $0.0003–0.0011/piece, open weights, hybrid thinking that can be disabled), **Meituan LongCat-Flash-Lite** (about $0.0017, non-thinking, but older than 3 months) and **StepFun step-3.5-flash** (about $0.0015, but thinking may not be disableable). Over the cap: StepFun Step 5 Preview, Meituan LongCat 2.0 (by a hair), Baidu ERNIE 5.1 and Tencent Hy4-preview.

### Cited Findings
**Ant Group / inclusionAI Ling-3.0-flash**
- Released 2026-07-23 (llm-releases), though Artificial Analysis gives 2026-08-04. It has 124B total / 5.1B active parameters and a 262K context — [LLM Releases](https://www.llm-releases.com/); [Artificial Analysis](https://artificialanalysis.ai/models/ling-3-0-flash)
- It is a "native hybrid reasoning model". Thinking is on by default and "can be disabled per request with `chat_template_kwargs: {enable_thinking: false}`" — HF model card via search snippet, [inclusionAI/Ling-3.0-flash](https://huggingface.co/inclusionAI/Ling-3.0-flash)
- Prices conflict across sources:
  - OpenRouter: $0.021/$0.063 → **$0.00032/piece**
  - AnotherWrapper / LLM Gateway: $0.06/$0.18 → $0.00090
  - AA (inclusionAI API): $0.07/$0.22, 80% cache discount → $0.00107
  
  Sources: [search summary of OpenRouter](https://openrouter.ai/inclusionai/ling-3.0-flash); [LLM Gateway](https://llmgateway.io/models/ling-3.0-flash); [Artificial Analysis](https://artificialanalysis.ai/models/ling-3-0-flash)
- AA figures: Intelligence Index 25 (#1 of 65 in its class), **362.8 output t/s**, **2.65 s TTFT** (measured in reasoning mode), 2 API providers — [Artificial Analysis](https://artificialanalysis.ai/models/ling-3-0-flash)
- Spin-offs:
  - Ling-3.0-flash-VL (Sep 10), with a `:free` variant on OpenRouter — [OpenRouter](https://openrouter.ai/inclusionai/ling-3.0-flash-vl:free)
  - -Fin (Aug 27) and -Sante (Sep 4), plus Ling-3.0-tiny (Aug 6, MIT) — [LLM Releases](https://www.llm-releases.com/)
- Predecessor Ling-2.6-flash (2026-04-21, instant/non-thinking, 104B/7.4B): $0.01/$0.03 → $0.00015/piece, with a `:free` variant on OpenRouter — [OpenRouter](https://openrouter.ai/inclusionai/ling-2.6-flash:free); [pricepertoken](https://pricepertoken.com/pricing-page/model/inclusionai-ling-2.6-flash)

**Meituan LongCat**
- LongCat 2.0 (released 2026-07-20): $0.30/$1.20 → **$0.00498/piece**, just over the $0.00495 cap — [search summary of OpenRouter](https://openrouter.ai/meituan/longcat-2.0); [Crypto Briefing](https://cryptobriefing.com/meituan-longcat-2-undercuts-gpt-claude-pricing/)
- LongCat-Flash-Lite is a **non-thinking** 68.5B MoE at $0.10 in / $0.40 out → **$0.00166/piece**, with about 500 t/s claimed and a 256K context — [search summaries: pricepertoken / llm-stats](https://llm-stats.com/models/longcat-flash-lite); [AIbase](https://news.aibase.com/news/25351)
- LongCat Flash Chat (released 2025-09) is listed at $0/$0 on one aggregator — [pricepertoken](https://pricepertoken.com/pricing-page/model/meituan-longcat-flash-chat). Unverified and probably a promotional or stale entry.

**StepFun** (official pricing page)
- step-5-preview (paid API from 2026-09-20; open weights promised for Oct 15; 600B/27B): $1.00/$2.70 → $0.0145. **Over the cap.** — [StepFun pricing](https://platform.stepfun.ai/docs/en/guides/pricing/details); [MarkTechPost](https://www.marktechpost.com/2026/09/20/stepfun-launches-step-5-preview/)
- step-3.7-flash (198B MoE, multimodal): $0.20/$1.15 → $0.00388. Reasoning only comes as `reasoning_effort` low/medium/high, **with no off switch**. StepFun notes that "output tokens include the reasoning process" — [StepFun pricing](https://platform.stepfun.ai/docs/en/guides/pricing/details); [Baseten](https://www.baseten.co/blog/introducing-step-37-flash-multimodal-reasoning/)
- step-3.5-flash / step-3.5-flash-2603: $0.10/$0.30 → $0.00150. It is classed as a "reasoning model", and an HF discussion thread asks how to disable or reduce its reasoning — [StepFun pricing](https://platform.stepfun.ai/docs/en/guides/pricing/details); [HF discussion](https://huggingface.co/stepfun-ai/Step-3.5-Flash/discussions/22)

**Baidu ERNIE**
- ERNIE 5.1 (2026-05-08) is hosted-only; the 5.x weights have never been published. It costs $0.59/$2.65 → $0.0103. **Over the cap.** — [search summary: codersera/apidog](https://codersera.com/blog/baidu-ernie-5-1-launch-2026/); [The Decoder](https://the-decoder.com/baidus-ernie-5-1-cuts-94-percent-of-pre-training-costs-while-competing-with-top-models/)

**Tencent (newer than Hy3)**
- Hy4-preview (2026-08-28, 770B/49B, Apache-2.0): $0.834/$2.501, cache $0.042 → $0.0125. **Over the cap.** It was free only for two weeks on WorkBuddy/CodeBuddy at its August launch — [OpenRouter](https://openrouter.ai/tencent/hy4-preview); [Tencent](https://www.tencent.com/tencent-releases-and-open-sources-tencent-hy4-preview/)
- Hy-MT2-30B-A3B (Aug 20) is a translation specialist — [LLM Releases](https://www.llm-releases.com/)

**Alibaba (a model cheaper than qwen3.8-flash)**
- Qwen3.7-Flash (commercial API listing 2026-07-27, multimodal, 1M context): **$0.03/$0.13 for prompts under 32K** → **$0.00051/piece**. It is cheaper than qwen3.8-flash ($0.15/$0.47 → $0.00228) — [eesel](https://www.eesel.ai/blog/qwen-3-7-flash); [LLM Releases](https://www.llm-releases.com/). Price not verified on Alibaba's own page; thinking toggle not checked.

**iFlytek, Shanghai AI Lab, others**
- iFlytek: Spark X2.5 cloud flagship MoE (293B), announced 2026-09-07, **CNY pricing only**. Full launch is due at 1024 Developer Day in October — [LLM Releases](https://www.llm-releases.com/); [OrcaRouter](https://www.orcarouter.ai/blog/spark3-leak)
- Shanghai AI Lab: "Atria Dawn Preview" (2026-09-11, 744B MoE, MIT, 256K) — [LLM Releases](https://www.llm-releases.com/). No price was found.
- Other new Chinese releases, all from [LLM Releases](https://www.llm-releases.com/) and none with a price found:
  - Nex AGI Nex-N2.5 family (Sep 8, open weights)
  - RedNote Dots3-Note (Aug 14, 280B/16B)
  - OpenBMB MiniCPM5-2B (Sep 7, a small edge model)
  - Moonshot Kimi K2.8 Preview (Sep 11)
- Zhipu GLM-5.2 Turbo ($1.99/$6.16) is over the cap. The DeepSeek V4-Flash-0731 snapshot ($0.14/$0.28) was **retired on Sep 10** — [LLM Releases](https://www.llm-releases.com/)
- For reference, DeepSeek V4.1-Flash at $0.30/$1.20 also works out to $0.00498/piece, marginally over the cap (same arithmetic as LongCat 2.0).

### Inferences
- A candidate shortlist for a bake-off, cheapest first:
  1. Ling-3.0-flash with thinking off
  2. Qwen3.7-Flash
  3. LongCat-Flash-Lite
  4. MiMo-V2.6-Flash with thinking off
  
  All are 2.6x to 30x cheaper than the incumbent. Only MiMo-V2.6-Flash and Ling-3.0-flash are both new (last 3 months) and have a documented off-switch.
- Ling's AA speed and TTFT were measured in reasoning mode. Non-thinking TTFT should be lower but has not been measured.
- Step 3.7 Flash fails the "thinking must be switchable off" rule. Step 3.5 Flash probably does too (unverified).
- Very-low-active-parameter models (Ling 5.1B, LongCat-Lite) carry the highest risk on idiomatic English. None has published writing-quality evidence.

### Gaps
- **English writing quality:** no Vectara hallucination, EQ-Bench creative, LMArena creative-writing or IFBench scores were found for any of these models. This is the biggest gap.
- **Data-privacy / training-use terms** for the first-party APIs (Xiaomi, inclusionAI, Meituan, StepFun) were not retrieved.
- **OpenRouter free-tier terms:** the rate limits and training terms of the `:free` variants (Ling-2.6-flash, Ling-3.0-flash-VL) were not retrieved. OpenRouter model pages returned only API boilerplate, so their provider and throughput tables could not be read.
- **Pricing not checked:** Baichuan, 01.AI Yi, Kuaishou KAT/Kwai, JD and SenseTime returned no releases in this window in my searches. That is absence of evidence, not confirmation.
- **Release dates and hosts:** LongCat-Flash-Lite's release date was not confirmed (likely early 2026, outside the 3-month window). Prices on Western hosts (DeepInfra, Together, Fireworks, Novita, SiliconFlow, Chutes) were not collected per model.
