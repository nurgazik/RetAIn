# Content Source Inventory (licensing verified 2026-07-22; expanded 2026-07-25)

> 2026-07-25: merged findings from an external Gemini Deep Research sweep
> (docs/gemini-research-RetAIn-sources.md) after spot-verification. Its license
> verdicts held up where tested; its volume claims ran optimistic (e.g. SciDev
> publishes ~2-4/week, not the claimed 3-8/day). The fresh-anchor single point
> of failure is resolved: we now have ~5 live fresh sources alongside Global Voices.

Research question: which content sources are freely fetchable **and** legally rewritable
(derivative works allowed), so RetAIn can rewrite real content with target words embedded?

Note: for the personal PoC, licensing is irrelevant (private use). This inventory exists so
the pipeline is built on clean sources from day one and never needs rework at product scale.

## License buckets

| Bucket | Meaning for us |
|--------|----------------|
| Public domain | Rewrite freely, no strings (attribution still good practice) |
| CC BY | Rewrite freely with attribution — the gold standard |
| CC BY-SA | Rewrite with attribution; derivative must carry the same license (acceptable wrinkle: our rewritten piece becomes CC BY-SA, but app value is personalization, not content exclusivity) |
| CC BY-ND | Republish verbatim only — **unusable** for rewriting |

## Verified sources

### Daily news (anchor slot)

**Status update (verified live, 2026-07-24): Global Voices is the anchor (PRD D16).**

- **Global Voices** — ✅ CC BY, **alive and publishing daily**. World culture / underreported
  stories; explicitly invites editing, remixing, rewriting. Full article text ships in the RSS
  `content:encoded` field (no scraping needed); `dc:creator` gives the author for attribution;
  `category` tags drive the D14 taste filter — needed, because the main feed skews grim
  (topic feeds at `/-/topics/<topic>/feed/` are the gentler pools: technology, arts-culture,
  environment, travel, education, media-journalism).
  https://globalvoices.org/about/global-voices-attribution-policy/
- **Voice of America (VOA)** — ⚠️ Public domain (US government work), but **dormant since
  March 2025** (USAGM halted VOA operations; every feed's newest item is 2025-03). Now a
  frozen public-domain *archive* — potential evergreen pool for feature-style pieces, not a
  news anchor. Config kept disabled in case it revives. Wire caveat still applies: pages mix
  in licensed AFP/AP/Reuters content (RSS `author` field exposes it — filter implemented).
  Terms: https://www.voanews.com/terms-use-and-privacy-notice
- **Wikinews** — ❌ **Closed by the Wikimedia Foundation in 2026** after 21 years. Archive
  remains CC BY if ever useful. https://en.wikinews.org/wiki/Wikinews:Copyright

**Added 2026-07-25 (fresh, license-verified unless noted):**

- **SciDev.Net** — ✅ CC BY 2.0, **verified directly**: "copy, distribute and display the
  work as well as make derivative works." Global science/tech/development features, clear
  professional English. ~2–4 articles/week (not daily — supplement, not sole anchor).
  Attribution required within first three paragraphs of a republication; third-party
  photos excluded (text-only ingestion). Feeds: /global/global_rss.xml, /global/feed/.
  https://www.scidev.net/global/content/media.html
- **NASA news & features** — ✅ Public domain (US federal work), **feed verified live
  daily** (rss/dyn/breaking_news.rss + section feeds). Space/earth science/tech; excellent
  tone fit. Watch for contractor co-productions.
- **Our World in Data** — ✅ CC BY 4.0 (site-wide, well-established; feed verified live,
  ~2–5 long-form pieces/week). Data-driven essays: health, environment, progress.
- **GOV.UK news** — ✅ UK OGL v3 (verified 2026-07: permits adapt + commercial use).
  High volume but press-release register — selective use; soft departmental releases only.
- **World Bank news & blogs** — ✅ CC BY 3.0 IGO (well-established). Policy-adjacent
  essays on development/economics/innovation; requires IGO attribution format
  ("adaptation not endorsed by World Bank").

### Curiosity / Q&A

- **Stack Exchange network** — ✅ CC BY-SA ("intended to be shared and remixed"). Hundreds of
  sites: Workplace (dead-on for professional-register goals), History, Cooking, Personal
  Finance, Sci-Fi, Travel, English Language. Free API + full data dumps.
  https://stackoverflow.blog/2009/06/25/attribution-required/
- **Wikipedia / Wikivoyage** — ✅ CC BY-SA. "On this day", "Did you know", featured articles;
  Wikivoyage travel guides.

### Science / ideas

- **Open-access journals (PLOS, eLife, PeerJ, BioMed Central)** — ✅ CC BY. Raw papers too
  dense; use abstracts and eLife's plain-language digests as seeds.
  https://journals.plos.org/plosbiology/s/licenses-and-copyright
- **US government science/culture (NASA, NIH, NOAA, Smithsonian, Library of Congress)** —
  ✅ Public domain (US federal works). Space, health, weather, "Today in History".
  https://resources.data.gov/open-licenses/

### Fiction / narrative (sleeper hit)

- **Project Gutenberg / Standard Ebooks** — ✅ Public domain. Retell classic short stories
  (O. Henry, Chekhov, Saki, Maupassant) in modern register, ~500 words, preserving plot and
  the ending's punch. Real narrative craft that generated-from-scratch content can't match.

### Evergreen additions (2026-07-25, from research sweep — licenses consistent with known facts)

- **OpenStax** — ✅ CC BY 4.0. 60+ peer-reviewed textbooks; structured, clear prose;
  API + GitHub dumps. Great "explainer" seed material.
- **Wikisource** — ✅ PD / CC BY-SA. Historical essays, speeches, literary nonfiction.
- **Rijksmuseum API** — ✅ CC0 (data/text). 800K+ art-object descriptions and curatorial
  commentary.
- **Europeana (open subset)** — ✅ filter API by `reusability=open` (CC0/CC BY only);
  discard NC/ND-tagged records.
- **Chronicling America (LoC)** — ✅ PD historic newspapers (1770–1963); OCR noise needs
  cleanup — the retold-classic wrapper could love this ("news from 100 years ago today").

### Needs human check (parked)

- **Public Domain Review** — underlying texts PD, but staff editorial essays carry
  separate rights; only usable if we extract the underlying PD text. Superb tone fit —
  worth the check later.
- **Hakai, Rest of World, Atlas Obscura** — per-article or partial open licensing at
  best; requires outreach/manual review. Not worth it while the verified pool suffices.

### Government (Canada/UK angle)

- **UK Open Government Licence / Canada Open Government Licence** — ✅ Explicitly permit
  adaptation of Crown content (Parks Canada, StatCan explainers, gov.uk).
  https://en.wikipedia.org/wiki/Open_Government_Licence

## Ruled out

- **The Conversation** — ❌ CC BY-ND: "you can't edit material" without author approval.
  https://theconversation.com/us/republishing-guidelines
- **Guardian Open Platform** — ⚠️ Current terms unverified (site blocks automated fetch);
  recollection is the free tier requires unmodified reproduction. Treat as out unless
  re-verified. Not needed given VOA + Global Voices + Wikinews.
- **Reddit API** — ❌ Paid/restricted since 2023; content licensing murky for derivatives.
- **Ruled out by 2026-07-25 sweep (all verified ND/NC/proprietary):** Mongabay (BY-ND),
  Knowable Magazine (BY-ND), Undark ("DO NOT EDIT" custom terms), ProPublica (no-edit,
  no-automation custom terms), openDemocracy (BY-NC — commercial use requires paid
  syndication), 404 Media (all rights reserved), wikiHow + iFixit (both BY-NC-SA — the
  NC kills it). The nonprofit-journalism world defaults to ND/NC precisely to prevent
  automated commercial reuse — assume ND/NC until a license page says otherwise.
- **General RSS scraping of publisher full text** — ❌ at product scale (copyright + ToS);
  RSS summaries themselves are fine as published-for-syndication metadata.

## Per-source rewrite prompt wrappers (see PRD D6)

- **News (VOA/Wikinews/GV):** preserve all facts, names, numbers, dates exactly; no invented
  details; inverted-pyramid structure; neutral register.
- **Q&A (Stack Exchange):** transform question + top answer into an advice-column piece;
  conversational-professional register.
- **Classics (Gutenberg):** compress to ~500 words; modernize register; preserve plot and
  ending.
- **Proprietary (no source):** dialogue / flash fiction / workplace vignette in the user's
  interest areas — also the register vehicle (words shown in the register the user wants to
  speak in).

Shared core (all): due-word list with "use only where genuinely idiomatic — skip words that
don't fit"; wrap used words in `<mark>`; advanced reading level (no simplification); target
length. QC pass after generation: words present and marked; per-word naturalness check;
facts preserved (news); regenerate on failure.

## Research sweep 2 (2026-08-08, founder-commissioned): creative corpora

Context: founder's feed-coherence critique ("feels incredibly random") + density-first
direction (D33). All licenses below verified by fetching the cited page on 2026-08-08.

### Top finds (high rewrite affordance, verified)

- **The Public Domain Review** — ✅ CC BY-SA 4.0 (most essays; some book excerpts
  stricter, check per item; https://publicdomainreview.org/legal/). Charming scholarly
  essays on obscure history/art/science; RSS live at /rss.xml. Rubric: "The Cabinet."
- **NOAA Ocean Exploration mission logs** — ✅ US-gov PD (oceanexplorer.noaa.gov
  media-kit + FAQ pages). First-person dive logs: shipwrecks, new species. Archive to
  2001 covers expedition gaps. No confirmed RSS — URL-pattern fetch. Rubric:
  "Dispatch from the Deep."
- **Wiktionary etymologies** — ✅ CC BY-SA 4.0 + GFDL
  (en.wiktionary.org/wiki/Wiktionary:Copyrights). Word-origin stories via MediaWiki
  API. Uniquely on-brand: the biography of one of the READER'S OWN target words.
  Needs curation filter (many etymologies are boring). Rubric: "Where Words Come From."
- **National Park Service API** — ✅ US-gov PD (nps.gov/aboutus/disclaimer.htm).
  Narrative articles: park history, wildlife, biographical sketches; REST API at
  api.nps.gov (api.data.gov key). Rubric: "Postcard from a Park."
- **Wikipedia film plots + unusual articles** — ✅ CC BY-SA 4.0. Film-plot sections and
  the "unusual articles" long tail via MediaWiki API. Avoid reproducing film dialogue
  verbatim. Rubric: "One Strange Story" / "Tonight's Plot."

### Second tier (verified, medium affordance)

- **Office of the Historian** (history.state.gov) — ✅ PD (site FAQ + FRUS about page).
  Milestones diplomatic-history essays; FRUS declassified cables. "The Back Channel."
- **Smithsonian Open Access** — ✅ CC0 subset (github.com/Smithsonian/OpenAccess
  LICENSE). api.si.edu; filter for records with substantial descriptions. "Object of
  the Day."
- **USPTO patents** — ✅ PD-typical (uspto.gov/terms-use-uspto-websites). Quirky
  historical patents via PatentsView API; needs a curated weird-patents seed list.
  "Somebody Patented That."
- **Wikivoyage** — ✅ CC BY-SA (en.wikivoyage.org/wiki/Wikivoyage:Copyleft).
  "Understand" sections only. "If You Were In..."
- **The Met Open Access** — ✅ CC0 (github.com/metmuseum/openaccess). Free API; rich
  prose only on highlight objects; pairs with existing Rijksmuseum slot.
- **CIA World Factbook** — ✅ PD (archived copyright page; current page blocks bots).
  Structured facts, LLM builds the narrative. "Country You'd Fail a Quiz On."
- **govinfo Public Papers of the Presidents** — ✅ PD (govinfo.gov/about/policies).
  api.govinfo.gov. Cleaner than Miller Center (whose terms page 404'd — do not use).
- **Wikibooks Cookbook** — ✅ CC BY-SA. Ingredient-history pages only; patchy coverage.
- **arXiv abstracts** — ⚠️ abstracts CC0, full text NOT (info.arxiv.org/help/api/tou.html).
  Thin source material; hallucination risk when expanding; ranked low deliberately.
- **Wikiquote** — ⚠️ editorial text CC BY-SA but quotes carry original copyright;
  usable ONLY with a pre-1930/PD-era author filter. Weakest recommendation.

### Ruled out this sweep (do not re-propose)

- **Old Bailey Online** — ❌ CC BY-NC (would have been top-3 otherwise).
- **Founders Online** — ❌ dataset CC BY-NC + UVA Press annotations; underlying
  18th-c. text arguably PD but separation is legal gray — parked Horizon 3.
- **ESA text** — ❌ terms forbid derivatives (esa.int/Services/Terms_and_conditions);
  only their image/video terms are CC.
- **Miller Center** — ❌ unverifiable terms (404); use govinfo PPP instead.
- **NYPL Digital Collections** — images + metadata, little narrative text; low
  affordance ("What's on the Menu" is charming but is data, not story).
- **Etymonline** — ❌ proprietary; use Wiktionary for etymology.

License-tier note: 11 of 15 finds are CC0/PD (zero attribution burden); the CC BY-SA
tier (Wikimedia family + PDR) inherits the share-alike posture already accepted for
Global Voices; Wikiquote's fair-use-adjacent tier is the only weak one.
