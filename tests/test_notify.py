"""CI-safe tests for notify.py (GUI paths mocked)."""

import json
import sys
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

# Repo root on PYTHONPATH (set in CI and local: PYTHONPATH=. python3 -m unittest ...)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import notify  # noqa: E402


class TestNotifyMain(unittest.TestCase):
    def test_empty_stdin(self):
        with patch.object(sys, "stdin", StringIO("")):
            with self.assertRaises(SystemExit) as ctx:
                notify.main()
            self.assertEqual(ctx.exception.code, 0)

    def test_non_permission_event_exits_silently(self):
        payload = {"hook_event_name": "Other"}
        with patch.object(sys, "stdin", StringIO(json.dumps(payload))):
            out = StringIO()
            with patch.object(sys, "stdout", out):
                with self.assertRaises(SystemExit) as ctx:
                    notify.main()
            self.assertEqual(ctx.exception.code, 0)
            self.assertEqual(out.getvalue(), "")

    def test_invalid_json_exits_zero(self):
        with patch.object(sys, "stdin", StringIO("not json")):
            out = StringIO()
            with patch.object(sys, "stdout", out):
                with self.assertRaises(SystemExit) as ctx:
                    notify.main()
            self.assertEqual(ctx.exception.code, 0)
            self.assertEqual(out.getvalue(), "")

    def test_allow_emits_json(self):
        payload = {
            "hook_event_name": "PermissionRequest",
            "tool_name": "Bash",
            "tool_input": {"command": "ls"},
        }
        with patch.object(sys, "stdin", StringIO(json.dumps(payload))):
            with patch("notify.show_permission_notification", return_value="allow"):
                out = StringIO()
                with patch.object(sys, "stdout", out):
                    with self.assertRaises(SystemExit) as ctx:
                        notify.main()
                self.assertEqual(ctx.exception.code, 0)
        data = json.loads(out.getvalue().strip())
        self.assertEqual(
            data["hookSpecificOutput"]["decision"]["behavior"],
            "allow",
        )

    def test_deny_emits_json(self):
        payload = {
            "hook_event_name": "PermissionRequest",
            "tool_name": "Bash",
            "tool_input": {"command": "ls"},
        }
        with patch.object(sys, "stdin", StringIO(json.dumps(payload))):
            with patch("notify.show_permission_notification", return_value="deny"):
                out = StringIO()
                with patch.object(sys, "stdout", out):
                    with self.assertRaises(SystemExit) as ctx:
                        notify.main()
                self.assertEqual(ctx.exception.code, 0)
        data = json.loads(out.getvalue().strip())
        self.assertEqual(
            data["hookSpecificOutput"]["decision"]["behavior"],
            "deny",
        )

    def test_no_decision_no_stdout(self):
        payload = {
            "hook_event_name": "PermissionRequest",
            "tool_name": "Bash",
            "tool_input": {"command": "ls"},
        }
        with patch.object(sys, "stdin", StringIO(json.dumps(payload))):
            with patch("notify.show_permission_notification", return_value=None):
                out = StringIO()
                with patch.object(sys, "stdout", out):
                    with self.assertRaises(SystemExit) as ctx:
                        notify.main()
                self.assertEqual(ctx.exception.code, 0)
                self.assertEqual(out.getvalue(), "")


class TestShowPermissionNotification(unittest.TestCase):
    def test_non_darwin_returns_none(self):
        with patch("notify.platform.system", return_value="Linux"):
            r = notify.show_permission_notification("Bash", "ls")
            self.assertIsNone(r)


if __name__ == "__main__":
    unittest.main()
