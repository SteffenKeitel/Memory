#!/bin/bash
# SessionEnd-Hook Wrapper: Lädt API-Key und ruft session_hook.py auf.
set -euo pipefail

HOOK_DIR="$HOME/.claude/hooks"

# .env laden (enthält ANTHROPIC_API_KEY)
if [ -f "$HOOK_DIR/.env" ]; then
    set -a
    source "$HOOK_DIR/.env"
    set +a
fi

exec "$HOOK_DIR/.venv/bin/python" "$HOOK_DIR/session_hook.py"
