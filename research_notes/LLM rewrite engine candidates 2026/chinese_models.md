# Chinese LLMs as rewrite-engine candidates (as of 2026-09-26)

>
> Cost formula used throughout: 2,500 input + 1,200 output tokens = 0.0025 x (input $/1M) + 0.0012 x (output $/1M).
> These costs assume thinking is OFF. Any hidden reasoning tokens are billed as output and add to the cost. Incumbent gemini-3.1-flash-lite ≈ $0.0017 per call.
> Release dates marked "(OR)" are OpenRouter listing dates (the `created` field in its API). They are close to, but not necessarily the same as, the lab's release date.

## 1. Per-lab fast/cheap models: IDs, official prices, per-call cost

### Takeaway
Several Chinese "flash" models now cost about half of gemini-3.1-flash-lite or less per rewrite, if thinking is turned off: qwen3.8-flash (~$0.0009), GLM-5.3-Flash (~$0.001), deepseek-flash (V4.1-Flash, $0.0011 off-peak / $0.0022 peak), and Tencent Hy3 (~$0.0006). Kimi's current line (K3 $3/$15, K2.6 $0.95/$4) is 4–15x more expensive than the incumbent. It is not a cheap-tier option.

### Cited Findings
**Alibaba Qwen (Model Studio, official)**
- Singapore (intl) prices per 1M tokens: qwen3.8-flash $0.15 in / $0.47 out, flat pricing, 1M-token free quota. qwen3.7-flash (0–32K tier) $0.03 / $0.13. qwen-flash (0–256K) $0.05 / $0.40. qwen3.7-plus (0–256K) $0.40 / $1.60. qwen3.8-max $2 / $6 — [Alibaba Model Studio pricing](https://www.alibabacloud.com/help/en/model-studio/model-pricing)
- US (Virginia) prices are lower: qwen3.8-flash $0.113 / $0.382. qwen3.7-flash (0–32K) $0.028 / $0.110. qwen-flash (0–128K) $0.022 / $0.216. qwen3.7-plus $0.276 / $1.101 — [Alibaba Model Studio pricing](https://www.alibabacloud.com/help/en/model-studio/model-pricing)
- Per-call cost: qwen3.8-flash SG $0.00094 / US $0.00074. qwen3.7-flash SG $0.00023. qwen-flash SG $0.00061. qwen3.7-plus SG $0.0029. qwen3.8-max $0.0122 (computed).
- OpenRouter listing dates: qwen3.8-flash 2026-08-26, qwen3.7-flash 2026-07-27, qwen3.8-max-0902 2026-09-03, qwen3.8-27b 2026-08-14 (open-weight size; licence not verified) — [OpenRouter models API](https://openrouter.ai/api/v1/models)
- OpenRouter describes qwen3.8-flash as a "multimodal reasoning model". Alibaba is the only provider for qwen3.8-flash and qwen3.7-flash, so those two are closed-weight in practice — [OpenRouter endpoints](https://openrouter.ai/api/v1/models/qwen/qwen3.8-flash/endpoints)

**DeepSeek (api.deepseek.com, official)**
- The current IDs are `deepseek-flash` (maps to DeepSeek-V4.1-Flash; 1M context; 384K max output) and `deepseek-v4-pro` (V4-Pro-0813). The pricing page no longer lists the older `deepseek-chat` / `deepseek-reasoner` IDs — [DeepSeek pricing](https://api-docs.deepseek.com/quick_start/pricing)
- deepseek-flash: input (cache miss) $0.15 off-peak / $0.30 peak. Output $0.60 off-peak / $1.20 peak. deepseek-v4-pro: $0.66 / $1.32 in and $1.98 / $3.96 out. Peak hours are 01:00–04:00 and 06:00–10:00 UTC on weekdays, and off-peak is half the peak rate — [DeepSeek pricing](https://api-docs.deepseek.com/quick_start/pricing)
- Per-call cost: deepseek-flash $0.0011 off-peak / $0.0022 peak. v4-pro $0.0040 off-peak / $0.0081 peak (computed).
- V4.1-Flash is open-weight under the MIT licence (commercial use allowed) and was released in September 2026 — [Artificial Analysis comparison](https://artificialanalysis.ai/models/comparisons/deepseek-v4-1-flash-vs-glm-5-3-flash). It uses a new "Causal Encoder-Decoder" MoE with 8B active parameters on input and 16B on output — [OpenRouter endpoints](https://openrouter.ai/api/v1/models/deepseek/deepseek-v4.1-flash/endpoints). Technical report: [arXiv 2609.19969](https://arxiv.org/pdf/2609.19969)
- The earlier V4-Flash-0731 has 284B total / 13B active parameters — [OpenRouter endpoints](https://openrouter.ai/api/v1/models/deepseek/deepseek-v4-flash-0731/endpoints)

**Zhipu / Z.ai GLM (official)**
- GLM-5.3-Flash $0.15 in / $0.03 cached / $0.50 out. GLM-5.3-FlashX $0.37 / $0.075 / $1.25. GLM-5.3 $1.40 / $0.26 / $4.40. GLM-4.7-Flash and GLM-4.5-Flash are free — [Z.ai pricing](https://docs.z.ai/guides/overview/pricing)
- Per-call cost: GLM-5.3-Flash $0.00098. FlashX $0.0024. GLM-5.3 $0.0088 (computed).
- GLM-5.3-Flash is open-weight under MIT and was released in August 2026 — [Artificial Analysis comparison](https://artificialanalysis.ai/models/comparisons/deepseek-v4-1-flash-vs-glm-5-3-flash). OpenRouter listing dates: GLM-5.3 2026-08-18, GLM-5.3-Flash 2026-08-26, FlashX 2026-09-18 — [OpenRouter models API](https://openrouter.ai/api/v1/models)
- Z.ai markets FlashX as the high-speed tier ("up to 200 tokens/s") — [OpenRouter endpoints](https://openrouter.ai/api/v1/models/z-ai/glm-5.3-flashx/endpoints)
- Price conflict: OpenRouter lists `z-ai/glm-5.3` at $0.38 / $1.19, while Z.ai's own page says $1.40 / $4.40 — [OpenRouter models API](https://openrouter.ai/api/v1/models) vs [Z.ai pricing](https://docs.z.ai/guides/overview/pricing). The cause is unresolved.

**Moonshot Kimi (platform.kimi.ai; the old platform.moonshot.ai now redirects there)**
- kimi-k3: $3.00 in ($0.30 cache hit) / $15.00 out. kimi-k2.6: $0.95 / $4.00. kimi-k2.7-code: $0.95 / $4.00. kimi-k2.7-code-highspeed: $1.90 / $8.00. The pricing page shows no non-thinking or turbo text variant — [Kimi pricing](https://platform.kimi.ai/docs/pricing/chat)
- Per-call cost: K3 $0.0255 before any reasoning tokens. K2.6 $0.0072 (computed).
- K3 is described as a 2.8T-parameter open-weight multimodal reasoning model, listed 2026-07-16 — [OpenRouter endpoints](https://openrouter.ai/api/v1/models/moonshotai/kimi-k3/endpoints)

**MiniMax** (the official intl pricing page was not fetched; this is MiniMax's own endpoint price as shown on OpenRouter)
- minimax-m3: MiniMax's endpoint charges $0.30 / $1.20. It has 1M context, is multimodal, and was listed 2026-05-31 → per call $0.0022 — [OpenRouter endpoints](https://openrouter.ai/api/v1/models/minimax/minimax-m3/endpoints)

**ByteDance Seed** (the official BytePlus ModelArk pricing page was not fetched; this is the "Seed" first-party endpoint on OpenRouter)
- seed-2.0-mini: $0.10 / $0.40 → $0.00073 per call. It is aimed at "latency-sensitive, high-concurrency, cost-sensitive" work and has 4 reasoning-effort modes (minimal/low/medium/high). Listed 2026-02-26 — [OpenRouter endpoints](https://openrouter.ai/api/v1/models/bytedance-seed/seed-2.0-mini/endpoints)
- seed-2-1-turbo: $0.50 / $2.50 → $0.0043 per call. Listed 2026-08-12. Only the Seed first-party endpoint serves it — [OpenRouter endpoints](https://openrouter.ai/api/v1/models/bytedance-seed/seed-2-1-turbo/endpoints)

**Others**
- StepFun step-3.7-flash: 196B MoE with ~11B active parameters. StepFun's own endpoint charges $0.20 / $1.15 → $0.0019 per call. Listed 2026-05-28 — [OpenRouter endpoints](https://openrouter.ai/api/v1/models/stepfun/step-3.7-flash/endpoints)
- Tencent `hy3`: 295B MoE with 21B active parameters and configurable reasoning effort. Tencent's endpoint charges $0.083 / $0.33 → $0.0006 per call. Listed 2026-07-06. `hy4-preview` costs $0.834 / $2.50 (listed 2026-08-27) — [OpenRouter endpoints](https://openrouter.ai/api/v1/models/tencent/hy3/endpoints)
- Meituan longcat-2.0: 1.6T total / 48B active parameters. $0.30 / $1.20 → $0.0022 per call — [OpenRouter endpoints](https://openrouter.ai/api/v1/models/meituan/longcat-2.0/endpoints)
- Baidu ERNIE: no ERNIE model appeared in OpenRouter's 2026 listings, and I did not fetch Baidu's pricing. Baidu does appear as a *host* for DeepSeek V4-Flash-0731 — [OpenRouter endpoints](https://openrouter.ai/api/v1/models/deepseek/deepseek-v4-flash-0731/endpoints)

### Inferences
- If thinking can be disabled, qwen3.8-flash, GLM-5.3-Flash and deepseek-flash (off-peak) each cost about 55–65% of the incumbent per call. qwen3.7-flash and Hy3 cost about 15–35%.
- deepseek-flash's peak-hour price ($0.0022) is higher than the incumbent's. Whether peak or off-peak applies depends on when users read, which is unpredictable for worldwide users.
- Kimi does not fit the cost envelope at any current tier. This matches the July K2.5 rejection.

### Gaps
- Official intl pricing pages for MiniMax and BytePlus ModelArk (Seed), and Baidu ERNIE and Tencent Hunyuan intl pricing, were not fetched. Prices above for those labs come from their first-party endpoints on OpenRouter.
- Open-weight licences were verified only for DeepSeek V4.1-Flash and GLM-5.3-Flash (MIT, per Artificial Analysis). Licences for Qwen3.8-27B, Kimi K3, MiniMax M3, Step 3.7 and Hy3 were not checked.
- Exact lab release dates are unverified. The dates above are OpenRouter listing dates.

## 2. Can thinking be turned off?

### Takeaway
Thinking can be disabled on Qwen and DeepSeek through documented API parameters. On both it is **on by default**, so the call must set it explicitly. Seed-2.0-mini has a "minimal" effort mode and Tencent Hy3 has configurable reasoning effort. I could not confirm a thinking toggle for GLM-5.3-Flash, and Kimi's pricing page documents no non-thinking variant.

### Cited Findings
- qwen3.8-flash, qwen3.7-flash, qwen3.7-plus and qwen3.8-max are hybrid-thinking models with **thinking enabled by default**. Setting `enable_thinking=false` makes the model "respond directly". `thinking_budget` (1–32,768 tokens) caps reasoning. qwen-flash (older Qwen3 line) has thinking off by default — [Alibaba deep-thinking docs](https://www.alibabacloud.com/help/en/model-studio/deep-thinking)
- DeepSeek: thinking is controlled by `{"thinking": {"type": "enabled" | "disabled"}}`, and "thinking mode is enabled by default, with the default effort being `high`" — [DeepSeek thinking-mode guide](https://api-docs.deepseek.com/guides/thinking_mode). Both deepseek-flash and deepseek-v4-pro support thinking and non-thinking modes — [DeepSeek pricing](https://api-docs.deepseek.com/quick_start/pricing)
- Seed-2.0-mini offers four reasoning-effort modes, including "minimal" — [OpenRouter endpoints](https://openrouter.ai/api/v1/models/bytedance-seed/seed-2.0-mini/endpoints)
- Tencent Hy3 "supports a configurable reasoning effort" — [OpenRouter endpoints](https://openrouter.ai/api/v1/models/tencent/hy3/endpoints)
- Z.ai's pricing page says nothing about a thinking toggle — [Z.ai pricing](https://docs.z.ai/guides/overview/pricing). Kimi's pricing page lists no non-thinking variant — [Kimi pricing](https://platform.kimi.ai/docs/pricing/chat)
- OpenRouter marks nearly every 2026 Chinese model as supporting the `reasoning` parameter. The exceptions are Tencent's small hy-mt2 translation models and minimax-m2-her — [OpenRouter models API](https://openrouter.ai/api/v1/models)

### Inferences
- Because Qwen and DeepSeek default to thinking ON, a bakeoff that omits the flag will reproduce the Kimi K2.5 failure (long latency, hidden output tokens). The harness must set `enable_thinking=false` / `thinking.type=disabled` explicitly.
- Through OpenRouter, the unified `reasoning` parameter (e.g. effort/enabled) is probably the portable switch. Whether each upstream provider honours "off" was not verified.

### Gaps
- GLM-5.3-Flash thinking toggle: I did not fetch Z.ai's API reference. Earlier GLM releases used a `thinking: {type: enabled/disabled}` parameter, but that is from memory and unverified for 5.3.
- Kimi K3 / K2.6: I found no documentation on disabling thinking.
- MiniMax M3 and Step 3.7 Flash reasoning controls were not checked.

## 3. Latency / throughput (Artificial Analysis)

### Takeaway
DeepSeek V4.1 Flash is fast: 237 tokens/s and 0.99s time to first token (TTFT), even measured at max-effort reasoning. GLM-5.3-Flash is slow at 46 tokens/s and 3.4s TTFT, so a 1,200-token rewrite would take about 25–30s on the Z.ai path, far worse than the incumbent's ~3s. I got no Artificial Analysis non-reasoning numbers for Qwen3.8-Flash.

### Cited Findings
- Artificial Analysis: DeepSeek V4.1 Flash (Reasoning, Max Effort) runs at 237 tok/s, 0.99s TTFT, 11.5s end-to-end for 500 tokens, Intelligence Index 39. GLM 5.3 Flash runs at 46 tok/s, 3.37s TTFT, 58s end-to-end for 500 tokens, Intelligence Index 42 — [AA comparison](https://artificialanalysis.ai/models/comparisons/deepseek-v4-1-flash-vs-glm-5-3-flash)
- Another AA page shows GLM 5.3 Flash at 88.0 tok/s and Qwen3.8 27B (low) at 52.6 tok/s. That conflicts with the 46 tok/s figure; the measurements likely differ by snapshot or provider — [AA comparison](https://artificialanalysis.ai/models/comparisons/glm-5-3-flash-vs-qwen3-8-27b-low)
- Z.ai says GLM-5.3-FlashX reaches "up to 200 tokens/s" (vendor claim) — [OpenRouter endpoints](https://openrouter.ai/api/v1/models/z-ai/glm-5.3-flashx/endpoints)
- The AA models overview says Gemini 2.5 Flash-Lite (non-reasoning) has the lowest latency (0.30s) — [Artificial Analysis models](https://artificialanalysis.ai/models)

### Inferences
- If DeepSeek V4.1 Flash with thinking disabled keeps ~230 tok/s, a 1,200-token output would take about 5–6s end to end. That is plausibly close to the incumbent's ~3s, but unverified.
- GLM-5.3-Flash through Z.ai is too slow for interactive use unless a Western host serves it faster (many do; see §5). FlashX costs 2.5x more.

### Gaps
- AA non-reasoning measurements for Qwen3.8-Flash, Seed-2.0-mini, Hy3, Step-3.7-Flash, MiniMax M3 and Gemini 3.1 Flash-Lite were not retrieved. The AA leaderboard page did not render its table for the fetch tool.
- OpenRouter's per-provider latency and throughput fields came back null in the API response.

## 4. English writing quality / instruction following / hallucination

### Takeaway
I did not retrieve current benchmark data (EQ-Bench Creative Writing v3, IFEval, Vectara HHEM) for these September 2026 models. Quality has to be established by RetAIn's own bakeoff (`src/bakeoff.py`), which is the more relevant test anyway: idiomatic word placement plus the fact judge.

### Cited Findings
- On the AA Intelligence Index, GLM 5.3 Flash scores 42 and DeepSeek V4.1 Flash (max-effort reasoning) scores 39. This measures reasoning-heavy general intelligence, not prose quality — [AA comparison](https://artificialanalysis.ai/models/comparisons/deepseek-v4-1-flash-vs-glm-5-3-flash)
- The EQ-Bench creative-writing page loaded without its data table — [EQ-Bench](https://eqbench.com/creative_writing.html)
- Third-party comparison posts exist (Yotta Labs, regolo.ai: DeepSeek V4 Flash vs Qwen3.8-Flash-Next vs GLM-5.3-Flash) but were not read. They are secondary sources — [Yotta Labs](https://www.yottalabs.ai/post/deepseek-v4-flash-vs-glm-5-3-flash-vs-qwen-flash-next-2026), [regolo.ai](https://regolo.ai/deepseek-v4-flash-vs-qwen3-8-flash-next-vs-glm-5-3-flash-the-real-leader-in-quality-to-price-in-2026/)

### Inferences
- Intelligence Index scores come from reasoning mode. Non-thinking quality for the rewrite task could be materially lower, which is what model-bakeoff.md's "deliberation dose-response" finding would predict.

### Gaps
- EQ-Bench, IFEval and Vectara hallucination scores for all candidates remain unretrieved. The pages are JS-rendered or were not fetched.
- The "Qwen3.8-Flash-Next" name appears in third-party posts but not on Alibaba's pricing page. Its relation to `qwen3.8-flash` is unclear.

## 5. Western-host availability and prices (avoid sending data to China)

### Takeaway
The open-weight models (DeepSeek V4.1-Flash / V4-Flash-0731, GLM-5.3-Flash, MiniMax M3, Step 3.7 Flash, Hy3, Qwen3.6-35B-A3B) are widely served by US/EU hosts: Together, Fireworks, DeepInfra, BaseTen, Parasail, CoreWeave, Modal and others. Several are cheaper than the labs' own APIs. Qwen3.8-Flash and Seed are closed-weight, served only by Alibaba and ByteDance.

### Cited Findings (OpenRouter provider prices, $/1M in/out, 2026-09-26)
- DeepSeek V4.1 Flash: DeepInfra (fp8) $0.14 / $0.42 → $0.00085 per call. Fireworks $0.22 / $0.66. Together, BaseTen, Modal, Parasail and DigitalOcean $0.30 / $1.20 → $0.0022. The DeepSeek first-party endpoint is $0.15 / $0.60 — [OpenRouter endpoints](https://openrouter.ai/api/v1/models/deepseek/deepseek-v4.1-flash/endpoints)
- DeepSeek V4-Flash-0731: DeepInfra $0.06 / $0.18 → $0.00037 per call. Together, Nebius, Parasail and Cohere $0.14 / $0.28 → $0.00069. BaseTen and CoreWeave $0.13 / $0.26–0.28 — [OpenRouter endpoints](https://openrouter.ai/api/v1/models/deepseek/deepseek-v4-flash-0731/endpoints)
- GLM-5.3-Flash: DeepInfra (fp4) $0.075 / $0.25 → $0.00049 per call. Together, Fireworks, BaseTen, CoreWeave, Modal and Parasail $0.15 / $0.50 → $0.00098. Cloudflare $0.30 / $1.00 — [OpenRouter endpoints](https://openrouter.ai/api/v1/models/z-ai/glm-5.3-flash/endpoints)
- MiniMax M3: Together and Parasail $0.30 / $1.20. CoreWeave (fp4) $0.23 / $0.96. SambaNova $0.60 / $2.40 — [OpenRouter endpoints](https://openrouter.ai/api/v1/models/minimax/minimax-m3/endpoints)
- Step 3.7 Flash: DeepInfra (US) $0.16 / $0.92 — [OpenRouter endpoints](https://openrouter.ai/api/v1/models/stepfun/step-3.7-flash/endpoints)
- Tencent Hy3: DeepInfra (fp4) $0.13 / $0.53 — [OpenRouter endpoints](https://openrouter.ai/api/v1/models/tencent/hy3/endpoints)
- Qwen3.6-35B-A3B (open-weight, 3B active): DeepInfra $0.10 / $0.95. Parasail $0.15 / $1.00 — [OpenRouter endpoints](https://openrouter.ai/api/v1/models/qwen/qwen3.6-35b-a3b/endpoints)
- qwen3.8-flash and qwen3.7-flash: Alibaba is the only provider. Seed-2.0-mini and Seed-2.1-turbo: Seed is the only provider — [OpenRouter endpoints](https://openrouter.ai/api/v1/models/qwen/qwen3.8-flash/endpoints)

### Inferences
- The lowest-risk path to a Chinese model is an open-weight model on a US host: GLM-5.3-Flash or DeepSeek V4.1-Flash on Together, Fireworks or DeepInfra, at the same or lower price than the labs' own APIs. Many cheap endpoints are fp4/fp8 quantized, and quantization can degrade prose quality. Pin the provider and precision in any bakeoff.
- For Qwen, Alibaba's US (Virginia) region is the non-China option (see §6), but the vendor is still a PRC-headquartered company.

### Gaps
- Groq and Cerebras did not appear as providers for these models on OpenRouter. I did not check their own catalogues.
- Throughput per Western host was not available (null in the OpenRouter API).

## 6. Data privacy and legal concerns

### Takeaway
DeepSeek's first-party API is the highest-risk route: data is stored in the PRC, its terms are governed by PRC law, and its consumer privacy policy allows training (with opt-out). Alibaba Model Studio offers non-China regions (Singapore, US-Virginia, Frankfurt, Tokyo) and says it never trains on customer data. US restrictions found so far target government devices, not consumer apps. Self-hosted or Western-hosted open weights sidestep PRC data transfer entirely.

### Cited Findings
- DeepSeek privacy policy: "we directly collect, process and store your Personal Data in People's Republic of China". Data may be used "to train and improve our technology, such as our machine learning models", with a right to opt out. The policy states that processing for end users of developer apps built on the open platform "are not covered by this privacy policy" — [DeepSeek privacy policy](https://cdn.deepseek.com/policies/en-US/deepseek-privacy-policy.html)
- DeepSeek Open Platform terms are "governed by the laws of the People's Republic of China", with disputes heard in courts where DeepSeek is registered. Users keep rights in their inputs and are assigned rights in outputs. The terms do not state a data location or a training opt-out for API data — [DeepSeek Open Platform ToS](https://cdn.deepseek.com/policies/en-US/deepseek-open-platform-terms-of-service.html)
- Alibaba Model Studio "will never use your data for model training". It stores "data generated from model and application calls" in compliance with law, holds a SOC 2 report, and runs in Beijing, US (Virginia), Singapore, Tokyo, Frankfurt and Hong Kong. Stated in search-result snippets of the official privacy notice and FAQ; the page itself was not fetched — [Alibaba privacy notice](https://www.alibabacloud.com/help/en/model-studio/privacy-notice), [Alibaba FAQ](https://www.alibabacloud.com/help/doc-detail/2587658.html)
- US: Virginia, Texas and New York ban DeepSeek on state government devices. The federal "No DeepSeek on Government Devices Act" was introduced 2025-02-07 — [GovTech](https://www.govtech.com/biz/data/wheres-deepseek-banned-the-states-blocking-chinese-made-ai), [FedScoop](https://fedscoop.com/deepseek-ban-government-devices-house-bill/), [NBC News](https://www.nbcnews.com/tech/new-york-state-bans-deepseek-government-devices-rcna191510)
- As of May 2026, one secondary source found no nationwide US consumer ban on DeepSeek (low-reliability, fan-style site) — [chat-deep.ai](https://chat-deep.ai/privacy-security/is-deepseek-banned-in-us/)

### Inferences
- Sending users' reading text to api.deepseek.com means PRC storage, and PRC law can compel data access. RetAIn's own privacy policy would need to disclose that cross-border transfer. That transfer is a GDPR Chapter V problem for EU users, because China has no EU adequacy decision. (Inference from general GDPR knowledge; not researched here.)
- App Store: I found no evidence of an Apple rule barring apps that call Chinese LLM APIs. Apple's privacy nutrition label and third-party-AI disclosure would still need to name the processor. (Unverified; not researched.)

### Gaps
- Z.ai, Moonshot/Kimi, MiniMax intl, BytePlus (Seed) and Tencent privacy terms (processing location, retention, training use) were not fetched.
- I did not research EU (Italy's Garante, 2025) or South Korea actions against DeepSeek for 2026 status. They are known from earlier coverage but unverified here.
- I found no source on whether 2026 US federal rules (e.g. Commerce ICTS rules on Chinese AI) apply to commercial apps using Chinese model APIs.
