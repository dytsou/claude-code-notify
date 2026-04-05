# claude-code-notify

Interactive approval notifications for [Claude Code](https://claude.ai/code) permission requests.

When Claude Code asks for permission to run a command or edit a file, you get a macOS notification with **Approve** and **Reject** buttons — no need to keep watching the terminal.

## How it works

- Claude Code fires a `PermissionRequest` hook before showing a permission prompt
- `src/notify.py` intercepts it and shows a native macOS notification with action buttons
- Click **Approve** → Claude proceeds immediately
- Click **Reject** → Claude is denied
- Click **Ask in Terminal** (or let it time out after 60s) → falls back to the normal Claude Code terminal prompt
- Clicking the **notification body** brings your terminal / VS Code window to the foreground

## Requirements

- macOS (Apple Silicon or Intel)
- Python 3 (pre-installed on macOS)
- [Claude Code](https://docs.anthropic.com/claude-code) installed

## Quick setup

```bash
git clone https://github.com/dytsou/claude-code-notify
cd claude-code-notify
make install
```

Then **restart Claude Code**.

`make install` will:

1. Download and install [`alerter`](https://github.com/vjeantet/alerter) (the notification backend)
2. Add a `PermissionRequest` hook to `~/.claude/settings.json` pointing at `src/presummary.py` (async) and `src/notify.py` (sync)

## Uninstall

```bash
make uninstall
```

Removes the `PermissionRequest` entry from `~/.claude/settings.json`. Does not remove `alerter`.

## Manual setup

If you already have a custom `~/.claude/settings.json` and want to add the hook manually, merge the contents of `settings-snippet.json` — replacing the paths with the absolute paths to your local `src/presummary.py` and `src/notify.py`:

```json
{
  "hooks": {
    "PermissionRequest": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 /absolute/path/to/claude-code-notify/src/notify.py",
            "timeout": 65000,
            "statusMessage": "Waiting for approval..."
          }
        ]
      }
    ]
  }
}
```

The hook must be **synchronous** (no `"async": true`) so Claude Code waits for the decision.

## Notification fallback

If `alerter` is not found, `src/notify.py` falls back to an `osascript` dialog popup. To restore inline notification buttons, re-run `./scripts/install.sh`.

## Moving the repo

If you move the repo directory, re-run `./scripts/install.sh` to update the path in `settings.json`.

## Terminal detection

`src/notify.py` detects your terminal app from `$TERM_PROGRAM` to bring the right window to focus when you click the notification body:

| `$TERM_PROGRAM`   | App activated |
| ----------------- | ------------- |
| `vscode`          | VS Code       |
| `Apple_Terminal`  | Terminal.app  |
| `iTerm.app`       | iTerm2        |
| `WarpTerminal`    | Warp          |
| `Hyper`           | Hyper         |
| _(anything else)_ | Terminal.app  |

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
