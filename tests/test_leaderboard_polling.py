"""Tests for the SSH leaderboard poller. Run: python3 -m unittest discover -s tests -v"""
import json
from pathlib import Path
import tempfile
from unittest import TestCase, mock

from scripts import poll_leaderboards
from scripts.build_leaderboards import build


class PollerTests(TestCase):
    def source(self, enabled=True):
        return {
            "enabled": enabled,
            "host": "192.168.222.100",
            "user": "uplinklogs",
            "identity_file": "/root/.ssh/id_ed25519_uplink",
            "remote_log": "/home/xonotic/.xonotic/data/data/scores.log"
        }

    def test_validate_source(self):
        self.assertTrue(poll_leaderboards.source_is_valid("xonotic", self.source()))
        dangerous = self.source()
        dangerous["remote_log"] = "/tmp/log;touch /tmp/pwned"
        self.assertFalse(poll_leaderboards.source_is_valid("xonotic", dangerous))
        self.assertFalse(poll_leaderboards.source_is_valid("unknown", self.source()))

    def test_fetch_failure_keeps_previous_data(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            output = root / "leaderboards.json"
            old = {"games": {"xonotic": {"label": "Score",
                    "players": [{"name": "Lex", "score": 30}]}}}
            output.write_text(json.dumps(old), encoding="utf-8")
            config_path = root / "sources.json"
            config_path.write_text(json.dumps({
                "output": str(output),
                "games": {"xonotic": self.source()}
            }), encoding="utf-8")
            with mock.patch.object(poll_leaderboards, "fetch_log", side_effect=OSError("offline")):
                self.assertEqual(poll_leaderboards.run(config_path), 1)
            self.assertEqual(json.loads(output.read_text()), old)

    def test_success_refreshes_and_is_nginx_readable(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            output = root / "leaderboards.json"
            config_path = root / "sources.json"
            config_path.write_text(json.dumps({
                "output": str(output), "games": {"xonotic": self.source()}
            }), encoding="utf-8")

            def fake_fetch(_source, destination):
                destination.write_text(
                    ":scores:dm_map:120\n:player:5:1:120:1:Lex\n:end\n",
                    encoding="utf-8"
                )

            with mock.patch.object(poll_leaderboards, "fetch_log", side_effect=fake_fetch):
                self.assertEqual(poll_leaderboards.run(config_path), 0)
            self.assertEqual(json.loads(output.read_text())["games"]["xonotic"]["players"][0]["score"], 5)
            self.assertEqual(output.stat().st_mode & 0o444, 0o444)
            # Repeat refresh; should not duplicate scores.
            with mock.patch.object(poll_leaderboards, "fetch_log", side_effect=fake_fetch):
                self.assertEqual(poll_leaderboards.run(config_path), 0)
            self.assertEqual(json.loads(output.read_text())["games"]["xonotic"]["players"][0]["score"], 5)


if __name__ == "__main__":
    import unittest
    unittest.main()
