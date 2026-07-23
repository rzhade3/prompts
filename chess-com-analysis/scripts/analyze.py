#!/usr/bin/env python3
"""
Chess.com game analyzer.

Pulls a player's most recent games from the public Chess.com API (no auth
required) and produces a structured report: win rates overall and by time
control, how games are won/lost, opening repertoire by color, and current
ratings.

Usage:
    python3 analyze.py <username> [--games 500] [--json]

Notes:
- Uses only the Python standard library (urllib, json, re).
- The Chess.com API requires a descriptive User-Agent header.
- Data is fetched from monthly archives, newest first, until the requested
  number of games is collected.
"""
import argparse
import json
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


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def fetch_games(username, want):
    """Return up to `want` most-recent games (newest first)."""
    username = username.strip().lower()
    try:
        archives = _get(f"{API}/player/{username}/games/archives")["archives"]
    except urllib.error.HTTPError as e:
        if e.code == 404:
            sys.exit(f"Error: Chess.com user '{username}' not found.")
        raise
    games = []
    for url in reversed(archives):  # newest month first
        month = _get(url).get("games", [])
        games.extend(reversed(month))  # newest game first within month
        if len(games) >= want:
            break
    return games[:want]


def opening_name(pgn):
    m = re.search(r'\[ECOUrl "https://www\.chess\.com/openings/([^"]+)"\]', pgn or "")
    if m:
        return m.group(1).replace("-", " ")
    m = re.search(r'\[ECO "([^"]+)"\]', pgn or "")
    return m.group(1) if m else "Unknown"


def analyze(username, games):
    username = username.strip().lower()
    n = len(games)
    overall = [0, 0, 0]  # win, loss, draw
    by_tc = defaultdict(lambda: [0, 0, 0])
    win_methods = Counter()
    loss_methods = Counter()
    latest_rating = {}
    latest_time = {}
    openings = {"white": defaultdict(lambda: [0, 0]),
                "black": defaultdict(lambda: [0, 0])}
    first_end = last_end = None

    for g in games:
        et = g.get("end_time")
        if et is None:
            continue
        first_end = et if first_end is None else min(first_end, et)
        last_end = et if last_end is None else max(last_end, et)
        color = "white" if g["white"]["username"].lower() == username else "black"
        me = g[color]
        opp = g["black" if color == "white" else "white"]
        tc = g.get("time_class", "unknown")
        res = me["result"]

        if et > latest_time.get(tc, -1):
            latest_time[tc] = et
            latest_rating[tc] = me.get("rating")

        name = opening_name(g.get("pgn", ""))
        short = " ".join(name.split(" ")[:4])
        od = openings[color][short]
        od[1] += 1

        if res == "win":
            overall[0] += 1
            by_tc[tc][0] += 1
            win_methods[opp["result"]] += 1
            od[0] += 1
        elif res in DRAW_RESULTS:
            overall[2] += 1
            by_tc[tc][2] += 1
        else:
            overall[1] += 1
            by_tc[tc][1] += 1
            loss_methods[res] += 1

    def summary(tc):
        """Win/loss summary for a time control."""
        w, l, d = by_tc[tc]
        total = w + l + d
        if total == 0:
            return None
        score = (w + 0.5 * d) / total
        return {
            "games": total,
            "win_rate": round(score * 100, 1),
            "current_rating": latest_rating.get(tc),
        }

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


def main():
    ap = argparse.ArgumentParser(description="Analyze a Chess.com player's recent games.")
    ap.add_argument("username")
    ap.add_argument("--games", type=int, default=500, help="number of recent games (default 500)")
    ap.add_argument("--json", action="store_true", help="emit raw JSON instead of a report")
    args = ap.parse_args()

    games = fetch_games(args.username, args.games)
    if not games:
        sys.exit("No games found for that user.")
    report = analyze(args.username, games)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)


if __name__ == "__main__":
    main()
