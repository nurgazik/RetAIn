# RetAIn backlog

*The living work list. Four epics — Tech Debt, Monetization, UX, Administration — with
the founder's pending decisions on top and a done ledger at the end. Ids are stable
(DEC-n, TD-n, MO-n, UX-n, AD-n). Each item: value / trade-off / implementation, priority
order within its epic. Product decisions are logged in PRD.md (D1–D39); the PoC 2 record
and spike findings live in docs/poc2-transform.md; session narrative in PROGRESS.md.*

Epics: **Tech Debt**, **Monetization**, **UX** (speed, reading, sharing, in-app
experience), **Administration** (accounts, money, entities, App Store, licences).
Items are priority-ordered within each epic; ids are stable for reference. Each carries
value / trade-off / implementation. Product decisions the founder still owes are listed
first because several items hang on them. The done ledger and Horizon 3 sit at the end.

## Decisions pending (founder)

| # | Decision | Blocks |
|---|---|---|
| DEC-1 | ~~**Engine density.**~~ Decided 2026-09-26 → **D40**: no ~120-word stretch without a word (trial anchor, replaced per-paragraph); tiers SUBSTITUTE / REPHRASE / SUPPLEMENT (≤50% trial), all in one model call; checker kept as is (relaxing it is a future founder lever). | UX-1, TD-2 |
| DEC-2 | **Monetization model (P2):** credits per transform / bring-your-own key / subscription with fair-use cap. Inputs: $0.0016–0.010 per transform, spend visible in Settings. | MO-1..MO-4 |
| DEC-3 | **TestFlight thresholds (P3):** What is confidered a user forming a habbit? DAU?. | AD-6 verdict |
| DEC-4 | **Seller entity before public launch (D39):** individual now, consulting corp later (D-U-N-S, domain email, website). Decided with DEC-2. | AD-7 |

## Epic: Tech Debt

| # | Item | Value | Trade-off | Implementation |
|---|---|---|---|---|
| TD-1 | **Move the service off the Mac mini** (Fly.io, ~$5/mo, founder-approved) with nightly DB backups | Other people can depend on it; survives home-network and Mac outages | Small monthly cost; one deploy pipeline to own | Dockerfile for `src/service`, Fly volume for SQLite, Litestream or cron copy to object storage, secrets via `fly secrets`; switch `RETAIN_SERVER`; keep the Mac as fallback until cutover |
| TD-2 | **Latency: retry policy + input cap** (6–14 s today; model time ≈ 100%) | Faster sheet; fewer wasted calls (a piece can burn 7 calls and place 0) | Fewer rounds = lower density; a cap = partial pieces on long pages | **Partly done (D41, 2026-09-26): sentence mode no longer regenerates on a judge rejection — 5/5 fixtures at 1 draft + 1 check, avg 2.8 s.** Remaining: make retries depend on DEC-1; cap input at ~1,500 words with a "first part" note; measure via `calls.ms` |
| TD-3 | **Remove the dev-token path from device builds** before anyone else installs | No shared secret in an app binary | None once Sign in with Apple works everywhere | Delete `RETAIN_DEV_TOKEN` from Info.plist generation; keep it for the simulator only; rotate the token |
| TD-4 | **Offline and error states** (My Reads needs the network; failures show raw messages) | The app never looks broken | Some UI work | Serve My Reads from the app-group cache first; friendly error copy; retry buttons |
| TD-5 | **Rate limiting and abuse protection** beyond the per-user daily cap | Protects the model bill when strangers arrive | None | Per-IP and per-user limits in the service; alert on daily spend threshold |
| TD-6 | **Page extraction quality** (readability-style) | Fewer navigation/ad fragments in pieces on messy sites | A day of JS work; risk of dropping real text | Score candidate containers by text density in `RetAInPage.js`; use `textContent` for collapsed sections; test on 10 sites |
| TD-7 | **Repo hygiene:** ~~purge `service.db` from history~~ (founder 2026-09-26: leave history as is); `output/` artefacts; spike folder archived | Privacy; smaller repo | — | Move `spikes/` to a branch or `archive/` |
| TD-8 | **Retire the digest server + Shortcut** (`src/serve.py`, launchd `com.retain.server`, port 8484) | One system to run | None; PoC 1 artefacts stay in git | Unload the launchd agent; note in PROGRESS; delete the Shortcut on the phone |
| TD-9 | **Source-text retention policy** (every piece stores its full original forever) | Privacy; storage | Some analytics lose the source | Keep source text N days, then keep only the piece; document in the privacy policy (AD-2) |
| TD-10 | **Native text renderer** replacing WKWebView | Faster open, native selection, less memory (~15–20 MB), proper Dynamic Type | Rebuild highlights, popup and underline natively | AttributedString from the piece HTML; SwiftUI Text with tap targets; keep WKWebView behind a flag until parity |
| TD-11 | **Service observability:** structured logs, error alerting, daily cost/latency summary | See problems before users report them | Small | Log to file with rotation; a daily summary script or Fly log drain; alert on failed pieces > N/day |
| TD-12 | ~~**Replace the model fallback**~~ Done 2026-09-26 → D42: fallback is gemini-3.1-flash-lite (Google direct), Haiku removed | — | — | — |
| TD-13 | **Model evals: finish the loop** (harness built 2026-09-26: `src/evals`, golden set of 30, blind grading in Claude Code, writer/checker role tests) | Any new model gets a cheap × fast × quality verdict | Grading uses the founder's plan (helper agents) | Founder blind-labels ~150 words (`src/evals label`) to check Claude's grading; blind-grade the Gemma + gpt-6-luna checker run (34) vs production; decide whether to split writer and checker (D42 caveat) |
| TD-14 | **LLM tracing with Langfuse** (open source; cloud Hobby free: 50k units/mo, 30-day retention; Core $29/mo: 100k units, 90 days; +$8 per 100k — pricing checked 2026-09-27) | Per-transform traces in a dashboard (each call's input/output, cost, latency, per user); prompt versions; evals on production traffic; datasets to re-test prompt/model changes — replaces reading `calls.response` by hand once more than the founder uses the app | Users' reading text leaves our server and is kept 30 days–3 years (we chose zero-retention model hosts, D42) → privacy-policy line and founder call; self-hosting is free but needs Postgres + ClickHouse + Redis + blob storage | Around TestFlight (AD-6). Python SDK / OpenAI-client wrapper at `call_model` in `src/generate.py`; one trace per piece, one generation per call. Check field masking before sending source text. Complements TD-11, ties to TD-9 retention. Interim: raw output in `calls.response` + `prompt_sha` (2026-09-27) |

## Epic: Monetization

| # | Item | Value | Trade-off | Implementation |
|---|---|---|---|---|
| MO-1 | **Decide the model (DEC-2)** using real numbers: per-transform cost by length, spend per user/day | Everything below | — | One-page memo from the `calls` table: cost distribution, worst-case heavy reader, break-even per plan |
| MO-2 | **Entitlements in the service** (free tier limits, paid tier, per-user caps by plan) | The app can enforce a plan | Design once, before StoreKit | `plans` table + `users.plan`; cap logic reads the plan; admin script to set plans for testers |
| MO-3 | **StoreKit 2 purchase flow** (subscription or credits per DEC-2) + receipt validation server-side | Revenue | Apple review requirements; sandbox testing | StoreKit 2 in the app; App Store Server API notifications to the service; restore purchases; paywall screen |
| MO-4 | **Bring-your-own-key option** (if DEC-2 includes it) | Power users pay Google directly; zero marginal cost | Key handling on device; support burden | Key stored in keychain; service accepts a per-request key header; never logged |
| MO-5 | **Cost controls:** per-plan daily caps, spend alerts, kill switch | No surprise bills | — | Extends TD-5; Settings shows remaining allowance |

## Epic: UX (speed, reading, sharing, in-app experience)

| # | Item | Value | Trade-off | Implementation |
|---|---|---|---|---|
| UX-1 | **Engine density per DEC-1** | The core reading experience: how many words land, how faithful the text | Density vs fidelity; latency | D40 engine + reader **done and live 2026-09-26** (tier tagging, tap-to-reveal original, notes in one call, ~120-word stretches, tier colours + bracket bars + tap hints). Measured: 15 fixture pieces → 1.5 words/piece, 58% stretches covered; founder's first real share (CBC wastewater, ~1,000 words) → 2 words (model attempted 6 across ~8 stretches, checker rejected 4, the one note died with its word). **Open:** (a) model under-attempts and misuses words → test stronger models via TD-13 on surviving words per article; (b) stretch length (120 vs ~60) is a founder call — shorter = more words, mostly notes; (c) note quality is generic, occasional trend claim |
| UX-2 | **Faster transforms** (user-facing half of TD-2) | The magic moment stays under ~6 s | See TD-2 | Phase labels already stream; add a "reading the first part now" partial for long pages if a cap is adopted |
| UX-3 | **First-run experience** (a new account has zero words → nothing gets placed) | New users see the product work in minute one | Starter words must fit the reader's level | Onboarding: pick a level → starter set (e.g. 20 words); import from a list/Kindle export later; "add your first word" prompt |
| UX-4 | **Word card enrichment** (PRD §8: register, collocations, nuance, 2–3 examples) | Capture becomes "better than a Kindle lookup" | One extra model call per capture (~$0.0001) | Extend the `card` prompt; store JSON fields on `words`; card view sections |
| UX-5 | **Sharing routes: every app's own Share button works** (founder 2026-09-27: nobody selects text to share) — one source at a time | Sharing is one tap from anywhere, or nobody uses it | Per-source terms (Reddit, X ruled out server-side by D37) | **Step 1 built 2026-09-27:** link-only shares (Chrome, other apps) read on the phone via hidden web view + Safari page script (`PageFetcher`); open pages only, device test pending. **Next:** Reddit Share button, Facebook, X (each needs research + a decision); confirm Kindle / Apple News payloads |
| UX-6 | **My Reads polish:** search, filters (by word), swipe to delete, source link, extension pieces appear instantly | Reading history becomes useful | — | Server: delete endpoint + query params; app: list UI; app-group cache write from the extension (needs App Groups on device — now available) |
| UX-7 | **In-reader lookup & capture** (tap any unknown word → define → add) | Closes the loop inside reading (Horizon 3 item promoted) | Popup complexity | Long-press on any word → `POST /v1/words`; reuse the card call |
| UX-8 | **Word list quality-of-life:** sort by servings/age, bulk retire, notes | Managing 50–200 words stays pleasant | — | Sort controls; multi-select; optional note field |
| UX-9 | **Reader typography controls** (size, serif/sans, line height) — *partial 2026-09-27: New York serif + follows iOS Dynamic Type; in-app picker still open* | Reading comfort; accessibility | Trivial with a native renderer (TD-10) | Settings → reader prefs → CSS variables or native fonts |
| UX-10 | **App icon, launch screen, empty states** | The app looks like a product | Design time | Icon set; launch storyboard; empty-state copy for Words / My Reads |
| UX-11 | **Clean, structured text in** (was: "one big blob", metadata looks like body text) | Words land in prose, not in page junk; paragraphs survive | — | **Partly done 2026-09-26:** Safari shares run Mozilla Readability 0.6.0 (clutter out, headline → title, byline/site/date as fields); `sentence_guard` no longer collapses a piece into one paragraph. **Open:** photo captions still pass (CBC); text shared from other apps is uncleaned (no DOM); byline/site/date captured but not shown — a proper header in the reader. **Done 2026-09-27 (D44):** header shows dek + "byline · site · date"; datelines, hidden notes and header lines no longer reach the body (verified on device) |
| UX-12 |: Onboarding expeirence: we can't let the user start without any words. At least needs to have 20.
| UX-13 | **Margin bar shape per the founder's Figma** (nodes 5265-7722 / 5267-7723 / 5267-7724) | Reader matches the design | One-line bars render as a short stub (shape is stretched to bar height) | **Done 2026-09-26:** each tier's Figma path is a CSS mask on `.bar::before` in `PieceHTML.swift` (filled "D", flat left, curved right; widths 10/13/12 px); note colour orange → yellow (`#FFCE1F`); light mode = Figma hues darkened for cream: `#28a012` / `#0097a7` / `#d4a200` (assistant's pick at founder's request) |


## Epic: Administration

| # | Item | Value | Trade-off | Implementation |
|---|---|---|---|---|
| AD-1 | **App Store Connect app record** (bundle id `com.retain.app`, name, category, age rating) | Prerequisite for TestFlight | — | Create in App Store Connect under team UKGU6PX43H; register the two extension ids |
| AD-2 | **Privacy policy page + support email** (required for Sign in with Apple and review) | Compliance | Needs a public URL: a GitHub Pages page is enough | Write the policy (what is stored: words, pieces incl. source text per TD-9, Apple id, email; model providers = OpenRouter zero-retention hosts (Gemma, D42) + Google (fallback)); publish; add URL to App Store Connect and the app's Settings |
| AD-3 | **Account deletion in-app** (App Store rule for apps with sign-in) + export | Compliance; trust | Build work in app + service | `DELETE /v1/me` cascading; Settings → Delete account with confirmation; optional export of words/pieces as JSON |
| AD-4 | **App privacy "nutrition label" + privacy manifest** (data types collected, tracking = none) | Required at submission | — | Fill in App Store Connect; add `PrivacyInfo.xcprivacy` to the targets (required reason APIs) |
| AD-5 | **Model-provider terms check** for user content sent to Gemini (retention, training opt-out on the paid tier) | Honest privacy policy; no surprises | — | Read Google's Gemini API terms for paid usage; record in docs/content-sources.md or a new docs/privacy.md |
| AD-6 | **TestFlight:** archive + upload, internal testers, then ~5 external readers for 2 weeks (M9) | The real habit test | External testers need App Review of the build | Xcode Archive → App Store Connect; TestFlight groups; feedback form; measure DEC-3 |
| AD-7 | **Paid Apps Agreement, tax and banking** (for MO-3) and the seller-entity call (DEC-4) | Ability to charge | Individual vs corp (D39) | Agreements in App Store Connect; W-8/Canadian tax forms; bank details |
| AD-8 | **Domain + email** (e.g. retain.app or similar) for support, privacy page, and a later corp enrollment | Professional surface; needed for D-U-N-S path | Small yearly cost | Buy domain; forwarders for support@; host the privacy page there |
| AD-9 | **Licences and attributions** in-app (open-source notices; content-source attributions from PoC 1 if any surface again) | Compliance | — | Settings → Acknowledgements |

## Done ledger (2026-09-24 → 26)

M1 transform service (FastAPI + SQLite, Sign in with Apple, SSE phases, cost + latency
telemetry, daily cap, diagnostics, pytest suite) · M2 iOS app (Words, My Reads, paste +
clipboard offer, Settings with spend, Sign in with Apple, shared session) · M3 share-sheet
sheet · M4 Safari page action · M5 single-word capture · M6 clipboard intake · Sentence-
scoped engine mode with mechanical guard + underline · Popup stats + "Got it" · Dark mode ·
Foreground refresh · Tailscale Funnel HTTPS · Paid Apple Developer membership (D39) ·
Device verification of all of the above on the founder's iPhone · D43 notes allowed in stretches that already carry a word (2026-09-27) · D41 revert-on-reject (sentence mode) · D40 three tiers in one call (substitute / rephrase / note) with ~120-word stretches · Reader: tier colours, bracket margin bars, tap hints, tap-to-reveal original, founder's dark palette · Safari clutter removal (Readability) · Demo piece `p_demo_283d0c28f2` in the founder's account.

