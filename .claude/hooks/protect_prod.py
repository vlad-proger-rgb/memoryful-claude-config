"""PreToolUse:Bash hook — production guardrail for the Memoryful workspace.

Claude Code pipes the pending tool call to this script as JSON on stdin and reads
a decision back as JSON on stdout. Printing nothing means "no opinion, carry on".

    DENY  -> blocked outright, no prompt shown
    ASK   -> destructive but legitimate; a human has to confirm
    ALLOW -> proven read-only; runs without a prompt

Patterns are matched against the whole command string, so a bare filename would also
fire on `cat scripts/…`, on a grep, and on a commit message that merely names the file.
The rules below anchor on the *command word* instead: reading and describing these files
is fine, running them is not. Anything not proven to be an invocation falls through to
Claude Code's own permission prompt, since none of these scripts is on the allow-list.

ALLOW alone is matched with fullmatch, so nothing may surround it: a trailing
`; docker restart` drops through to DENY instead. Its remote grammar admits no shell
metacharacter, and LEAK is checked first, so no allowed read can carry a credential.
"""

from __future__ import annotations

import json
import re
import sys

Rule = tuple[re.Pattern[str], str]

# Start of the command, or straight after a shell separator — i.e. a command word
# rather than an argument to `cat` or a word inside a message.
CMD = r"(?:^|[\n;&|(]\s*)(?:sudo\s+)?"
# Same position, but allowing an interpreter and a directory prefix before the script.
RUN = CMD + r"(?:(?:bash|sh|zsh|source|exec)\s+)?\S*"

VM_CONTAINER = r"(?:memoryful-(?:app|mcp|nginx)|celery-worker|certbot-renew|watchtower)"

VM_READ = "|".join(
    (
        r"docker\s+ps(?:\s+-a)?",
        r"docker\s+logs(?:\s+--tail=\d{1,5})?(?:\s+--since=\d{1,4}[smhd])?\s+" + VM_CONTAINER,
        r"docker\s+inspect\s+" + VM_CONTAINER,
        r"docker\s+stats\s+--no-stream",
        r"free\s+-[mh]",
        r"df\s+-h",
        r"uptime",
    )
)

GFLAG = r"--[a-z-]+(?:=[\w.:@/-]+)?"  # --zone=…, --project=… — never a quoted value.


def rules(*pairs: tuple[str, str]) -> list[Rule]:
    return [(re.compile(p, re.IGNORECASE), why) for p, why in pairs]


ALLOW: list[Rule] = rules(
    (
        rf"gcloud\s+compute\s+instances\s+(?:describe|list)(?:\s+[\w.@-]+)?(?:\s+{GFLAG})*",
        "only reads VM metadata",
    ),
    (
        rf"gcloud\s+compute\s+ssh\s+[\w.@-]+(?:\s+{GFLAG})*"
        rf"\s+--command=(?P<q>[\"'])(?:{VM_READ})(?P=q)",
        "observes the production VM without changing it",
    ),
)

LEAK: list[Rule] = rules(
    (r"neon\.tech|BACKUP_SOURCE_URL", "points at the production Neon database"),
    (r"--env-file[= ]\.env(\s|$)", "hands the bare .env (prod Neon URL) to compose"),
)

DENY: list[Rule] = rules(
    # No rule for .env.prod on purpose: editing it is normal, only deploying it is not.
    (
        r"docker[\s-]compose\b[^\n]*?(?:-f|--file)[= ]\s*\S*docker-compose\.vm\.yml",
        "starts the production VM stack",
    ),
    (RUN + r"deploy-app\.sh", "runs the production deploy"),
    (RUN + r"cos-swap-startup\.sh", "runs a production VM startup script"),
    (CMD + r"gcloud\s+(compute|run|secrets|storage\s+rm)", "mutates GCP production resources"),
)

ASK: list[Rule] = rules(
    (
        r"docker\s+compose[^\n]*\bdown\b[^\n]*\s-v\b",
        "deletes every local volume — the DB restores itself on next up, but MinIO and "
        "any pulled Ollama model do not",
    ),
    (r"\bdocker\s+volume\s+rm\b", "deletes a Docker volume"),
    (r"manage_backup\.py\s+backup", "connects to the production database to take a dump"),
    (CMD + r"git\s+(commit|push)\b", "writes to git history"),
)

LOCAL_HINT = (
    "For local work use: docker compose -p memoryful --env-file .env.local "
    "-f docker/docker-compose.local.yml ..."
)


TAILS = {
    "deny": f"Production changes are made by a human, never by an agent. {LOCAL_HINT}",
    "ask": "Confirm if that is what you want.",
    "allow": "Observation only — report what it shows, and never act on production.",
}


def respond(decision: str, why: str) -> None:
    tail = TAILS[decision]
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": decision,
                    "permissionDecisionReason": (f"protect_prod.py: this command {why}. {tail}"),
                }
            }
        )
    )


def decide(command: str) -> tuple[str, str] | None:
    for pattern, why in LEAK:
        if pattern.search(command):
            return "deny", why
    for pattern, why in ALLOW:
        if pattern.fullmatch(command.strip()):
            return "allow", why
    for ruleset, decision in ((DENY, "deny"), (ASK, "ask")):
        for pattern, why in ruleset:
            if pattern.search(command):
                return decision, why
    return None


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return  # A malformed payload must never wedge the session.

    verdict = decide(payload.get("tool_input", {}).get("command", ""))
    if verdict:
        respond(*verdict)


if __name__ == "__main__":
    main()
