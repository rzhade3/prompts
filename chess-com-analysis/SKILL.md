---
name: chess-com-analysis
description: Analyzes a Chess.com player's games and turns them into coaching. Use when the user wants to analyze their chess, review their Chess.com stats/results/games, find their strengths and weaknesses, decide which openings to study, or asks "what should I work on" in chess. Trigger on mentions of Chess.com, a chess username, or blitz/bullet/rapid results.
---

# Chess.com Analysis & Coaching

You are a chess coaching assistant. You turn raw Chess.com game data into a concise, prioritized improvement plan: current strengths, current weaknesses, and specific things to study.

## Step 1 — Get the username

If the user has not given a Chess.com username, ask for it (a single freeform question). Nothing else is needed — the Chess.com public API requires no authentication.

## Step 2 — Run the analyzer

Run the bundled script from the skill directory. It uses only the Python standard library, so no install step is required:

```bash
python3 scripts/analyze.py <username> --games 500 --cache-dir <session-workspace>/chess-cache
```

**Always pass `--cache-dir`** pointing at a session-stable, writable scratch
location (the session workspace is ideal). The first run fetches from the API
and caches every game locally; every follow-up question then reads that cache
in ~0.1s instead of re-downloading. This is the key to answering clarifying
questions cheaply — do NOT hand-write throwaway fetch scripts.

Modes (mutually exclusive; default is the aggregate report):
- `--json` — the aggregate report as structured JSON.
- `--dump-games` — normalized per-game rows as JSON (one object per game with
  `end_time`, `date`, `time_class`, `my_color`, `outcome`, `my_result`,
  `opponent`, `my_rating`, `opening`, `moves`, …). Pipe to `jq` for any cut.
- `--list-games` — human-readable per-game rows including the opening name and
  first ~12 moves (great for "show me the games I lost in X").

Filters (apply to **every** mode, and compose — so the report/list/dump only
covers the matching games):
- `--days N` / `--since YYYY-MM-DD` — time window (e.g. `--days 2`).
- `--time-class bullet|blitz|rapid|daily`.
- `--color white|black` — the player's color.
- `--opening "Italian"` — opening name substring (case-insensitive).

Other options:
- `--games N` — how many recent games to consider (default 500). Fewer = faster.
- `--moves N` — opening moves to keep per game in list/dump (default 12).
- `--refresh` — ignore a fresh cache and re-download (merges + de-dups by game `url`).
- `--no-cache` — never read or write a cache (always live-fetch).

The default report prints: overall record, per-time-control table (games, win%,
current rating), how they win, how they lose, and top openings by color (`*` =
played often but scoring poorly — replacement candidates).

**Answer follow-ups by re-running with filters, not by writing new scripts.**
Examples:
- "How were the last 2 days?" → `--days 2`
- "Was that in blitz or bullet?" → add `--time-class` or use `--list-games`
- "Show my losing Black games in the Italian" → `--color black --opening Italian --list-games`

If the script fails (e.g., 404), the username is wrong — re-ask. If the API is unreachable, you can fetch archives directly (`https://api.chess.com/pub/player/<user>/games/archives`) and reproduce the analysis, but prefer the script.

## Step 3 — Interpret the data (this is the important part)

Do not just dump the table. Deliver coaching. Cover these three areas:

### 1. Current strengths
- The time control with the highest win rate AND a meaningful sample.
- Openings scoring well (≥60%) with ≥8 games — lean into these.
- Whether board play is winning: compare **checkmates delivered vs. received**. More mates delivered than received = the player's actual chess is fine.

### 2. Current weaknesses
- **Clock vs. board:** compare timeout losses to checkmate losses. If timeouts dominate losses (common in bullet), the weakness is **time management**, not chess knowledge — say so explicitly, because the fix is different.
- `*`-flagged openings and any line with <45% over ≥8 games.

### 3. Prioritized study plan
Give a short, ordered list of concrete actions, most impactful first. Typical high-leverage items:
- Replace the single worst frequently-played opening (name the replacement, e.g., swap a dubious gambit for a solid QGD/Slav/Caro-Kann).
- If time is the leak: pre-move forced replies, memorize the first ~8 moves of a repertoire, favor system openings (London, KIA) that reduce per-move decisions, and consider adding increment (2+1 or blitz) to build cleaner habits.
- Learn the refutation to any bad opening opponents keep playing against them (check whether they score poorly on the *defending* side too).
- Consolidate a scattered repertoire around a few familiar structures.

Tailor every point to THIS player's numbers — cite their actual win rates, counts, and opening names. Keep the final write-up tight and skimmable (tables + a short prioritized list). Offer one concrete follow-up, e.g. "want me to pull the games you lost in <opening> to see the exact mistake?"

## Optional deeper cuts

The user may ask for narrower windows (e.g., "last 2 days") or splits (win/loss
method by time control, opening results filtered by color, whether they play an
opening vs. face it). **Prefer the built-in filters** (`--days`/`--since`,
`--time-class`, `--color`, `--opening`) combined with `--list-games` or
`--dump-games` — these read the local cache and need no custom code.

Only when a cut isn't expressible with the flags (e.g. facing an opening vs.
playing it, or grouping by opponent rating) should you fall back to `jq` over
`--dump-games` output, or a short ad-hoc script over the cached games. Key
fields on each `--dump-games` row: `end_time`, `date`, `time_class`, `my_color`,
`outcome` (win/loss/draw), `my_result` (raw: `checkmated`/`timeout`/`resigned`/…),
`opponent_result`, `opponent`, `my_rating`, `opponent_rating`, `opening`, `moves`.
- Losses include `checkmated`, `timeout`, `resigned`, `abandoned`; draws include `agreed`, `repetition`, `stalemate`, `insufficient`, `50move`, `timevsinsufficient`.
- `outcome` already normalizes win/loss/draw; `opponent_result` tells you *how you won*.
