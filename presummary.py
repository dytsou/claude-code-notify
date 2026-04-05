#!/usr/bin/env python3
"""
claude-code-notify — Async pre-summarizer for PermissionRequest.

Runs concurrently with notify.py (as an async hook). Calls `claude -p` to
produce a one-sentence summary of the action and writes it to a temp cache
file. notify.py polls that file so it can show the summary the moment it
arrives instead of waiting for its own blocking call.
"""

import sys
import json
import subprocess
import hashlib
import os

CACHE_DIR = "/tmp"
CACHE_PREFIX = ".claude-notify-"


def _cache_path(tool_name, command):
    key = hashlib.md5(f"{tool_name}|{command[:400]}".encode()).hexdigest()
    return os.path.join(CACHE_DIR, f"{CACHE_PREFIX}{key}.txt")


def _summarize(tool_name, raw_command):
    prompt = (
        "Summarize the following Claude Code permission request in one short sentence "
        "(12 words max). Be direct — no preamble, no quotes.\n"
        f"Tool: {tool_name}\n"
        f"Input: {raw_command}"
    )
    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--output-format", "text"],
            input="",
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def main():
    try:
        stdin_content = sys.stdin.read().strip()
        if not stdin_content:
            sys.exit(0)

        data = json.loads(stdin_content)
        if data.get("hook_event_name") != "PermissionRequest":
            sys.exit(0)

        tool_name = data.get("tool_name", "Unknown Tool")
        tool_input = data.get("tool_input", {})
        command = (
            tool_input.get("command")
            or tool_input.get("description")
            or str(tool_input)[:200]
        ) or ""

        summary = _summarize(tool_name, command)
        if summary:
            path = _cache_path(tool_name, command)
            with open(path, "w", encoding="utf-8") as f:
                f.write(summary)
    except Exception:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
