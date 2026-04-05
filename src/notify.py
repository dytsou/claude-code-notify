#!/usr/bin/env python3
"""
claude-code-notify — Permission request notification hook for Claude Code.

Reads a Claude Code PermissionRequest hook event from stdin and shows an
interactive macOS notification with inline Approve / Reject buttons.
Outputs the user's decision as JSON so Claude Code can proceed without
requiring terminal focus.

Install: ./scripts/install.sh
"""

import sys
import json
import subprocess
import platform
import hashlib
import os
import time

CACHE_DIR = "/tmp"
CACHE_PREFIX = ".claude-notify-"
CACHE_MAX_AGE = 30  # seconds — ignore stale entries


# ── Cache helpers (shared with presummary.py) ────────────────────────────────

def _cache_path(tool_name, command):
    key = hashlib.md5(f"{tool_name}|{command[:400]}".encode()).hexdigest()
    return os.path.join(CACHE_DIR, f"{CACHE_PREFIX}{key}.txt")


def _poll_cache(tool_name: str, command: str, timeout: float = 5.0):
    """
    Poll the cache file written by presummary.py for up to `timeout` seconds.
    Returns the summary string, or None if not ready in time.
    """
    path = _cache_path(tool_name, command)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if os.path.exists(path):
            try:
                age = time.monotonic() - os.path.getmtime(path)
                if age < CACHE_MAX_AGE:
                    with open(path, encoding="utf-8") as f:
                        summary = f.read().strip()
                    os.unlink(path)  # consume — one-shot
                    return summary or None
            except Exception:
                break
        time.sleep(0.1)
    try:
        os.unlink(path)
    except Exception:
        pass
    return None


# ── Helpers ──────────────────────────────────────────────────────────────────

def _show_via_alerter(alerter_path, tool_name, display_command):
    """Show inline-button notification via alerter. Returns 'allow', 'deny', or None."""
    message = f"[{tool_name}] {display_command}"
    try:
        result = subprocess.run(
            [
                alerter_path,
                "--title",       "Claude Code \u2014 Approval Needed",
                "--message",     message,
                "--actions",     "Approve,Reject",
                "--close-label", "Ask in Terminal",
                "--timeout",     "60",
                "--ignore-dnd",
                "--json",
            ],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=65,
        )
        data = json.loads(result.stdout)
        if data.get("activationType") == "actionClicked":
            value = data.get("activationValue", "")
            if value == "Approve":
                return "allow"
            if value == "Reject":
                return "deny"
        # contentsClicked → app activated; fall through to terminal prompt
        return None
    except Exception:
        return None


def _show_via_osascript(tool_name, display_command):
    """Fallback: blocking osascript dialog. Returns 'allow', 'deny', or None."""
    dialog_message = f"Tool: {tool_name}\n\nAction: {display_command}"
    script = (
        "try\n"
        f"  set r to display dialog {json.dumps(dialog_message)} "
        "with title \"Claude Code \u2014 Approval Needed\" "
        "buttons {\"Reject\", \"Ask in Terminal\", \"Approve\"} "
        "default button \"Approve\" "
        "giving up after 60\n"
        "  if gave up of r then\n"
        "    return \"timeout\"\n"
        "  end if\n"
        "  return button returned of r\n"
        "on error\n"
        "  return \"error\"\n"
        "end try"
    )
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=65,
        )
        button = result.stdout.strip()
        if button == "Approve":
            return "allow"
        if button == "Reject":
            return "deny"
        return None
    except Exception:
        return None


def show_permission_notification(tool_name, command):
    """
    Show a blocking notification with Approve / Reject / Ask-in-Terminal buttons.

    Returns:
        'allow'  — user clicked Approve
        'deny'   — user clicked Reject
        None     — dismissed, timed out, or "Ask in Terminal" clicked
                   (Claude Code will show its normal terminal prompt)
    """
    if platform.system() != "Darwin":
        return None

    raw = command or "(no details)"

    # Wait for presummary.py (async hook) to write the cache; fall back to raw
    summary = _poll_cache(tool_name, raw) or raw
    display_command = summary[:200] + "\u2026" if len(summary) > 200 else summary

    alerter_path = subprocess.run(
        ["which", "alerter"], capture_output=True, text=True
    ).stdout.strip()

    if alerter_path:
        return _show_via_alerter(alerter_path, tool_name, display_command)
    else:
        return _show_via_osascript(tool_name, display_command)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    """Read Claude Code hook JSON from stdin and handle PermissionRequest."""
    try:
        stdin_content = sys.stdin.read().strip()
        if not stdin_content:
            sys.exit(0)

        data = json.loads(stdin_content)
        event = data.get("hook_event_name", "")

        if event != "PermissionRequest":
            sys.exit(0)

        tool_name = data.get("tool_name", "Unknown Tool")
        tool_input = data.get("tool_input", {})
        command = (
            tool_input.get("command")
            or tool_input.get("description")
            or str(tool_input)[:200]
        )

        decision = show_permission_notification(tool_name, command)

        if decision == "allow":
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PermissionRequest",
                    "decision": {"behavior": "allow"},
                }
            }))
        elif decision == "deny":
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PermissionRequest",
                    "decision": {"behavior": "deny", "message": "Rejected via notification"},
                }
            }))
        # else: None → exit 0, no output → Claude Code shows terminal prompt

        sys.exit(0)

    except json.JSONDecodeError:
        sys.exit(0)
    except Exception:
        sys.exit(0)


if __name__ == "__main__":
    main()
