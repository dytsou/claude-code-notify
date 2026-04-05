"""CI-safe tests for presummary.py."""

import json
import sys
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import presummary  # noqa: E402


class TestPresummaryMain(unittest.TestCase):
    def test_empty_stdin(self):
        with patch.object(sys, "stdin", StringIO("")):
            with self.assertRaises(SystemExit) as ctx:
                presummary.main()
            self.assertEqual(ctx.exception.code, 0)

    def test_wrong_event_no_file(self):
        payload = {"hook_event_name": "Other"}
        with patch.object(sys, "stdin", StringIO(json.dumps(payload))):
            with self.assertRaises(SystemExit) as ctx:
                presummary.main()
            self.assertEqual(ctx.exception.code, 0)

    def test_empty_summary_skips_cache_write(self):
        payload = {
            "hook_event_name": "PermissionRequest",
            "tool_name": "Bash",
            "tool_input": {"command": "git status"},
        }
        fake_run = MagicMock()
        fake_run.stdout = ""
        fake_run.stderr = ""

        m = mock_open()
        with patch.object(sys, "stdin", StringIO(json.dumps(payload))):
            with patch("presummary.subprocess.run", return_value=fake_run):
                with patch("builtins.open", m):
                    with self.assertRaises(SystemExit) as ctx:
                        presummary.main()
                    self.assertEqual(ctx.exception.code, 0)
                    m.assert_not_called()

    def test_summary_writes_cache(self):
        payload = {
            "hook_event_name": "PermissionRequest",
            "tool_name": "Bash",
            "tool_input": {"command": "git status"},
        }
        fake_run = MagicMock()
        fake_run.stdout = "Short summary line"
        fake_run.stderr = ""

        m = mock_open()
        with patch.object(sys, "stdin", StringIO(json.dumps(payload))):
            with patch("presummary.subprocess.run", return_value=fake_run):
                with patch("builtins.open", m):
                    with self.assertRaises(SystemExit) as ctx:
                        presummary.main()
                    self.assertEqual(ctx.exception.code, 0)
                    m.assert_called()


if __name__ == "__main__":
    unittest.main()
