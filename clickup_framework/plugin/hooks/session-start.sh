#!/usr/bin/env bash
# SessionStart hook for the nutcracker plugin.
#
# Force-loads the using-cum-planning routing skill into every session's
# context, the same way superpowers force-loads using-superpowers. Adapted
# from superpowers' hooks/session-start (Claude Code output shape only --
# nutcracker doesn't ship the Cursor/Copilot branches superpowers carries).

set -euo pipefail

# Resolve the plugin root from this script's own location rather than
# trusting CLAUDE_PLUGIN_ROOT -- works the same whether invoked by the hook
# runner or by hand in a test.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# A missing/unreadable skill file must NOT break session start: fall back to
# an error string that still gets wrapped in valid JSON below.
skill_content=$(cat "${PLUGIN_ROOT}/skills/using-cum-planning/SKILL.md" 2>&1 || echo "Error reading using-cum-planning skill")

# Escape for embedding in a JSON string. Each ${s//old/new} is one pass.
escape_for_json() {
    local s="$1"
    s="${s//\\/\\\\}"
    s="${s//\"/\\\"}"
    s="${s//$'\n'/\\n}"
    s="${s//$'\r'/\\r}"
    s="${s//$'\t'/\\t}"
    printf '%s' "$s"
}

escaped=$(escape_for_json "$skill_content")
context="<IMPORTANT>\nYou have nutcracker: hierarchical task planning backed by ClickUp via the cum CLI.\n\n**Below is the full content of your 'nutcracker:using-cum-planning' skill. For all other nutcracker skills, use the Skill tool:**\n\n${escaped}\n</IMPORTANT>"

# printf with %s keeps any '%' in the content literal (it's an argument, not
# part of the format string). Avoids a heredoc, which hangs on bash 5.3+.
printf '{\n  "hookSpecificOutput": {\n    "hookEventName": "SessionStart",\n    "additionalContext": "%s"\n  }\n}\n' "$context"

exit 0
