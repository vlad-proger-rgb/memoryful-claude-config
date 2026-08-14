"""Regression test for protect_prod.py — `python .claude/hooks/test_protect_prod.py`.

No pytest: this has to stay runnable with nothing but a Python on PATH, the same way
the hook itself is. The rules are load-bearing security, and the interesting half is
what they must *not* block — reading these files and naming them in a commit message.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).with_name("protect_prod.py")

spec = importlib.util.spec_from_file_location("protect_prod", HOOK)
assert spec and spec.loader
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)

# Built by name so the strings under test never appear literally in this file's own
# command line when it is run — the hook would otherwise deny the test run itself.
VM = "docker-compose.vm.yml"
DEPLOY = "deploy-app.sh"
SWAP = "cos-swap-startup.sh"

CASES: list[tuple[str, str | None]] = [
    # Real invocations stay denied.
    (f"docker compose -p memoryful -f docker/{VM} up -d", "deny"),
    (f"docker compose -f {VM} up", "deny"),
    (f"docker-compose --file docker/{VM} up", "deny"),
    (f"./scripts/{DEPLOY}", "deny"),
    (f"bash scripts/{DEPLOY}", "deny"),
    (f"sh {SWAP}", "deny"),
    (f"cd /srv && ./{DEPLOY}", "deny"),
    (f"scripts/{DEPLOY} --yes", "deny"),
    ("gcloud compute instances list", "deny"),
    ("gcloud secrets versions access latest --secret=db", "deny"),
    ("psql $BACKUP_SOURCE_URL -c 'select 1'", "deny"),
    ("pg_dump postgres://u:p@ep-x.neon.tech/db", "deny"),
    ("docker compose --env-file .env -f docker/docker-compose.local.yml up", "deny"),
    # Reading and inspecting them is allowed — this is the whole point of the anchors.
    (f"cat scripts/{DEPLOY}", None),
    (f"grep -n image docker/{VM}", None),
    (f"head -20 scripts/{SWAP}", None),
    (f"less docker/{VM}", None),
    (f"wc -l scripts/{DEPLOY}", None),
    ("ls scripts/", None),
    ("git log --oneline -5", None),
    ("git diff --stat", None),
    (
        "docker compose -p memoryful --env-file .env.local "
        "-f docker/docker-compose.local.yml up --build",
        None,
    ),
    ("docker exec memoryful-app-local mypy", None),
    # Prose naming the files reaches git's own ASK rather than a hard deny.
    (f'git commit -m "docs: explain that {DEPLOY} is off limits"', "ask"),
    (f'git commit -m "ci: stop referencing {VM} in the guide"', "ask"),
    (f"echo 'the ban is on running {DEPLOY}'", None),
    # Unchanged ASK behavior.
    ("git commit -F -", "ask"),
    ("git push origin dev", "ask"),
    ("cd frontend && git commit -m 'x'", "ask"),
    ("docker compose -p memoryful down -v", "ask"),
    ("docker volume rm memoryful_db", "ask"),
    ("python scripts/python/manage_backup.py backup", "ask"),
]


def run_hook(command: str) -> str | None:
    """Drive the hook as a subprocess, the way Claude Code does."""
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps({"tool_input": {"command": command}}),
        capture_output=True,
        text=True,
        check=True,
    )
    if not result.stdout.strip():
        return None
    return json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"]


def main() -> int:
    failures = 0

    for command, expected in CASES:
        verdict = hook.decide(command)
        got = verdict[0] if verdict else None
        if got != expected:
            failures += 1
            print(f"FAIL  expected={expected!s:<5} got={got!s:<5}  {command}")

    # Spot-check the stdin/stdout contract too, not just the rule table.
    for command, expected in (CASES[0], CASES[13], CASES[24]):
        got = run_hook(command)
        if got != expected:
            failures += 1
            print(f"FAIL (subprocess)  expected={expected} got={got}  {command}")

    broken = subprocess.run(
        [sys.executable, str(HOOK)], input="not json", capture_output=True, text=True
    )
    if broken.returncode != 0 or broken.stdout.strip():
        failures += 1
        print(f"FAIL  malformed payload must be silent: rc={broken.returncode}")

    total = len(CASES) + 4
    print(f"{total - failures}/{total} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
