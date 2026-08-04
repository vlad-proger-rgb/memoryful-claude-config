"""PreToolUse hook — let Claude file into its own TickTick column without a prompt.

Permission rules in settings.json match on tool *name* only, so they can't express
"writing here is fine, writing there is not". This hook reads the arguments and
decides.

Contract: task creation is auto-approved only when every task in the call is
addressed to the Claude Backlog column AND carries the `claude` tag. Anything
else prints nothing, which is not an approval — it falls through to the normal
permission rules, where every TickTick write sits on `ask`.

Deliberately narrow: only creation is in scope. Updating, moving, completing or
deleting a task would need the task's current column to judge, which means a
round-trip this hook has no business making. Those keep prompting.
"""

from __future__ import annotations

import json
import sys

CLAUDE_COLUMN_ID = "6a71069d8f08cc64fe195c59"
REQUIRED_TAG = "claude"
CREATE_TOOLS = {"mcp__ticktick__create_task", "mcp__ticktick__batch_add_tasks"}


def tasks_in(tool_input: dict) -> list[dict]:
    """Both tools carry tasks, but shaped differently."""
    if isinstance(tool_input.get("tasks"), list):
        return [t for t in tool_input["tasks"] if isinstance(t, dict)]
    if isinstance(tool_input.get("task"), dict):
        return [tool_input["task"]]
    # create_task may take the fields flat rather than nested.
    return [tool_input] if "title" in tool_input else []


def in_scope(task: dict) -> bool:
    tags = task.get("tags") or []
    return (
        task.get("columnId") == CLAUDE_COLUMN_ID
        and isinstance(tags, list)
        and REQUIRED_TAG in [str(t).lower() for t in tags]
    )


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return

    if payload.get("tool_name") not in CREATE_TOOLS:
        return

    tasks = tasks_in(payload.get("tool_input") or {})
    if not tasks or not all(in_scope(t) for t in tasks):
        return  # Silence is not consent — the `ask` rule still applies.

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "allow",
                    "permissionDecisionReason": (
                        f"ticktick_scope.py: {len(tasks)} task(s), all tagged "
                        f"`{REQUIRED_TAG}` and addressed to the Claude Backlog column. "
                        "Triage queue only — nothing lands in a working column."
                    ),
                }
            }
        )
    )


if __name__ == "__main__":
    main()
    sys.exit(0)
