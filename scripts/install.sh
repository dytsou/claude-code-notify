#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NOTIFY_SCRIPT="$REPO_ROOT/src/notify.py"
SETTINGS="$HOME/.claude/settings.json"

echo "==> claude-code-notify installer"
echo ""

# ── 1. Verify Python 3 ────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo "Error: python3 not found. Install Python 3 first." >&2
    exit 1
fi

# ── 2. Install alerter ────────────────────────────────────────────────────────
if command -v alerter &>/dev/null; then
    echo "==> alerter already installed at $(which alerter)"
else
    echo "==> Installing alerter..."

    # Determine install dir (prefer /opt/homebrew/bin on Apple Silicon)
    if [ -d "/opt/homebrew/bin" ]; then
        ALERTER_DEST="/opt/homebrew/bin/alerter"
    elif [ -d "/usr/local/bin" ]; then
        ALERTER_DEST="/usr/local/bin/alerter"
    else
        echo "Error: cannot find a suitable bin directory (/opt/homebrew/bin or /usr/local/bin)." >&2
        exit 1
    fi

    TMP_DIR="$(mktemp -d)"
    trap 'rm -rf "$TMP_DIR"' EXIT

    ALERTER_URL="https://github.com/vjeantet/alerter/releases/download/v26.5/alerter-26.5.zip"
    curl -sL "$ALERTER_URL" -o "$TMP_DIR/alerter.zip"
    unzip -o -q "$TMP_DIR/alerter.zip" -d "$TMP_DIR"

    cp "$TMP_DIR/alerter" "$ALERTER_DEST"
    chmod +x "$ALERTER_DEST"
    xattr -d com.apple.quarantine "$ALERTER_DEST" 2>/dev/null || true

    echo "==> alerter installed at $ALERTER_DEST"
fi

# ── 3. Ensure ~/.claude/settings.json exists ──────────────────────────────────
mkdir -p "$HOME/.claude"
if [ ! -f "$SETTINGS" ]; then
    echo '{}' > "$SETTINGS"
    echo "==> Created $SETTINGS"
fi

# ── 4. Inject PermissionRequest hooks ────────────────────────────────────────
PRESUMMARY_SCRIPT="$REPO_ROOT/src/presummary.py"

python3 - "$SETTINGS" "$PRESUMMARY_SCRIPT" "$NOTIFY_SCRIPT" <<'PYEOF'
import sys, json

settings_path    = sys.argv[1]
presummary_path  = sys.argv[2]
notify_path      = sys.argv[3]

with open(settings_path, "r") as f:
    settings = json.load(f)

hooks = settings.setdefault("hooks", {})
if hooks.get("PermissionRequest"):
    print(f"  Warning: replacing existing PermissionRequest hook in {settings_path}")

hooks["PermissionRequest"] = [{"hooks": [
    {
        "type":    "command",
        "command": f"python3 {presummary_path}",
        "timeout": 12000,
        "async":   True,
    },
    {
        "type":          "command",
        "command":       f"python3 {notify_path}",
        "timeout":       65000,
        "statusMessage": "Waiting for approval...",
    },
]}]

with open(settings_path, "w") as f:
    json.dump(settings, f, indent=2)
    f.write("\n")

print(f"  Patched {settings_path}")
print(f"  presummary: python3 {presummary_path}  (async)")
print(f"  notify:     python3 {notify_path}")
PYEOF

echo ""
echo "Done! Restart Claude Code to activate approval notifications."
echo ""
echo "When Claude Code requests a permission you will see a notification with:"
echo "  [Approve]  — allow the action"
echo "  [Reject]   — deny the action"
echo "  [Ask in Terminal] — fall back to the Claude Code terminal prompt"
