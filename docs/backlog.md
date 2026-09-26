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
| DEC-1 | **Engine density.** Sentence mode is live at ~2.4 words/1,000 (about one per piece); rewrite mode gives 5.6 with occasional invented colour. Founder has an idea ("a creative task"). | UX-1, TD-2 |
| DEC-2 | **Monetization model (P2):** credits per transform / bring-your-own key / subscription with fair-use cap. Inputs: $0.0016–0.010 per transform, spend visible in Settings. | MO-1..MO-4 |
| DEC-3 | **TestFlight thresholds (P3):** transforms/user/week that count as a habit; day-14 self-quiz bar. | AD-6 verdict |
| DEC-4 | **Seller entity before public launch (D39):** individual now, consulting corp later (D-U-N-S, domain email, website). Decided with DEC-2. | AD-7 |
| DEC-5 | **Purge `data/service.db` from git history** (holds the founder's Apple id, email, and every transformed text; private repo) or leave it. | TD-7 |

## Epic: Tech Debt

| # | Item | Value | Trade-off | Implementation |
|---|---|---|---|---|
| TD-1 | **Move the service off the Mac mini** (Fly.io, ~$5/mo, founder-approved) with nightly DB backups | Other people can depend on it; survives home-network and Mac outages | Small monthly cost; one deploy pipeline to own | Dockerfile for `src/service`, Fly volume for SQLite, Litestream or cron copy to object storage, secrets via `fly secrets`; switch `RETAIN_SERVER`; keep the Mac as fallback until cutover |
| TD-2 | **Latency: retry policy + input cap** (6–14 s today; model time ≈ 100%) | Faster sheet; fewer wasted calls (a piece can burn 7 calls and place 0) | Fewer rounds = lower density; a cap = partial pieces on long pages | Skip the second generation round when nothing was rejected; make retries depend on DEC-1; cap input at ~1,500 words with a "first part" note; measure via `calls.ms` |
| TD-3 | **Remove the dev-token path from device builds** before anyone else installs | No shared secret in an app binary | None once Sign in with Apple works everywhere | Delete `RETAIN_DEV_TOKEN` from Info.plist generation; keep it for the simulator only; rotate the token |
| TD-4 | **Offline and error states** (My Reads needs the network; failures show raw messages) | The app never looks broken | Some UI work | Serve My Reads from the app-group cache first; friendly error copy; retry buttons |
| TD-5 | **Rate limiting and abuse protection** beyond the per-user daily cap | Protects the model bill when strangers arrive | None | Per-IP and per-user limits in the service; alert on daily spend threshold |
| TD-6 | **Page extraction quality** (readability-style) | Fewer navigation/ad fragments in pieces on messy sites | A day of JS work; risk of dropping real text | Score candidate containers by text density in `RetAInPage.js`; use `textContent` for collapsed sections; test on 10 sites |
| TD-7 | **Repo hygiene:** purge `service.db` from history (DEC-5); `output/` artefacts; spike folder archived | Privacy; smaller repo | History rewrite + force-push if purged | `git filter-repo` on `data/service.db`; move `spikes/` to a branch or `archive/` |
| TD-8 | **Retire the digest server + Shortcut** (`src/serve.py`, launchd `com.retain.server`, port 8484) | One system to run | None; PoC 1 artefacts stay in git | Unload the launchd agent; note in PROGRESS; delete the Shortcut on the phone |
| TD-9 | **Source-text retention policy** (every piece stores its full original forever) | Privacy; storage | Some analytics lose the source | Keep source text N days, then keep only the piece; document in the privacy policy (AD-2) |
| TD-10 | **Native text renderer** replacing WKWebView | Faster open, native selection, less memory (~15–20 MB), proper Dynamic Type | Rebuild highlights, popup and underline natively | AttributedString from the piece HTML; SwiftUI Text with tap targets; keep WKWebView behind a flag until parity |
| TD-11 | **Service observability:** structured logs, error alerting, daily cost/latency summary | See problems before users report them | Small | Log to file with rotation; a daily summary script or Fly log drain; alert on failed pieces > N/day |

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
| UX-1 | **Engine density per DEC-1** | The core reading experience: how many words land, how faithful the text | Density vs fidelity; latency | Implement the founder's idea as an engine mode behind `RETAIN_ENGINE_MODE`; measure on the 5 fixtures + device pieces; compare page |
| UX-2 | **Faster transforms** (user-facing half of TD-2) | The magic moment stays under ~6 s | See TD-2 | Phase labels already stream; add a "reading the first part now" partial for long pages if a cap is adopted |
| UX-3 | **First-run experience** (a new account has zero words → nothing gets placed) | New users see the product work in minute one | Starter words must fit the reader's level | Onboarding: pick a level → starter set (e.g. 20 words); import from a list/Kindle export later; "add your first word" prompt |
| UX-4 | **Word card enrichment** (PRD §8: register, collocations, nuance, 2–3 examples) | Capture becomes "better than a Kindle lookup" | One extra model call per capture (~$0.0001) | Extend the `card` prompt; store JSON fields on `words`; card view sections |
| UX-5 | **Sharing routes:** confirm X, Kindle, Apple News payloads; in-app guidance per app ("Reddit: copy text") | Fewer dead ends when sharing | — | Diagnostics table already records unusable shares; add per-app hints in the "nothing to read" message; log Kindle/News/X once |
| UX-6 | **My Reads polish:** search, filters (by word), swipe to delete, source link, extension pieces appear instantly | Reading history becomes useful | — | Server: delete endpoint + query params; app: list UI; app-group cache write from the extension (needs App Groups on device — now available) |
| UX-7 | **In-reader lookup & capture** (tap any unknown word → define → add) | Closes the loop inside reading (Horizon 3 item promoted) | Popup complexity | Long-press on any word → `POST /v1/words`; reuse the card call |
| UX-8 | **Word list quality-of-life:** sort by servings/age, bulk retire, notes | Managing 50–200 words stays pleasant | — | Sort controls; multi-select; optional note field |
| UX-9 | **Reader typography controls** (size, serif/sans, line height) | Reading comfort; accessibility | Trivial with a native renderer (TD-10) | Settings → reader prefs → CSS variables or native fonts |
| UX-10 | **App icon, launch screen, empty states** | The app looks like a product | Design time | Icon set; launch storyboard; empty-state copy for Words / My Reads |

## Epic: Administration

| # | Item | Value | Trade-off | Implementation |
|---|---|---|---|---|
| AD-1 | **App Store Connect app record** (bundle id `com.retain.app`, name, category, age rating) | Prerequisite for TestFlight | — | Create in App Store Connect under team UKGU6PX43H; register the two extension ids |
| AD-2 | **Privacy policy page + support email** (required for Sign in with Apple and review) | Compliance | Needs a public URL: a GitHub Pages page is enough | Write the policy (what is stored: words, pieces incl. source text per TD-9, Apple id, email; model provider = Google); publish; add URL to App Store Connect and the app's Settings |
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
Device verification of all of the above on the founder's iPhone.

