"""Run with: python -m unittest discover -s tests -v"""
import json
from pathlib import Path
import tempfile
import unittest

from scripts.build_leaderboards import (
    build, parse_assaultcube, parse_openarena, parse_xonotic,
)


class ParserTests(unittest.TestCase):
    def test_xonotic_completed_matches_and_colon_in_name(self):
        log = (
            ":scores:dm_map:120\n"
            ":player:4:2:120:1:Lex:NL\n"
            ":player:2:4:120:1:Guest\n"
            ":end\n"
            ":scores:dm_map:120\n"
            ":player:3:1:120:1:Lex:NL\n"
            ":end\n"
            ":scores:dm_map:120\n"
            ":player:99:0:120:1:Incomplete\n"
        )
        self.assertEqual(
            parse_xonotic(log),
            [{"name": "Lex:NL", "score": 7}, {"name": "Guest", "score": 2}]
        )

    def test_xonotic_real_uplink_labelled_score_log(self):
        labels = "score!!" + "," * 34 + "kills,deaths<,,suicides<,dmg,dmgtaken<,rounds_pl,elo" + "," * 9
        values = [0] * 51
        values[0] = 30
        values[34] = 31
        values[35] = 13
        values[37] = 1
        values[38] = 4026.613770
        values[39] = 2302.657471
        values[41] = -2
        log = (
            ":scores:dm_silentsiege:533\n"
            + ":labels:player:" + labels + "\n"
            + ":player:see-labels:" + ",".join(str(v) for v in values)
            + ":527:-1:LexusTG⚡\n"
            + ":end\n"
        )
        self.assertEqual(
            parse_xonotic(log),
            [{"name": "LexusTG⚡", "score": 30}],
        )

    def test_xonotic_ignores_eventlog_format(self):
        self.assertEqual(
            parse_xonotic(":scores:dm_map:120\n:player:see-labels:9,2:120:1:7:Lex\n:end"),
            [],
        )

    def test_openarena_end_of_match_score(self):
        log = (
            "0:00 InitGame: \\mapname\\q3dm1\n"
            "4:00 Exit: Fraglimit hit.\n"
            "4:00 score: 20 ping: 13 client: 0 Lex\n"
            "4:01 score: 20 ping: 13 client: 0 name: Lex\n"
            "4:01 score: -2 ping: 20 client: 1 name: Guest\n"
            "5:00 InitGame: \\mapname\\q3dm2\n"
            "8:00 Exit: Timelimit hit.\n"
            "8:00 score: 10 ping: 13 client: 0 name: Lex\n"
        )
        self.assertEqual(
            parse_openarena(log),
            [{"name": "Lex", "score": 30}, {"name": "Guest", "score": -2}],
        )

    def test_assaultcube_frag_events_only(self):
        log = (
            "[192.0.2.42] Lex fragged Guest\n"
            "[192.0.2.42] Lex fragged Guest\n"
            "Some unrelated server message\n"
            "[192.0.2.43] Guest fragged Lex\n"
        )
        self.assertEqual(
            parse_assaultcube(log),
            [{"name": "Lex", "score": 2}, {"name": "Guest", "score": 1}],
        )

    def test_build_preserves_other_boards_and_is_repeatable(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            output = directory / "leaderboards.json"
            xlog = directory / "xonotic.log"
            xlog.write_text(":scores:dm_map:60\n:player:5:0:60:1:Lex\n:end\n")
            output.write_text(json.dumps({"games": {"assaultcube": {
                "label": "Frags", "players": [{"name": "Guest", "score": 3}]
            }}}))
            first = build({"xonotic": xlog}, output)
            second = build({"xonotic": xlog}, output)
            self.assertEqual(first["games"]["xonotic"]["players"], second["games"]["xonotic"]["players"])
            self.assertEqual(second["games"]["assaultcube"]["players"][0]["score"], 3)
            self.assertEqual(json.loads(output.read_text())["games"]["xonotic"]["players"][0]["score"], 5)

    def test_missing_log_does_not_overwrite_json(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "leaderboards.json"
            output.write_text('{"games":{}}')
            with self.assertRaises(FileNotFoundError):
                build({"xonotic": Path(folder) / "missing.log"}, output)
            self.assertEqual(output.read_text(), '{"games":{}}')


if __name__ == "__main__":
    unittest.main()
