# Competitive scan — "your words woven into what you're already reading"

*G4 in docs/poc2-transform.md §8. Researched 2026-09-24 by a background research agent over
30+ fetched pages; every row cites a fetched page or a search snippet, and unverified items
are marked. PRD §6's "competitive scan not yet done" is closed by this file.*

## What is ours

Nobody found does RetAIn's combination: user-chosen **English** content, taken via the iOS
share sheet, LLM-transformed to carry the reader's **own** target words idiomatically, with
tap-to-reveal, for advanced ESL readers. The two nearest neighbours each hold one half:
**LinguistiCat** has the iOS Safari substitution surface (foreign-language dictionary swap,
not idiomatic rewrite, English not a target); the **LLM-story apps** (Storytailor, A1-C1,
WordLoopStory, Langua, Lenguia, StoryLearning, WordPecker) put "your words in prose" but in
generated filler content, never in what you were already reading. Absence in this scan is
not proof of absence.

Cautionary signals from the neighbours: browser substitution extensions monetise poorly
(Toucan: $30M raised, could not reach profitability, folded into Babbel's free tier; Fluent
dormant; Vocabo and NeonLingo free), and most LLM-era ESL entrants are solo-dev apps with
single-digit ratings. Demand-side interest, no traction proof yet.

## Landscape

| Product | Platform | Mechanism | Audience | Pricing | Traction | Status |
|---|---|---|---|---|---|---|
| **Toucan by Babbel** | Chrome + Edge desktop; no Safari/iOS | Dictionary substitution of English words on any page into the *foreign* language being learned; hover shows original | Foreign-language learners (not ESL) | Free since acquisition | ~$30M raised; 200k users, 4.6★ | Wound down 2023; tech acquired by Babbel; extension still maintained (Jul 2025) |
| **Fluent (usefluent.co)** | Chrome | Same substitution model (FR/ES/IT) | Foreign-language learners | Free | 7k users (2021) | Dormant: site 404, last update Jan 2024 |
| **Vocabo** | Chromium browsers | Google-Translate substitution, 249 languages | Foreign-language learners | Free | ~758 active | Active |
| **NeonLingo** | Chrome + Edge | AI-chosen substitution at i+1 level; click-to-translate | Foreign-language learners | Freemium | 3k weekly | Active (LLM-era) |
| **LinguistiCat** | **iOS Safari extension** | Replaces words on sites with target-language vocab; v6.10 lets users add their own words | Foreign-language learners; English not a target | $1.99/mo, $7.99 lifetime | 11k downloads, 4.6★/68 | Active, solo dev |
| **Readlang** | Web, ext., iOS/Android | Click-to-translate while reading; no rewriting | Foreign-language readers | $6/mo | Long-running | Active |
| **LingQ** | Web, iOS/Android; **Safari share-sheet importer** | Import any page, read with click-to-translate; no rewriting | Foreign-language readers | $10/mo | Established | Active |
| **LelaAI** | iOS; **share extension** | Inline translation over imported articles; no rewriting | Foreign-language readers incl. English | ₹99/mo | Low | Last update Apr 2024 |
| **WordUp** | iOS/Android/web/Chrome | Own content: 25k-word map, AI tutor; no user-content rewrite | **ESL** | $8–11/mo | 4.8★/14k+ | Active |
| **Vocabulary.com** | Web/iOS | Adaptive quizzes; own content | ESL + schools | ~$13/mo | Acquired by IXL | Active |
| **Membean** | Web | Multimodal SRS drills; own content | Schools | $6–15/mo | Mixed | Active |
| **Lingua.ly** | Chrome + mobile | Immersion reading with click-tracked vocab | Foreign-language | Freemium | 100k first month | **Shut down 2016** |
| **Storytailor / Tsumugi** | iOS | Enter words → LLM story with words highlighted (generated) | Children + ESL | $3.99/mo | Few ratings | Active |
| **A1-C1: Learn words in context** | iOS | LLM daily dialogues around weak words (generated) | ESL | $1.79 | 1 rating | Solo dev |
| **Read More English** | iOS | AI articles to interests, tap-define (generated) | ESL | $25/yr | 2 ratings | Dec 2024 |
| **ReadSmart English** | iOS | Curated readings; **saved words highlighted when they recur** (no insertion) | ESL | IAPs | Few ratings | Active |
| **WordLoopStory** | iOS | LLM stories from its own pool (generated) | ESL | Freemium | n/a | Active |
| **Langua** | Web/iOS/Android | AI tutor; stories featuring saved words (generated) | Incl. English | Subscription | n/a | Active |
| **Lenguia** | Web/iOS/Android/ext. | Flashcard words prioritised in future stories; book import (generated + import) | Incl. English | Trial | n/a | Active |
| **StoryLearning App** | Web | Saved words reappear in future stories (generated) | Foreign-language | $15/mo | Parent brand 2M books | Active |
| **WordPecker** (OSS) | Web | LLM passages highlighting learned words (generated) | Any | Free | 2.3k stars | Hobby |
| **Cathoven Level Adaptor** | Web | LLM **rewrites arbitrary text** to a CEFR level — closest "rewrite user-chosen text" found, but level-targeting, for teachers | ELT writers | n/a | Cited in papers | Active |
| **HighVocab** | Chrome | Save + highlight English words across the web (unverified detail) | ESL | unverified | unverified | Active (unverified) |
| **Word Replacer for Safari** | iOS Safari ext. | Generic find/replace rules; no learning layer | General | unverified | unverified | Active |

## Sources fetched
techcrunch.com/2023/09/19/babbel-acquires-language-learning-browser-extension-toucan ·
babbel.com/press (Toucan integration) · jointoucan.com · Chrome Web Store (Toucan) ·
fluent.co (now unrelated) · scalarly.com (Fluent) · dailyhive.com (Fluent) · crx4chrome
(Fluent) · linkedin.com/company/usefluent · usefluent.co (404) · vocabo.io · neonlingo.com ·
apps.apple.com id1662017456 (LinguistiCat) · linguisticat.com · readlang.com/pricing ·
lingq.com importer + forum thread 5501 · producthunt LelaAI · apps.apple.com id1661017833 ·
producthunt Vocabi · apps.apple.com id1365078730 (WordUp) · ixl.com (Vocabulary.com) ·
membean.com/pricing · en.wikipedia.org/wiki/Lingua.ly · apps.apple.com id6744620244,
id6740411916, id6477700701, id6759513882 · wordloopstory.app · languatalk.com/try-langua ·
lenguia.com/functions/stories · storylearning.com/private-app · github.com/baturyilmaz/
wordpecker-app · github.com/Amirmfth/U-Vocab/issues/9 · cathoven.com/cefr-checker ·
highvocab.com · apps.apple.com id1611191823.
