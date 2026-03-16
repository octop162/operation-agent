#!/usr/bin/env bash
set -euo pipefail

# PreToolUse Hook: Protect config files and .env from agent edits
# Exit 2 = block the tool call, stderr = reason fed back to agent

input="$(cat)"
file="$(jq -r '.tool_input.file_path // .tool_input.path // empty' <<< "$input")"

[ -z "$file" ] && exit 0

# Block .env files (secrets)
case "$file" in
  *.env.example)
    # テンプレートファイルは編集可能
    ;;
  *.env|*.env.*|*/.env|*/.env.*)
    echo "BLOCKED: $file is an environment file containing secrets. Never edit .env files directly." >&2
    exit 2
    ;;
esac

# Protect linter/build config files from agent modification
PROTECTED="pyproject.toml lefthook.yml lefthook-local.yml .claude/settings.json"
basename_file="$(basename "$file")"
for p in $PROTECTED; do
  basename_p="$(basename "$p")"
  if [ "$basename_file" = "$basename_p" ]; then
    echo "BLOCKED: $file is a protected config file. Fix the code, not the config." >&2
    exit 2
  fi
done
