# Western closed-model APIs: small/fast/cheap rewrite-engine candidates (as of 2026-09-26)


Cost basis for every "per call" figure: 2,500 input + 1,200 output tokens at standard (non-batch)
list price, excluding any hidden reasoning tokens unless stated. Arithmetic is mine from cited prices.

## Google Gemini (Flash / Flash-Lite, thinking controls)

### Takeaway
Two newer options exist beyond gemini-3.1-flash-lite: gemini-3.5-flash-lite (July 21, 2026; $0.30/$2.50, clearly better on benchmarks, but thinking cannot be fully disabled, only set to "minimal") and three newer Flash models (3.6/3.7/3.8) that all bill thinking in output and cannot turn it off. For a no-thinking, cheapest-per-call rewrite, 3.1 Flash-Lite remains the Google baseline; 3.5 Flash-Lite is the upgrade to test.

### Cited Findings
- Current Flash-Lite IDs/prices (per 1M in/out, output "includes thinking tokens"): `gemini-3.5-flash-lite` $0.30/$2.50; `gemini-3.1-flash-lite` $0.25/$1.50; `gemini-2.5-flash-lite` $0.10/$0.40. Batch, Flex and Priority tiers are offered for all. — [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing)
- Current Flash IDs/prices: `gemini-3.8-flash`, `gemini-3.7-flash`, `gemini-3.6-flash` all $0.75 in / $3.75 out through Dec 31, 2026, input rising to $1.50 on Jan 1, 2027; `gemini-3.5-flash` $1.50/$9.00. Batch is 50% off. — [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing)
- Status: all of the above are listed as Stable; 3.8 Flash is "New" and described as "our most intelligent Flash model"; 3.7 and 3.6 are called "previous-generation". The models page gives no deprecation dates for 3.1 Flash-Lite. — [Gemini models](https://ai.google.dev/gemini-api/docs/models)
- Thinking controls, per the docs' table: 3.8/3.7 Flash default "On (medium)", levels low/medium/high, cannot be disabled; 3.6 Flash default medium, levels minimal–high, cannot be disabled; 3.5 Flash-Lite default "On (minimal)", levels minimal/low/medium/high, cannot be disabled; 2.5 Flash-Lite default Off and is the only model listed that can be disabled. The fetched page did not mention thinkingBudget for 3.x models and did not list 3.1 Flash-Lite. — [Gemini thinking docs](https://ai.google.dev/gemini-api/docs/thinking)
- 3.5 Flash-Lite launch: released July 21, 2026, alongside 3.6 Flash; Google says it has "significantly better quality than 3.1 Flash-Lite" (for example Terminal-Bench 2.1 at 54% vs 31%) and "runs at 350 output tokens/s" per Artificial Analysis. — [Google blog](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-6-flash-3-5-flash-lite-3-5-flash-cyber/)
- Artificial Analysis (AA) on 3.5 Flash-Lite: Intelligence Index 22; 348.6 output tok/s (#5 of 174); time to first token 9.51 s ("at the higher end" for reasoning models, which suggests the benchmark ran with thinking); used 59M output tokens across the index vs a median of 85M. — [AA: Gemini 3.5 Flash-Lite](https://artificialanalysis.ai/models/gemini-3-5-flash-lite)
- Sources disagree on the 3.5 Flash-Lite default: one search snippet said "defaults to medium thinking effort", while the official thinking docs say default "On (minimal)". — [Gemini thinking docs](https://ai.google.dev/gemini-api/docs/thinking) vs search snippet from [myclaw.ai](https://myclaw.ai/blog/gemini-3-5-flash-lite-vs-flash) (secondary source)

Per-call costs (my arithmetic, excluding thinking):
- gemini-3.1-flash-lite: $0.00243. The project's ~$0.0017 figure fits a ~600-word piece, which uses fewer tokens.
- gemini-3.5-flash-lite: $0.00375, plus minimal-level thinking tokens billed at $2.50/M.
- gemini-3.6/3.7/3.8-flash: $0.00638 now ($0.00825 from Jan 2027), plus thinking at medium by default or minimal (3.6 only) or low as the lowest setting.
- gemini-2.5-flash-lite: $0.00073, with thinking off.

### Inferences
- The July problem with 3.6 Flash (hidden thinking despite thinkingBudget 0) matches the docs: 3.6+ Flash cannot disable thinking. The same will apply to 3.7 and 3.8 Flash, so none of the Flash line is a like-for-like replacement.
- 3.5 Flash-Lite at "minimal" is the Google candidate worth a bakeoff run. Before judging cost, measure its thinking-token count per call (usageMetadata.thoughtsTokenCount). AA's 9.5 s TTFT is a warning for the ~3 s latency target, although that figure was likely measured at a higher thinking level (inferred).

### Gaps
- The docs do not say whether 3.1 Flash-Lite thinks by default or what its thinking controls are, because it was absent from the fetched thinking table. The project's own July measurement of no hidden thinking tokens is the best evidence.
- No deprecation or shutdown date was found for 3.1 Flash-Lite.
- AA metrics for 3.1 Flash-Lite could not be fetched (the AA URL returned 404).

## OpenAI (small models, reasoning_effort, tiers)

### Takeaway
The notable new entrant is **gpt-6-luna** (released Sept 22, 2026): $0.10/$0.50 per 1M tokens, reasoning_effort supports `none`, and AA measures 0.87 s time to first token in non-reasoning mode. At about $0.00085 per call it is roughly a third of 3.1 Flash-Lite's cost, but its non-reasoning intelligence score (18) is low and no writing-quality evidence exists yet, so it needs a bakeoff. gpt-5.4-mini and gpt-5.4-nano are also listed on the pricing page.

### Cited Findings
- `gpt-6-luna`: "Our most efficient model for focused, high-volume tasks"; $0.10 input / $0.01 cached / $0.50 output; Batch and Flex are 50% of standard; "Fast mode" costs 2x; regional processing adds 10%. reasoning_effort values are `none`, `low`, `medium` (default), `high`, `xhigh`, `max`. Context 1.05M, max output 128K, knowledge cutoff May 18, 2026. "Chat Completions supports function calling only with reasoning_effort set to none." — [OpenAI model page: gpt-6-luna](https://developers.openai.com/api/docs/models/gpt-6-luna)
- The rest of the GPT-6 lineup: `gpt-6-sol` $2/$10 with reasoning none–max; `gpt-6-astra` $10/$50. — [OpenAI models](https://developers.openai.com/api/docs/models)
- GPT-6 Luna per AA: released Sept 22, 2026, in six effort variants. Intelligence Index runs from 18 (non-reasoning) to 37 (max). Non-reasoning has the lowest time to first answer token at 0.87 s; the max variant outputs 146 tok/s. Cost per task runs from $0.0045 (low) to $0.07 (max). — [AA: GPT-6 Luna release](https://artificialanalysis.ai/models/releases/gpt-6-luna)
- AA says GPT-6 Luna (max) cut its hallucination rate from 93% to 77% vs GPT-5.6 Luna and raised its AA-Omniscience Index from -10 to 1. AA calls the release a cost-efficiency move rather than an intelligence leap. — [AA article](https://artificialanalysis.ai/articles/gpt-6-sol-and-luna-push-the-cost-efficiency-frontier)
- Pricing page, small models (standard in/out; batch and flex are half): `gpt-5.4-mini` $0.75/$4.50; `gpt-5.4-nano` $0.20/$1.25; `gpt-5-mini` $0.25/$2.00; `gpt-5-nano` $0.05/$0.40; `gpt-4.1-mini` $0.40/$1.60; `gpt-4.1-nano` $0.10/$0.40; `gpt-4o-mini` $0.15/$0.60 (no flex); `o4-mini` $1.10/$4.40. A "Fast mode" at 2x standard also exists. — [OpenAI pricing](https://developers.openai.com/api/docs/pricing)
- The pricing page also lists gpt-5.6-sol/terra/luna, gpt-5.5, gpt-5.4 and others as flagship models. The models overview page does not list gpt-5.4-mini/nano. — [OpenAI pricing](https://developers.openai.com/api/docs/pricing); [OpenAI models](https://developers.openai.com/api/docs/models)

Per-call costs (my arithmetic, excluding reasoning tokens):
- gpt-6-luna at `none`: $0.00085; $0.00043 on flex or batch.
- gpt-5.4-nano: $0.0020.
- gpt-5.4-mini: $0.0073.
- gpt-4.1-nano: $0.00073.
- gpt-4.1-mini: $0.0029.
- gpt-5-nano: $0.0006, plus mandatory reasoning.

### Inferences
- gpt-6-luna with `reasoning_effort: none` is the strongest new challenger on cost and latency. It is the only new model from any provider with zeroable reasoning at below-incumbent price.
- Flex tier halves the price but trades away latency and availability. It suits the judge calls better than the interactive rewrite (inferred; the SLA was not fetched).
- gpt-5-mini was rejected in July for word misuse, so treat the rest of the 5.x mini/nano line with the same suspicion until tested.

### Gaps
- No release dates or reasoning-effort options were fetched for gpt-5.4-mini/nano, and their absence from the models overview could mean they are being phased out (unverified).
- No output tok/s figure was found for non-reasoning Luna.
- No IFBench or writing-quality evidence was found for Luna.
- The exact priority-tier price was not captured.

## Anthropic (Haiku line, Sonnet)

### Takeaway
There is no Haiku newer than 4.5. The fallback **claude-haiku-4-5 has a retirement commitment of only "not sooner than October 15, 2026"**, about 3 weeks away, so the fallback choice needs revisiting. Sonnet 5 costs $2/$10, about $0.017 per call.

### Cited Findings
- Current lineup: Fable 5.1 ($10/$50), Opus 5.5 ($4/$20), Sonnet 5 (`claude-sonnet-5`, $2/$10, adaptive thinking, default effort high, retirement not sooner than June 30, 2027), and Haiku 4.5 (`claude-haiku-4-5-20251001`, alias `claude-haiku-4-5`, $1/$5, "Fastest", extended thinking which is optional and manual, effort not supported, 200K context, training cutoff Jul 2025). Haiku 4.5 retirement is "Not sooner than October 15, 2026". Batch is 50% off. — [Anthropic models overview](https://platform.claude.com/docs/en/docs/about-claude/models/overview)
- Sonnet 4.6 and 4.5 are "Legacy (still available)". — [Anthropic models overview](https://platform.claude.com/docs/en/docs/about-claude/models/overview)
- AA on Haiku 4.5 (non-reasoning): Intelligence Index 15, 80.9 output tok/s, 0.70 s time to first token. — [AA: Claude 4.5 Haiku](https://artificialanalysis.ai/models/claude-4-5-haiku)

Per-call costs (my arithmetic): Haiku 4.5 $0.0085; Sonnet 5 $0.017, plus adaptive thinking tokens.

### Inferences
- If Haiku 4.5 is retired after Oct 15, the fallback must move to Sonnet 5 (about 7x the incumbent's cost, possibly with mandatory adaptive thinking) or to another provider.

### Gaps
- Whether Sonnet 5's adaptive thinking can be zeroed was not verified. The docs say "Adaptive" without "(always on)", which suggests it is optional (inferred).
- No announced successor Haiku was found.

## xAI (Grok)

### Takeaway
The current xAI docs list no cheap "fast/mini" chat model comparable to Flash-Lite. The cheapest general option is grok-4.20-0309-non-reasoning (or grok-4.3) at $1.25/$2.50, about $0.0061 per call. xAI is not competitive on price.

### Cited Findings
- Models listed: grok-4.7/4.6/4.5 at $2/$6 (under 200K); grok-4.3 at $1.25/$2.50; `grok-4.20-0309-reasoning` and `grok-4.20-0309-non-reasoning` at $1.25/$2.50; `grok-build-0.1` ("mini", 256K context) at $1.00/$2.00. No deprecation notices are shown. — [xAI models](https://docs.x.ai/docs/models)

Per-call costs (my arithmetic): grok-4.20 non-reasoning $0.0061; grok-build-0.1 $0.0049.

### Gaps
- The earlier grok-4-fast / grok-4.1-fast models (from memory, unverified) do not appear on the fetched page, and their status is unknown.
- No latency or quality data was gathered for Grok.

## Mistral

### Takeaway
The current API models are Mistral Small 4 (`mistral-small-2603`, a hybrid instruct and reasoning model), Medium 3.5 (`mistral-medium-3504`), Large 3 (`mistral-large-2512`) and Ministral 3 (14B/8B/3B). Per-model prices could not be verified beyond the pricing page's example of "Mistral Large $0.5/$1.5".

### Cited Findings
- IDs and versions: Medium 3.5 v26.04 (`mistral-medium-3504`); Small 4 v26.03 (`mistral-small-2603`, "Hybrid model unifying instruct, reasoning, and coding", Apache 2.0); Large 3 v25.12 (`mistral-large-2512`, open-weight); Ministral 3 14B/8B/3B v25.12. Medium 3.1 and Small 3.2 are deprecated. — [Mistral models overview](https://docs.mistral.ai/getting-started/models/models_overview/)
- The pricing page example says "Mistral Large costs $0.5/M tokens for input and $1.5/M for output", with batch 50% off. It does not say which version, so this is likely Large 3 but unverified. — [Mistral pricing](https://mistral.ai/pricing)

Per-call cost (my arithmetic): Mistral Large at $0.5/$1.5 comes to $0.0031.

### Gaps
- Prices for Small 4, Medium 3.5 and Ministral were not found on official pages.
- Whether Small 4's reasoning can be switched off is unverified.
- No latency or quality data was gathered.

## Cohere (Command)

### Takeaway
The newest model is Command A+ (`command-a-plus-05-2026`, May 2026, MoE with reasoning), but Cohere's public pricing page lists per-token prices only for legacy models. Cohere is enterprise-oriented and a weak fit on verifiable price.

### Cited Findings
- Live models: `command-a-plus-05-2026` (May 2026, 128K context, 64K output, MoE, reasoning); `command-a-03-2025`; `command-r7b-12-2024`; `command-a-reasoning-08-2025`; `command-a-translate-08-2025`; `command-a-vision-07-2025`. Command R+, Command R, Command Light and Command were deprecated Sept 15, 2025. — [Cohere models](https://docs.cohere.com/docs/models)
- The pricing page lists legacy token prices only (for example Command R 03-2024 at $0.50/$1.50), with no price for Command A or A+. — [Cohere pricing](https://cohere.com/pricing)

### Gaps
- Official per-token prices for Command A and A+ were not found.
- Whether A+ reasoning can be turned off is unverified.
- No latency or quality data was gathered.
