#!/usr/bin/env python3
"""Poll configured game log files via SSH and refresh static leaderboards.json.

Only games with enabled=true are contacted. If a game is unavailable, its
previous leaderboard is preserved. No database or external Python packages.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

try:
    from .build_leaderboards import PARSERS, build  # imported from tests
except ImportError:
    from build_leaderboards import PARSERS, build   # run as a script


def source_is_valid(game: str, source: object) -> bool:
    """Validate source configuration before passing values to SSH."""
    if game not in PARSERS or not isinstance(source, dict):
        return False
    host = source.get("host")
    user = source.get("user")
    remote_log = source.get("remote_log")
    identity = source.get("identity_file")
    if not all(isinstance(value, str) and value for value in
               (host, user, remote_log, identity)):
        return False
    # Reject options / whitespace: prevent ssh argument and remote command injection.
    import re
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.:-]*", host):
        return False
    if not re.fullmatch(r"[a-z_][a-z0-9_-]*", user):
        return False
    if not remote_log.startswith("/") or not re.fullmatch(r"/[A-Za-z0-9_./-]+", remote_log):
        return False
    if not identity.startswith("/"):
        return False
    return True


def fetch_log(source: dict, destination: Path) -> None:
    """Fetch through restricted, key-authenticated SSH and save only on success."""
    # Remote path is restricted to safe characters in source_is_valid.
    remote_command = "cat " + source["remote_log"]
    command = [
        "ssh", "-T", "-i", source["identity_file"],
        "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=yes",
        "-o", "ConnectTimeout=8",
        "-o", "ConnectionAttempts=1",
        source["user"] + "@" + source["host"],
        remote_command,
    ]
    with destination.open("wb") as output:
        subprocess.run(
            command, stdout=output, check=True, timeout=60,
            stderr=subprocess.PIPE,
        )


def run(config_path: Path) -> int:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(config.get("games"), dict):
        raise ValueError("Configuration must contain a games object")
    output = Path(config["output"])
    if not output.is_absolute():
        raise ValueError("Output must be an absolute file path")

    paths: dict[str, Path] = {}
    failed = []
    with tempfile.TemporaryDirectory(prefix="uplink-logs-") as folder:
        for game, source in config["games"].items():
            if not isinstance(source, dict) or source.get("enabled") is not True:
                continue
            if not source_is_valid(game, source):
                print(f"Invalid source configuration: {game}", file=sys.stderr)
                failed.append(game)
                continue
            destination = Path(folder) / (game + ".log")
            try:
                fetch_log(source, destination)
                paths[game] = destination
                print(f"{game}: log received ({destination.stat().st_size} bytes)")
            except (subprocess.SubprocessError, OSError) as error:
                # Never output stdout or stderr containing raw player data.
                print(f"{game}: fetch failed ({type(error).__name__})", file=sys.stderr)
                failed.append(game)

        if paths:
            result = build(paths, output)
            for game in paths:
                print(f"{game}: {len(result['games'][game]['players'])} player(s)")
        else:
            print("No logs fetched; existing scores left unchanged", file=sys.stderr)
            return 1

    return 1 if failed else 0


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument(
        "--config", type=Path,
        default=Path("/var/www/html/config/leaderboard-sources.json"),
    )
    arguments = cli.parse_args()
    try:
        sys.exit(run(arguments.config))
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as error:
        print(f"Updater stopped: {error}", file=sys.stderr)
        sys.exit(1)
