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
    r"\bscore:\s*(-?\d+)\s+ping:\s*\d+\s+client:\s*\d+\s+(?:name:\s*)?(.+?)\s*$",
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
    """Read completed Xonotic score blocks, including labelled player rows.

    Select the 'score' metric by reading the :labels: column list, rather
    than assuming that the first numeric field is always the right metric.
    Names may include colons or Unicode characters.
    """
    rows = []
    match = []
    inside = False
    score_column = None
    for raw in log.splitlines():
        line = raw.strip()
        if line.startswith(":scores:"):
            match, inside, score_column = [], True, None
        elif inside and line.startswith(":labels:player:"):
            labels = line[len(":labels:player:"):].split(",")
            score_column = next(
                (i for i, label in enumerate(labels)
                 if label.rstrip("!<").casefold() == "score"),
                None
            )
        elif inside and line.startswith(":player:see-labels:"):
            # :player:see-labels:<comma separated stats>:<time>:<team>:<name>
            parsed = re.match(
                r"^:player:see-labels:([^:]*):(-?\d+):(-?\d+):(.+)$",
                line
            )
            if parsed and score_column is not None:
                fields = parsed.group(1).split(",")
                if score_column < len(fields):
                    try:
                        score = int(fields[score_column])
                        match.append((parsed.group(4), score))
                    except ValueError:
                        pass
        elif inside and line.startswith(":player:"):
            # Legacy layout: :player:<score>:<deaths>:<time>:<team>:<name>
            parsed = re.match(
                r"^:player:(-?\d+):(-?\d+):(\d+):(-?\d+):(.+)$",
                line
            )
            if parsed:
                match.append((parsed.group(5), int(parsed.group(1))))
        elif inside and line == ":end":
            rows.extend(match)
            match, inside, score_column = [], False, None
    return merge_scores(rows)


def parse_openarena(log: str, excluded_names: set[str] | None = None) -> list[dict]:
    """Capture Q3 scores, excluding configured bot nicknames."""
    excluded = {clean_name(n).casefold() for n in (excluded_names or set())}
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
                if clean_name(m.group(2)).casefold() not in excluded:
                    match.append((m.group(2), int(m.group(1))))
    if after_exit:
        rows.extend(match)
    return merge_scores(rows)


def parse_assaultcube(log: str) -> list[dict]:
    """Sum frags from final, completed AssaultCube match scoreboards only.

    Match end:
        Game status: deathmatch on ..., game finished, ...
        cn name              frag death ping role    host
         0 LexusTG             6     0   11 normal  192.168.222.203

    Flag modes include a 'flag' column before 'frag'. Ignore periodic
    Game status snapshots, disconnected-client scores and kill events.
    """
    rows = []
    awaiting_header = False
    reading_rows = False
    frag_column = None

    for raw in log.splitlines():
        line = raw.strip()
        if "Game status:" in line:
            # Only complete games; periodic 'minutes remaining' snapshots do
            # not count, nor do partially played games.
            awaiting_header = "game finished" in line.casefold()
            reading_rows = False
            frag_column = None
            continue

        if awaiting_header and line.startswith("cn ") and " name " in (" " + line + " "):
            columns = line.split()
            # Two supported scoreboard schemas: with or without 'flag'.
            if columns[:2] == ["cn", "name"] and "frag" in columns:
                frag_column = columns.index("frag") - 2
                if frag_column in (0, 1):
                    reading_rows = True
            awaiting_header = False
            continue

        if not reading_rows:
            continue

        # The final columns are numeric stats and role/host. Parse from the
        # right so player nicknames may contain spaces.
        if frag_column == 0:
            match = re.match(
                r"^\\d+\\s+(.+?)\\s+(-?\\d+)\\s+(-?\\d+)\\s+\\d+\\s+\\S+\\s+\\S+$",
                line,
            )
            if match:
                rows.append((match.group(1), int(match.group(2))))
        else:
            match = re.match(
                r"^\\d+\\s+(.+?)\\s+(-?\\d+)\\s+(-?\\d+)\\s+(-?\\d+)\\s+\\d+\\s+\\S+\\s+\\S+$",
                line,
            )
            if match:
                rows.append((match.group(1), int(match.group(3))))

        if not match:
            reading_rows = False

    return merge_scores(rows)


PARSERS = {
    "xonotic": parse_xonotic,
    "assaultcube": parse_assaultcube,
    "openarena": parse_openarena,
}


def build(paths: dict[str, Path], output: Path, excluded_names: dict[str, set[str]] | None = None) -> dict:
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
        if game == "openarena":
            players = parse_openarena(text, (excluded_names or {}).get(game))
        else:
            players = PARSERS[game](text)
        games[game] = {
            "label": "Frags" if game == "assaultcube" else "Score",
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
        # Nginx must be able to read the freshly replaced file. NamedTemporaryFile
        # defaults to 0600, which previously caused HTTP 403 after each update.
        os.chmod(temp_path, 0o644)
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
