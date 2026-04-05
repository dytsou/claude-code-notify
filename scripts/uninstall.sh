#!/usr/bin/env bash
set -euo pipefail

SETTINGS="$HOME/.claude/settings.json"

echo "==> claude-code-notify uninstaller"
echo ""

if [ ! -f "$SETTINGS" ]; then
    echo "No settings.json found at $SETTINGS — nothing to do."
    exit 0
fi

python3 - "$SETTINGS" <<'PYEOF'
import sys, json

settings_path = sys.argv[1]

with open(settings_path, "r") as f:
    settings = json.load(f)

hooks = settings.get("hooks", {})

if "PermissionRequest" not in hooks:
    print("No PermissionRequest hook found — nothing to remove.")
    sys.exit(0)

del hooks["PermissionRequest"]

with open(settings_path, "w") as f:
    json.dump(settings, f, indent=2)
    f.write("\n")

print(f"Removed PermissionRequest hook from {settings_path}")
PYEOF

echo ""
echo "Done. Restart Claude Code to apply."
