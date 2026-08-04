"""PreToolUse:Bash hook — production guardrail for the Memoryful workspace.

Claude Code pipes the pending tool call to this script as JSON on stdin and reads
a decision back as JSON on stdout. Printing nothing means "no opinion, carry on".

    DENY  -> blocked outright, no prompt shown
    ASK   -> destructive but legitimate; a human has to confirm
"""

from __future__ import annotations

import json
import re
import sys

Rule = tuple[re.Pattern[str], str]


def rules(*pairs: tuple[str, str]) -> list[Rule]:
    return [(re.compile(p, re.IGNORECASE), why) for p, why in pairs]


DENY: list[Rule] = rules(
    # .env.prod itself is NOT restricted — it holds non-secret prod config and is
    # meant to be edited alongside .env.local. Only *deploying* it is off limits.
    (r"docker-compose\.vm\.yml", "starts the production VM stack"),
    (r"deploy-app\.sh", "runs the production deploy"),
    (r"cos-swap-startup\.sh", "runs a production VM startup script"),
    (r"\bgcloud\s+(compute|run|secrets|storage\s+rm)", "mutates GCP production resources"),
    (r"neon\.tech|BACKUP_SOURCE_URL", "points at the production Neon database"),
    # The bare .env holds only BACKUP_SOURCE_URL — the prod Neon connection string.
    # It is host-tooling config for manage_backup.py and must never reach compose.
    (r"--env-file[= ]\.env(\s|$)", "hands the bare .env (prod Neon URL) to compose"),
)

ASK: list[Rule] = rules(
    (
        r"docker\s+compose[^\n]*\bdown\b[^\n]*\s-v\b",
        "deletes every local volume — the DB restores itself on next up, but MinIO and "
        "any pulled Ollama model do not",
    ),
    (r"\bdocker\s+volume\s+rm\b", "deletes a Docker volume"),
    (r"manage_backup\.py\s+backup", "connects to the production database to take a dump"),
    (r"\bgit\s+(commit|push)\b", "writes to git history"),
)

LOCAL_HINT = (
    "For local work use: docker compose -p memoryful --env-file .env.local "
    "-f docker/docker-compose.local.yml ..."
)


def respond(decision: str, why: str) -> None:
    tail = (
        f"Production changes are made by a human, never by an agent. {LOCAL_HINT}"
        if decision == "deny"
        else "Confirm if that is what you want."
    )
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": decision,
                    "permissionDecisionReason": (
                        f"protect_prod.py: this command {why}. {tail}"
                    ),
                }
            }
        )
    )


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return  # A malformed payload must never wedge the session.

    command: str = payload.get("tool_input", {}).get("command", "")

    for ruleset, decision in ((DENY, "deny"), (ASK, "ask")):
        for pattern, why in ruleset:
            if pattern.search(command):
                respond(decision, why)
                return


if __name__ == "__main__":
    main()
