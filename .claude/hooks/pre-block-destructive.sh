#!/usr/bin/env bash
set -euo pipefail

# PreToolUse Hook: Block destructive bash commands

input="$(cat)"
command="$(jq -r '.tool_input.command // empty' <<< "$input")"

[ -z "$command" ] && exit 0

# Strip heredoc bodies and quoted strings to avoid false positives
# Extract only the command skeleton (outside of heredocs and $(...) with heredocs)
cmd_skeleton="$(echo "$command" | sed '/<<.*EOF/,/^EOF/d')"

# Block destructive patterns
if echo "$cmd_skeleton" | grep -qE '(rm\s+-rf\s+[/~]|rm\s+-rf\s+\.\s|git\s+push\s+--force|git\s+reset\s+--hard|git\s+clean\s+-f)'; then
  echo "BLOCKED: Destructive command detected." >&2
  exit 2
fi

# Block --no-verify (bypass pre-commit hooks)
if echo "$cmd_skeleton" | grep -qE '(git\s+commit|git\s+push).*--no-verify'; then
  echo "BLOCKED: --no-verify is not allowed. Fix the issue instead of bypassing hooks." >&2
  exit 2
fi
