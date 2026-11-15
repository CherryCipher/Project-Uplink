#!/usr/bin/env python3
"""Build static Uplink leaderboards from completed matches / server frag logs.

No external packages and no database. Run from cron or systemd timer.
Only explicitly configured log files are read. Only names and scores are output.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import tempfile

SUPPORTED = ("xonotic", "assaultcube", "openarena")
COLOR_CODES = re.compile(r"\^[0-9]")
Q3_SCORE = re.compile(
    r"\bscore:\s*(-?\d+)\s+ping:\s*\d+\s+client:\s*\d+\s+name:\s*(.+?)\s*$",
    re.IGNORECASE,
)
# AssaultCube logs describe kills as "<attacker> fragged <victim>".
# The default Linux syslog prefix may be followed by "[IP] ".
AC_FRAG = re.compile(r"(?:^|\]\s+)(.+?)\s+fragged\s+(.+?)\s*$", re.IGNORECASE)


def clean_name(value: str) -> str:
    value = COLOR_CODES.sub("", value)
    value = "".join(c for c in value if c.isprintable())
    return value.strip()[:64]


def merge_scores(rows: list[tuple[str, int]]) -> list[dict]:
    totals: dict[str, dict] = {}
    for raw_name, score in rows:
        name = clean_name(raw_name)
        if not name or name.casefold() in ("unnamedplayer", "console", "world"):
            continue
        key = name.casefold()
        if key not in totals:
            totals[key] = {"name": name, "score": 0}
        totals[key]["score"] += score
    return sorted(totals.values(), key=lambda p: (-p["score"], p["name"].casefold()))[:100]


def parse_xonotic(log: str) -> list[dict]:
    """Parse old-style sv_logscores_file :scores/:player/:end blocks.

    Newer eventlog ':player:see-labels:...' records use another format;
    this parser intentionally ignores them rather than publishing wrong scores.
    """
    rows = []
    match = []
    inside = False
    for raw in log.splitlines():
        line = raw.strip()
        if line.startswith(":scores:"):
            match, inside = [], True
        elif inside and line.startswith(":player:"):
            parts = line.split(":", 6)
            if len(parts) == 7 and parts[2] != "see-labels":
                try:
                    frags = int(parts[2])
                    int(parts[3])  # deaths, validate format
                    match.append((parts[6], frags))
                except ValueError:
                    pass
        elif inside and line == ":end":
            rows.extend(match)
            match, inside = [], False
    return merge_scores(rows)


def parse_openarena(log: str) -> list[dict]:
    """Capture Q3 scoreboard lines after Exit: and before next InitGame."""
    rows = []
    match = []
    after_exit = False
    for raw in log.splitlines():
        line = raw.strip()
        if "InitGame:" in line:
            if after_exit:
                rows.extend(match)
            match, after_exit = [], False
        elif "Exit:" in line:
            if after_exit:
                rows.extend(match)
            match, after_exit = [], True
        elif after_exit:
            m = Q3_SCORE.search(line)
            if m:
                match.append((m.group(2), int(m.group(1))))
    if after_exit:
        rows.extend(match)
    return merge_scores(rows)


def parse_assaultcube(log: str) -> list[dict]:
    """Count clear player frag events in AssaultCube server logs.

    This is a frag EVENT counter, not an exact game scoreboard. Gib bonus,
    suicides, teamkills and frag rules differ by mode; inspect a real server
    log before calling this a verified leaderboard.
    """
    rows = []
    for raw in log.splitlines():
        line = raw.strip()
        m = AC_FRAG.search(line)
        if m:
            attacker = m.group(1).strip()
            # If syslog timestamp occurs before the IP prefix, use the last
            # bracketed prefix when available.
            if "] " in attacker:
                attacker = attacker.rsplit("] ", 1)[-1]
            rows.append((attacker, 1))
    return merge_scores(rows)


PARSERS = {
    "xonotic": parse_xonotic,
    "assaultcube": parse_assaultcube,
    "openarena": parse_openarena,
}


def build(paths: dict[str, Path], output: Path) -> dict:
    if not paths:
        raise ValueError("Supply at least one game log.")
    existing = {}
    if output.exists():
        try:
            old = json.loads(output.read_text(encoding="utf-8"))
            if isinstance(old.get("games"), dict):
                existing = {k: v for k, v in old["games"].items() if k in SUPPORTED}
        except (OSError, ValueError, AttributeError):
            pass

    games = dict(existing)
    timestamp = datetime.now(timezone.utc).isoformat()
    for game, path in paths.items():
        if not path.is_file():
            raise FileNotFoundError(f"{game}: log not found: {path}")
        text = path.read_text(encoding="utf-8", errors="replace")
        players = PARSERS[game](text)
        games[game] = {
            "label": "Frags" if game != "openarena" else "Score",
            "players": players,
            "updated": timestamp,
        }

    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {"games": games}
    # Atomic replace so a browser never reads half a JSON document.
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=output.parent, prefix=".leaderboards-",
        suffix=".tmp", delete=False
    ) as temporary:
        temp_path = Path(temporary.name)
        json.dump(payload, temporary, ensure_ascii=False, indent=2)
        temporary.write("\n")
    try:
        os.replace(temp_path, output)
    finally:
        temp_path.unlink(missing_ok=True)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for game in SUPPORTED:
        parser.add_argument("--" + game, type=Path, help=f"{game} server log file")
    parser.add_argument("--output", type=Path, default=Path("leaderboards.json"))
    args = parser.parse_args()
    paths = {game: getattr(args, game) for game in SUPPORTED if getattr(args, game)}
    if not paths:
        parser.error("provide at least one --xonotic/--assaultcube/--openarena path")
    result = build(paths, args.output)
    for game in paths:
        print(f"{game}: {len(result['games'][game]['players'])} players")


if __name__ == "__main__":
    main()
