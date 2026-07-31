#!/usr/bin/env python3
"""
Chess.com game analyzer.

Pulls a player's recent games from the public Chess.com API (no auth required)
and produces a structured report: win rates overall and by time control, how
games are won/lost, opening repertoire by color, and current ratings.

Fetched games are cached locally so follow-up questions (narrower windows,
color/opening/time-control splits, per-game listings) can be answered by
filtering the cache instead of re-downloading and re-parsing everything.

Usage:
    python3 analyze.py <username> [options]

Common options:
    --games N            number of recent games to consider (default 500)
    --json               emit the aggregate report as JSON
    --dump-games         emit normalized per-game rows as JSON (for follow-ups)
    --list-games         print human-readable per-game rows (with opening moves)

Filters (apply to every mode, so e.g. "--days 2" reports just the last 2 days):
    --days N             only games ended within the last N days
    --since YYYY-MM-DD   only games ended on/after this UTC date
    --time-class TC      bullet | blitz | rapid | daily
    --color COLOR        white | black (the player's color)
    --opening SUBSTR     opening name contains SUBSTR (case-insensitive)

Caching:
    --cache-dir DIR      where to store the games cache (see resolution below)
    --refresh            ignore any fresh cache and re-download
    --no-cache           do not read or write any cache (always live-fetch)

Cache directory resolution (first that works wins):
    1. --cache-dir DIR
    2. $CHESS_CACHE_DIR
    3. ./.cache/chess-com-analysis   (relative to the current working directory)
Caching is best-effort: if the directory is not writable, the script simply
fetches live. Agents should pass --cache-dir pointing at a session-stable,
writable scratch location so follow-ups in the same session reuse the cache.

Notes:
- Uses only the Python standard library (urllib, json, re).
- The Chess.com API requires a descriptive User-Agent header.
- Refresh re-downloads the newest month and merges it into the cache,
  de-duplicating by each game's unique `url`.
"""
import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error
from collections import Counter, defaultdict
from datetime import datetime, timezone

API = "https://api.chess.com/pub"
UA = "copilot-chess-analysis-skill (contact: via GitHub Copilot CLI)"
DRAW_RESULTS = {
    "agreed", "repetition", "stalemate", "insufficient",
    "50move", "timevsinsufficient",
}
CACHE_TTL = 600  # seconds; cache newer than this is reused without hitting the network


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #
def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


# --------------------------------------------------------------------------- #
# Cache
# --------------------------------------------------------------------------- #
def resolve_cache_dir(cli_dir):
    """Return a writable cache directory, or None if none can be created."""
    candidates = [
        cli_dir,
        os.environ.get("CHESS_CACHE_DIR"),
        os.path.join(os.getcwd(), ".cache", "chess-com-analysis"),
    ]
    for c in candidates:
        if not c:
            continue
        try:
            os.makedirs(c, exist_ok=True)
            testfile = os.path.join(c, ".write-test")
            with open(testfile, "w") as f:
                f.write("")
            os.remove(testfile)
            return c
        except OSError:
            continue
    return None


def _cache_path(cache_dir, username):
    return os.path.join(cache_dir, f"{username}.json")


def load_cache(cache_dir, username):
    """Return (games, fetched_at) from cache, or ([], 0) if unavailable."""
    if not cache_dir:
        return [], 0
    path = _cache_path(cache_dir, username)
    try:
        with open(path) as f:
            data = json.load(f)
        return data.get("games", []), data.get("fetched_at", 0)
    except (OSError, ValueError):
        return [], 0


def save_cache(cache_dir, username, games):
    if not cache_dir:
        return
    path = _cache_path(cache_dir, username)
    tmp = path + ".tmp"
    try:
        with open(tmp, "w") as f:
            json.dump({"fetched_at": _now_ts(), "games": games}, f)
        os.replace(tmp, path)
    except OSError:
        pass  # best-effort


def _now_ts():
    return int(datetime.now(timezone.utc).timestamp())


def _dedup(games):
    """Merge games keyed by unique `url`; later entries win (finalized data)."""
    by_url = {}
    for g in games:
        key = g.get("url") or g.get("uuid") or id(g)
        by_url[key] = g
    return sorted(by_url.values(), key=lambda g: g.get("end_time", 0), reverse=True)


def fetch_games(username, want, cache_dir, refresh, use_cache):
    """
    Return up to `want` most-recent games (newest first).

    Strategy: reuse a fresh cache when it already satisfies `want`; otherwise
    re-download the newest month(s), merge into the cache, and de-dup by `url`.
    """
    username = username.strip().lower()

    cached = []
    if use_cache and not refresh:
        cached, fetched_at = load_cache(cache_dir, username)
        fresh = (_now_ts() - fetched_at) < CACHE_TTL
        if fresh and len(cached) >= want:
            return cached[:want]

    try:
        archives = _get(f"{API}/player/{username}/games/archives")["archives"]
    except urllib.error.HTTPError as e:
        if e.code == 404:
            sys.exit(f"Error: Chess.com user '{username}' not found.")
        raise

    merged = {g.get("url"): g for g in cached if g.get("url")}
    downloaded_any = False
    for url in reversed(archives):  # newest month first
        month = _get(url).get("games", [])
        for g in month:
            if g.get("url"):
                merged[g["url"]] = g
        downloaded_any = True
        # Always refresh at least the newest month; stop once we have enough.
        if len(merged) >= want and downloaded_any:
            break

    games = _dedup(list(merged.values()))
    if use_cache:
        save_cache(cache_dir, username, games)
    return games[:want]


# --------------------------------------------------------------------------- #
# Normalization
# --------------------------------------------------------------------------- #
def opening_name(pgn):
    m = re.search(r'\[ECOUrl "https://www\.chess\.com/openings/([^"]+)"\]', pgn or "")
    if m:
        return m.group(1).replace("-", " ")
    m = re.search(r'\[ECO "([^"]+)"\]', pgn or "")
    return m.group(1) if m else "Unknown"


def extract_moves(pgn, limit=12):
    """Return the first `limit` SAN moves from a PGN's movetext."""
    if not pgn:
        return []
    parts = pgn.split("\n\n")
    movetext = parts[-1] if len(parts) > 1 else pgn
    movetext = re.sub(r"\{[^}]*\}", "", movetext)     # strip clock/eval comments
    movetext = re.sub(r"\d+\.(\.\.)?", "", movetext)  # strip move numbers
    movetext = movetext.replace("...", " ")
    toks = [t for t in movetext.split() if t not in ("1-0", "0-1", "1/2-1/2", "*")]
    return toks[:limit]


def normalize(username, g, moves_limit=12):
    """Flatten a raw Chess.com game into a single row keyed to the player."""
    color = "white" if g["white"]["username"].lower() == username else "black"
    me = g[color]
    opp = g["black" if color == "white" else "white"]
    res = me["result"]
    if res == "win":
        outcome = "win"
    elif res in DRAW_RESULTS:
        outcome = "draw"
    else:
        outcome = "loss"
    et = g.get("end_time")
    pgn = g.get("pgn", "")
    return {
        "url": g.get("url"),
        "end_time": et,
        "date": datetime.fromtimestamp(et, timezone.utc).strftime("%Y-%m-%d") if et else None,
        "time_class": g.get("time_class", "unknown"),
        "time_control": g.get("time_control"),
        "my_color": color,
        "outcome": outcome,          # win | loss | draw
        "my_result": res,            # raw: win, checkmated, timeout, resigned, ...
        "opponent_result": opp["result"],
        "opponent": opp.get("username"),
        "my_rating": me.get("rating"),
        "opponent_rating": opp.get("rating"),
        "opening": opening_name(pgn),
        "moves": extract_moves(pgn, moves_limit),
    }


# --------------------------------------------------------------------------- #
# Filtering
# --------------------------------------------------------------------------- #
def apply_filters(rows, args):
    out = rows
    if args.days is not None:
        cutoff = _now_ts() - args.days * 86400
        out = [r for r in out if (r["end_time"] or 0) >= cutoff]
    if args.since:
        try:
            since_ts = datetime.strptime(args.since, "%Y-%m-%d").replace(
                tzinfo=timezone.utc).timestamp()
        except ValueError:
            sys.exit("Error: --since must be YYYY-MM-DD")
        out = [r for r in out if (r["end_time"] or 0) >= since_ts]
    if args.time_class:
        tc = args.time_class.lower()
        out = [r for r in out if r["time_class"] == tc]
    if args.color:
        col = args.color.lower()
        out = [r for r in out if r["my_color"] == col]
    if args.opening:
        needle = args.opening.lower()
        out = [r for r in out if needle in (r["opening"] or "").lower()]
    return out


# --------------------------------------------------------------------------- #
# Aggregation / report
# --------------------------------------------------------------------------- #
def analyze(username, rows):
    n = len(rows)
    overall = [0, 0, 0]  # win, loss, draw
    by_tc = defaultdict(lambda: [0, 0, 0])
    win_methods = Counter()
    loss_methods = Counter()
    latest_rating = {}
    latest_time = {}
    openings = {"white": defaultdict(lambda: [0, 0]),
                "black": defaultdict(lambda: [0, 0])}
    first_end = last_end = None

    for r in rows:
        et = r["end_time"]
        if et is not None:
            first_end = et if first_end is None else min(first_end, et)
            last_end = et if last_end is None else max(last_end, et)
        tc = r["time_class"]
        if et is not None and et > latest_time.get(tc, -1):
            latest_time[tc] = et
            latest_rating[tc] = r["my_rating"]

        short = " ".join((r["opening"] or "Unknown").split(" ")[:4])
        od = openings[r["my_color"]][short]
        od[1] += 1

        if r["outcome"] == "win":
            overall[0] += 1
            by_tc[tc][0] += 1
            win_methods[r["opponent_result"]] += 1
            od[0] += 1
        elif r["outcome"] == "draw":
            overall[2] += 1
            by_tc[tc][2] += 1
        else:
            overall[1] += 1
            by_tc[tc][1] += 1
            loss_methods[r["my_result"]] += 1

    def summary(tc):
        w, l, d = by_tc[tc]
        total = w + l + d
        if total == 0:
            return None
        score = (w + 0.5 * d) / total
        return {"games": total, "win_rate": round(score * 100, 1),
                "current_rating": latest_rating.get(tc)}

    return {
        "username": username,
        "sample_size": n,
        "date_range": {
            "from": datetime.fromtimestamp(first_end, timezone.utc).strftime("%Y-%m-%d") if first_end else None,
            "to": datetime.fromtimestamp(last_end, timezone.utc).strftime("%Y-%m-%d") if last_end else None,
        },
        "overall": {"wins": overall[0], "losses": overall[1], "draws": overall[2],
                    "win_rate": round(overall[0] / n * 100, 1) if n else 0},
        "by_time_control": {tc: summary(tc) for tc in by_tc},
        "win_methods": dict(win_methods.most_common()),
        "loss_methods": dict(loss_methods.most_common()),
        "current_ratings": latest_rating,
        "openings": {
            color: sorted(
                ([name, w, t, round(w / t * 100)] for name, (w, t) in d.items() if t >= 3),
                key=lambda x: -x[2],
            )[:10]
            for color, d in openings.items()
        },
    }


def pct(part, whole):
    return f"{part / whole * 100:.0f}%" if whole else "-"


def print_report(r):
    o = r["overall"]
    print(f"\n{'=' * 60}")
    print(f"  CHESS.COM ANALYSIS: {r['username']}")
    print(f"  {r['sample_size']} games  |  {r['date_range']['from']} to {r['date_range']['to']}")
    print(f"{'=' * 60}\n")

    print(f"OVERALL: {o['wins']}W / {o['losses']}L / {o['draws']}D  ({o['win_rate']}% win rate)\n")

    print("BY TIME CONTROL")
    print(f"  {'control':8s} {'games':>6s} {'win%':>6s} {'cur':>6s}")
    for tc, s in sorted(r["by_time_control"].items(), key=lambda x: -(x[1]["games"] if x[1] else 0)):
        if not s:
            continue
        cur = s["current_rating"] if s["current_rating"] is not None else "-"
        print(f"  {tc:8s} {s['games']:>6d} {s['win_rate']:>5.0f}% {str(cur):>6s}")
    print()

    print("HOW YOU WIN")
    wtot = sum(r["win_methods"].values())
    for k, v in r["win_methods"].items():
        print(f"  {k:12s} {v:4d}  {pct(v, wtot)}")
    print("\nHOW YOU LOSE")
    ltot = sum(r["loss_methods"].values())
    for k, v in r["loss_methods"].items():
        print(f"  {k:12s} {v:4d}  {pct(v, ltot)}")
    print()

    for color in ("white", "black"):
        print(f"TOP OPENINGS AS {color.upper()}")
        for name, w, t, wr in r["openings"][color]:
            flag = " *" if t >= 8 and wr < 45 else ""
            print(f"  {t:4d} games  {wr:3d}%  {name}{flag}")
        print()
    print("(* = played often but low win rate — candidate to fix/replace)\n")


def print_game_list(rows):
    print(f"\n{len(rows)} games (newest first):\n")
    for r in rows:
        rating = r["my_rating"] if r["my_rating"] is not None else "-"
        header = (f"{r['date']}  {r['time_class']:6s}  {r['my_color']:5s}  "
                  f"{r['outcome']:4s} ({r['my_result']})  vs {r['opponent']} "
                  f"[{rating} v {r['opponent_rating']}]")
        print(header)
        print(f"    {r['opening']}")
        if r["moves"]:
            print(f"    {' '.join(r['moves'])}")
        print()


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description="Analyze a Chess.com player's recent games.")
    ap.add_argument("username")
    ap.add_argument("--games", type=int, default=500, help="number of recent games (default 500)")

    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--json", action="store_true", help="emit the aggregate report as JSON")
    mode.add_argument("--dump-games", dest="dump_games", action="store_true",
                      help="emit normalized per-game rows as JSON")
    mode.add_argument("--list-games", dest="list_games", action="store_true",
                      help="print per-game rows with opening moves")

    ap.add_argument("--days", type=int, help="only games ended within the last N days")
    ap.add_argument("--since", help="only games ended on/after this UTC date (YYYY-MM-DD)")
    ap.add_argument("--time-class", dest="time_class", help="bullet | blitz | rapid | daily")
    ap.add_argument("--color", help="white | black (the player's color)")
    ap.add_argument("--opening", help="opening name contains this substring (case-insensitive)")
    ap.add_argument("--moves", type=int, default=12, help="opening moves to keep per game (default 12)")

    ap.add_argument("--cache-dir", dest="cache_dir", help="directory for the games cache")
    ap.add_argument("--refresh", action="store_true", help="ignore fresh cache and re-download")
    ap.add_argument("--no-cache", dest="no_cache", action="store_true", help="never read or write a cache")
    args = ap.parse_args()

    use_cache = not args.no_cache
    cache_dir = resolve_cache_dir(args.cache_dir) if use_cache else None

    games = fetch_games(args.username, args.games, cache_dir, args.refresh, use_cache)
    if not games:
        sys.exit("No games found for that user.")

    username = args.username.strip().lower()
    rows = [normalize(username, g, args.moves) for g in games]
    rows = apply_filters(rows, args)
    if not rows:
        sys.exit("No games match the given filters.")

    if args.dump_games:
        print(json.dumps(rows, indent=2))
    elif args.list_games:
        print_game_list(rows)
    else:
        report = analyze(username, rows)
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print_report(report)


if __name__ == "__main__":
    main()
