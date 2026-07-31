# Deep Research prompt — content sources for RetAIn

Paste everything below the line into Gemini Deep Research. Findings get merged
into docs/content-sources.md after our own license verification pass.

---

I am building a small consumer app with the following content pipeline: we fetch
text content from legally safe sources and use an LLM to **rewrite it** (create
derivative works) — embedding specific vocabulary words into the text — then show
the rewritten piece to one reader inside the app, with attribution and a link to
the original. Think of it as a personalized daily reading digest built from
rewritten source material.

I need you to research and produce a comprehensive, verified inventory of English
(or English-edition) content sources we can legally and practically use. This is
the most important architectural decision in the product, so please be exhaustive
and skeptical: verify license claims against the source's own terms/license page
and quote the operative language.

## Hard criteria (all must hold)

1. **Legally rewritable.** The license must permit derivative works, including
   commercial use. Acceptable: public domain (including US federal government
   works), CC0, CC BY, CC BY-SA, or open government licenses that explicitly
   permit adaptation (e.g., UK OGL, Canada's Open Government Licence). NOT
   acceptable: CC BY-ND, CC BY-NC(-ND), "all rights reserved," or API terms that
   require displaying content unmodified. If a site's article text and its
   images/embeds carry different licenses, say so — we only need the text.
2. **Programmatically fetchable at zero or trivial cost.** RSS/Atom feeds, open
   REST APIs, bulk dumps, or stable scrape-friendly HTML with permissive terms
   of use. Note rate limits and whether full text (not just summaries) is
   available in the feed/API.
3. **English text** of reasonable quality (the reader is an advanced English
   learner; simplified-English sources are less interesting but note them).
4. **Tone-suitable for light reading.** We deliberately exclude tragedy-centric
   hard news (war casualties, disasters, trafficking) — sources skewing to
   science, technology, culture, history, food, travel, sports, business,
   human interest, and ideas are most valuable. A hard-news source is still
   worth listing if it has usable soft sections.

## Two buckets — we need both

- **FRESH (perishable):** publishes new items at least ~weekly, ideally daily.
  This is our scarce resource — dig hard here.
- **EVERGREEN (pool):** large archives whose value doesn't decay (Q&A sites,
  classic literature, essays, encyclopedic/travel/how-to content). Volume matters
  more than freshness.

## What we already know — do NOT spend effort re-verifying these

Verified usable: Global Voices (CC BY, alive, full text in RSS — currently our
only live news anchor, which is exactly the fragility this research must fix);
Stack Exchange network (CC BY-SA); Wikipedia/Wikivoyage (CC BY-SA); Project
Gutenberg + Standard Ebooks (public domain); open-access journals PLOS/eLife/
PeerJ/BMC (CC BY); US federal government works (public domain: NASA, NIH, NOAA,
Library of Congress, Smithsonian).

Verified dead or unusable: Voice of America (operations halted March 2025 —
frozen archive only; but tell me if it has meaningfully resumed publishing);
Wikinews (closed by Wikimedia 2026); The Conversation (CC BY-ND — no
derivatives); Reddit API (paid/restrictive); Guardian Open Platform (terms
require unmodified reproduction — but flag if their current terms say otherwise).

## Specific angles to investigate (beyond the obvious)

- Other CC BY or public-domain **news/feature outlets**: nonprofit newsrooms,
  openly licensed magazines, university news services, press-freedom or
  development-sector outlets (e.g., is SciDev.Net, Mongabay, ProPublica's
  non-ND subset, 404 Media?, The Public Domain Review, Rest of World, Knowable
  Magazine, Aeon/Psyche, Hakai, Undark, Grist, openDemocracy usable? Verify
  each — many use ND or NC clauses).
- **Science/knowledge digests** with permissive licenses: university press
  offices (many US state university news services), Eurekalert-style wires,
  The Conversation *competitors* without ND, open-access preprint digests,
  Our World in Data (verify current license).
- **Government & IGO publishers** beyond the US: UK OGL sources (gov.uk, BBC?
  no — but e.g. Kew, National Archives), Canada OGL, EU institutions
  (europa.eu reuse policy), UN agencies (UNESCO CC BY?, WHO, World Bank CC BY,
  IMF), national museums/galleries with CC0/CC BY text (Rijksmuseum, Met,
  Smithsonian Open Access, Europeana aggregated text).
- **Evergreen pools we may have missed:** wikiHow (license?), iFixit (CC BY-NC-SA?
  — check), OpenStax and other CC BY textbooks, Wikisource essays/speeches,
  LibriVox-adjacent text, StackExchange-alternatives (Quora? — almost certainly
  not; verify), TripAdvisor-alternatives with open licenses, open recipe
  databases, chess/sports databases with annotated prose, Atlas Obscura (?),
  99% Invisible transcripts (?), public-domain newspaper archives with modern
  usability (Chronicling America).
- **Aggregators/directories** that could point to more: DOAJ, Openverse,
  Creative Commons certified content lists, Wikimedia's list of CC BY news
  sources, awesome-lists on GitHub for open content.
- **Podcast/video transcripts** with permissive licenses (most are all-rights-
  reserved — but flag exceptions).

## Output format

For every candidate source, give:

| Field | What I need |
|---|---|
| Name + URL | |
| Bucket | fresh / evergreen |
| Content categories | e.g., science, culture, travel |
| License | exact license + **direct URL to the license/terms page** + a short quote of the operative language about derivatives/adaptation |
| Verdict | USABLE / UNUSABLE / NEEDS-HUMAN-CHECK, with one-line reason |
| Access method | RSS/API/dump/scrape; full text or summaries; rate limits |
| Volume & freshness | items/day or archive size |
| Tone fit | light-reading suitability, 1–5 |
| Caveats | mixed-license content, attribution requirements, share-alike obligations, wire-service contamination, etc. |

End with: (1) a ranked shortlist of the 5 best FRESH sources and 5 best EVERGREEN
sources by overall fit; (2) a list of promising sources you could NOT verify
confidently, so a human can check them; (3) anything structurally interesting we
haven't considered (e.g., a licensing program, a syndication service, a public
content API) that changes the picture.

Prioritize accuracy over volume: a wrong "USABLE" verdict is much worse than a
missing source. When license information is ambiguous or contradicts itself,
mark it NEEDS-HUMAN-CHECK rather than guessing.
