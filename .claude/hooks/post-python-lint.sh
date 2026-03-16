#!/usr/bin/env bash
set -euo pipefail

# PostToolUse Hook: Ruff auto-fix + format on Python file edits
# Returns diagnostics via hookSpecificOutput.additionalContext

input="$(cat)"
file="$(jq -r '.tool_input.file_path // .tool_input.path // empty' <<< "$input")"

# Only process Python files
case "$file" in
  *.py) ;;
  *) exit 0 ;;
esac

# Skip if file doesn't exist (e.g., deleted)
[ -f "$file" ] || exit 0

# Auto-fix then format
uv run ruff check --fix --quiet "$file" 2>/dev/null || true
uv run ruff format --quiet "$file" 2>/dev/null || true

# Report remaining violations
diag=""

ruff_diag="$(uv run ruff check "$file" 2>&1 | head -20)"
[ -n "$ruff_diag" ] && diag="[ruff]\n$ruff_diag"

mypy_diag="$(uv run mypy "$file" --no-error-summary 2>&1 | grep -v "^Success" | head -20)"
[ -n "$mypy_diag" ] && diag="$diag\n[mypy]\n$mypy_diag"

if [ -n "$diag" ]; then
  jq -Rn --arg msg "$diag" '{
    hookSpecificOutput: {
      hookEventName: "PostToolUse",
      additionalContext: $msg
    }
  }'
fi
