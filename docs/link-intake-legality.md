# Link intake — can RetAIn fetch a shared Reddit / X / web link? (G3)

*Researched 2026-09-24 by a background research agent; every claim cites a page fetched that
day (list at the end). Terms and technical assessment, not legal advice. Backlog item G3 in
docs/poc2-transform.md §8; founder ruling → PRD D37.*

## Headline

Neither Reddit nor X offers a free, terms-compliant way for a consumer iOS app to fetch a
shared post's text today. Reddit shut unauthenticated `.json` access in May 2026 and gates
its API behind manual approval that excludes monetised apps; X's free API tier is gone and
its unauthenticated embed endpoint truncates long posts and ignores threads. Both licences
allow modifying content "only to format it for display", which an LLM rewrite exceeds.
Generic web articles are fine through the in-Safari extension route the G1 spike already
uses. **Recommendation: share-selected-text is the MVP route for Reddit and X; the
in-Safari extension is the default for articles; a server-side fetch is at most a fallback
for URL-only shares from non-Safari apps.**

## Reddit

| Route | Works today? | Terms | Verdict |
|---|---|---|---|
| `.json` on a post URL, unauthenticated | **No.** Probed 2026-09-24 from a residential IP with three user agents: HTTP 403; `old.reddit.com` redirects to login; `robots.txt` is `Disallow: /`. Official: r/modnews 2026-05-28 "Deprecating unauthenticated JSON access". | User Agreement (eff. 2026-07-01): "scraping the Services without Reddit's prior written consent is prohibited." | Ruled out |
| OAuth Data API, free tier | Exists on paper (100 QPM) but self-service app creation is closed; Responsible Builder Policy (2026-06-05): "You must request access and get explicit approval before accessing any Reddit data." r/redditdev threads this summer: people stuck in the approval loop. Reddit (2026-08-05): third-party apps to be moved onto the hosted Developer Platform. | Developer Terms 4.1 (rev. 2026-03-24): no use "as part of a service or product that is monetized"; Reddit's own examples include subscription services and free features with upsell. Data API Terms 2.4: "You may not modify the User Content except to format it for such display." | Not for a monetised app |
| Commercial contract | Possible in principle; no public rate card. | Data API Terms 3.1 | Not for MVP |
| **User shares selected text** | Yes (S0, built). | Content comes from the user, not the API; no API terms attach. | **Recommended** |

## X

| Route | Works today? | Terms | Verdict |
|---|---|---|---|
| oEmbed `publish.x.com/oembed`, unauthenticated | Partly: returns a single post's text; a long-form post came back truncated at 269 chars; a thread head returned only the first post; a 2024 dev thread reports 404 bursts, no SLA. | Developer Policy: oEmbed is an "X for Websites" embed tool; "if you don't use X for Websites to display content, you must use the X API". Developer Agreement: "Modify X Content only to format it for display." X ToS (eff. 2026-10-09): no access "other than through the currently available, published interfaces"; liquidated damages clause for scraping. | Do not build on it |
| X API v2 `GET /2/tweets` | Yes, pay-per-use: $0.005 per post read, no free tier, credits pre-purchased. | Commercial use allowed on paid plans; deletions must be mirrored within 24 h; "format only" licence question remains. | Viable on cost, not for MVP |
| **User shares selected text** | Yes. | As for Reddit. | **Recommended** |

## Generic web articles

| Route | Works today? | Position | Verdict |
|---|---|---|---|
| Action/Share extension reads the page in the user's own Safari session (G1) | Yes; paywalled/logged-in pages included. Readwise documents this as the industry pattern ("the extension gets the underlying content rendered in your browser as opposed to just a URL"). | Strongest: the user's browser lawfully received the page; the app transforms a copy for that user only, nothing republished. Instapaper's terms frame the same model. hiQ v. LinkedIn (9th Cir. 2022): public data access "will likely not constitute access without authorization", with caveats for gated data and contract/copyright claims. No reader-mode personal-use case found (unverified negative). | **Default** |
| App server fetches the URL | Open pages only; paywalls and JS-heavy sites fail; datacenter IPs increasingly blocked. | Weaker: the developer's server is the accessing party, so site terms bind RetAIn. | Fallback only |

## Apple App Store Review Guidelines (fetched 2026-09-24)

- **5.2.2** — content from a third-party service requires being "specifically permitted to
  do so under the service's terms of use. Authorization must be provided upon request."
  This is the binding rule against unapproved Reddit/X fetching.
- **4.2.2** — apps "shouldn't primarily be … web clippings, content aggregators"; the
  rewriting/retention layer is the differentiator to lean on.
- **1.2** UGC obligations don't apply to single-user private pieces.

## Sources fetched
redditinc.com/policies/data-api-terms (rev. 2026-07-20) · redditinc.com/policies/developer-terms
(rev. 2026-03-24) · redditinc.com/policies/user-agreement (eff. 2026-07-01) · r/modnews
1tq9vxo (2026-05-28) · r/redditdev 1vgbm9c (2026-08-05) and /new feed · reddit.com/robots.txt ·
live `.json` probes · Wayback: Responsible Builder Policy (2026-08-28), Developer Platform &
Accessing Reddit Data (2026-09-18), Public Content Policy (2026-09-20), Data API Wiki
(2025-05-29) · docs.x.com/developer-terms/agreement (2026-04-27) · docs.x.com/developer-terms/policy
· docs.x.com/x-api/getting-started/pricing · docs.x.com/x-for-websites/oembed-api · x.com/en/tos
(eff. 2026-10-09) · publish.x.com/oembed probes (5 posts, 30-request burst) · devcommunity.x.com
t/225519 · developer.apple.com/app-store/review/guidelines · Wayback instapaper.com/terms
(2026-06-15) · docs.readwise.io/reader/docs/saving-content · loeb.com hiQ analysis (2022).
Unverified: X Articles via oEmbed; Reddit commercial pricing; logged-in Reddit `.json`.
