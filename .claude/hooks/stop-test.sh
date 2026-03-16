#!/usr/bin/env bash
set -euo pipefail

# Stop Hook: Run pytest before agent declares completion
# Prevents agent from claiming "done" without passing tests

# Guard against infinite loop: skip if already running
if [ "${STOP_HOOK_ACTIVE:-}" = "1" ]; then
  exit 0
fi
export STOP_HOOK_ACTIVE=1

# Only run if tests directory exists
if [ ! -d "tests" ]; then
  exit 0
fi

# Only run if there are test files
test_files=$(find tests -name "test_*.py" -o -name "*_test.py" 2>/dev/null | head -1)
if [ -z "$test_files" ]; then
  exit 0
fi

result="$(uv run pytest tests/ --tb=short -q 2>&1 | tail -30)"
exit_code=${PIPESTATUS[0]}

if [ "$exit_code" -ne 0 ]; then
  jq -Rn --arg msg "Tests FAILED. Fix before completing:\n$result" '{
    hookSpecificOutput: {
      hookEventName: "Stop",
      additionalContext: $msg
    }
  }'
  exit 1
fi
