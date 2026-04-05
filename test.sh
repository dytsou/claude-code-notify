#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
NOTIFY="$SCRIPT_DIR/src/notify.py"

echo "claude-code-notify — functional test"
echo "======================================"
echo ""

echo "A notification will appear with Approve / Reject / Ask in Terminal buttons."
echo "Content will be summarized via: $(which claude 2>/dev/null || echo 'claude not found — falling back to raw command')"
echo ""

PAYLOAD='{"hook_event_name":"PermissionRequest","tool_name":"Bash","tool_input":{"command":"[TEST] git push origin main"}}'

OUTPUT="$(echo "$PAYLOAD" | python3 "$NOTIFY")"

echo "Result from notify.py:"
echo ""

if [ -z "$OUTPUT" ]; then
    echo "  (no output) → 'Ask in Terminal' was clicked, notification timed out, or"
    echo "               notification was dismissed. Claude Code would show its"
    echo "               normal terminal prompt."
else
    echo "$OUTPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
decision = data.get('hookSpecificOutput', {}).get('decision', {})
behavior = decision.get('behavior', '?')
if behavior == 'allow':
    print('  ✓ Approved — Claude Code would proceed with the action.')
elif behavior == 'deny':
    msg = decision.get('message', '')
    print(f'  ✗ Rejected — Claude Code would be denied. ({msg})')
else:
    print(f'  ? Unknown decision: {data}')
"
fi

echo ""
echo "Test complete."
