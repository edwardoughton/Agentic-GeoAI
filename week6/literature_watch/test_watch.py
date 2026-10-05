"""Offline checks for the persistence behaviors the teaching example relies on."""
import json
from pathlib import Path
import subprocess
import sys
import uuid
import unittest

ROOT = Path(__file__).resolve().parent


class WatchTests(unittest.TestCase):
    def test_repeat_run_and_scope_change(self):
        directory = str(ROOT / "demo_output" / ("test-" + uuid.uuid4().hex))
        target = Path(directory)
        target.mkdir(parents=True)
        command = [sys.executable, str(ROOT / "watch.py"), "--mode", "fixture", "--config",
                   str(ROOT / "watch_config.json"), "--output", directory, "--today", "2026-10-05"]
        subprocess.run(command, check=True, capture_output=True)
        subprocess.run(command, check=True, capture_output=True)
        state = json.loads((target / "state/fixture_state.json").read_text())
        self.assertEqual(len(state["events"]), 1)
        self.assertEqual(state["runs"][-1]["new_events"], 0)
        self.assertFalse((target / "state/state.json").exists())
        self.assertIn("SYNTHETIC", (target / "docs/index.html").read_text())
        config = json.loads((ROOT / "watch_config.json").read_text())
        config["arxiv_query"] = "different scope"
        custom = target / "config.json"
        custom.write_text(json.dumps(config))
        command[command.index("--config") + 1] = str(custom)
        failed = subprocess.run(command, capture_output=True)
        self.assertNotEqual(failed.returncode, 0)
        unchanged = json.loads((target / "state/fixture_state.json").read_text())
        self.assertEqual(len(unchanged["runs"]), 2)


if __name__ == "__main__":
    unittest.main()
