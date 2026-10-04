# The user's day: how every request knows what "today" is

Decision: PRD D51 (2026-09-30). Design: `docs/architecture.md` "The user's day".
Built 2026-09-30: `db.resolve_day` (server), `WordsStore.dayKey` (widget, same 4 am rule).

```mermaid
flowchart TD
    A([Any request from the app<br/>header X-Timezone: America/Toronto]) --> B{Header a valid<br/>timezone name?}
    B -- yes --> C{Different from<br/>users.tz?}
    C -- yes --> S[("Save users.tz")]
    C -- no --> T
    S --> T
    B -- "no / missing" --> F["Use saved users.tz,<br/>else RETAIN_TZ"]
    F --> T["Now in that timezone,<br/>minus 4 hours → local date<br/>e.g. 1:30 am Oct 1 → 2026-09-30"]
    T --> M{"Earlier than<br/>users.last_day?"}
    M -- "yes (flew west)" --> K["Keep last_day"]
    M -- no --> N[("Save as users.last_day")]
    K --> D([Day key])
    N --> D
    D --> W["Stamp new rows<br/>pieces · calls · events · words"]
    D --> Q["Answer 'today' questions<br/>cap · spent today · daily set"]
    D --> R["/v1/me → day + next_day_at + tz"]
```

## Why

- UTC stays the stored truth; the day key is stored beside it so a later timezone change
  never rewrites history, and SQLite (which can't convert named timezones) can still group
  by day.
- 4 am, not midnight: late-night sessions stay in one day (Anki's default), and the boundary
  never falls in the hour daylight saving skips or repeats.
- The day never goes back: travel can't replay a day's cap or set.
