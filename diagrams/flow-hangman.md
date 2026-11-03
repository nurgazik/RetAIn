# User flow: hangman (daily exercise)

**Status: built 2026-11-01** (PRD D69; backlog UX-22): `ios/RetAIn/App/HangmanView.swift` (the game, on the phone),
`src/service/practice.py` (`hangman_result`, `play_hangman`), table `hangman_games`. No model calls.

```mermaid
flowchart TD
    Q["Code: the one prioritised list (D66)<br/>same rounds of 5 as the other exercises · any word, any length<br/>its own shuffled order inside the round (D72)"]:::code --> S
    S([You see the word's tiles in stardust (D65)<br/>its meaning · 6 lives as stars]) --> G([You tap a letter on the A–Z keys])
    S -.-> H([Stuck? Show a sentence:<br/>the word's fill-in sentence, blanked · from the bank, no model])
    H -.-> G
    G --> C{"Phone: in the word?"}:::code
    C -- yes --> R["Every place it occurs condenses out of the dust"]:::code --> W{"Every letter shown?"}:::code
    C -- no --> M["The row shakes · the mist thickens · a star dims"]:::code --> L{"6 wrong?"}:::code
    W -- no --> G
    L -- no --> G
    W -- yes --> WON([Won: the word in bold teal · tap it for its card])
    L -- yes --> LOST([Out of lives: the missing letters in red · tap for its card])
    WON --> P["POST /v1/practice/hangman with the whole guess log"]
    LOST --> P
    P --> V["Server: replay the log against the word (re-check),<br/>store the game in hangman_games · one game per word a day"]:::code
    V --> SC["Schedule: lost → a miss, top of tomorrow's list<br/>won alone → place unchanged (letters prompt the recall)"]:::code

    classDef code stroke:#718096,stroke-dasharray:4 3
```

- **No model, no eval.** The clue is the card's meaning; the hint reuses the banked fill-in sentence (a word without
  one shows no hint button).
- **6 lives for every word** (classic hangman), not tied to length: long words are the easier ones, and fixed rules
  keep scores comparable for future leaderboards.
- **Exercises stay independent (D57):** a word can come up in hangman after fill-in or the sentence exercise.
- **Order inside a round (D72):** each exercise visits the round's 5 words in its own shuffled order, fixed for the day (seeded by day, exercise and word), so one exercise doesn't give away the next word of another; rounds still come in priority order. You still know the round's 5 words.
- **Stats come later from the raw log** (`hangman_games`: guesses in order, wrong count, hint, won, seconds):
  games per word, hardest words, hint rate, streaks, points.
- **Leaderboards between users** would need each guess checked on the server (a game run on the phone can be
  faked); the table stays the same.
