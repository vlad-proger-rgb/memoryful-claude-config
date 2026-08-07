"""PostToolUse:Edit|Write — report mypy errors for the file just written.

Runs mypy inside the app container, where the dependencies and stubs live. Reports
only; it never blocks or rewrites, because a multi-step edit is legitimately broken
in between and stopping there would be worse than the errors.

Silent when the container is down, when mypy has nothing to say, or for anything
outside the backend.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "memoryful-backend"
CONTAINER = "memoryful-app-local"
# mypy.ini scopes these; anything else it would refuse to check anyway.
CHECKED_ROOTS = ("app", "mcp_server", "scripts")


def container_path(path: Path) -> str | None:
    """Repo path -> its /app path inside the container, if mypy covers it."""
    try:
        rel = path.relative_to(BACKEND)
    except ValueError:
        return None
    return f"/app/{rel.as_posix()}" if rel.parts[0] in CHECKED_ROOTS else None


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return

    raw = (payload.get("tool_input") or {}).get("file_path")
    if not raw:
        return
    path = Path(raw).resolve()
    if path.suffix != ".py":
        return
    target = container_path(path)
    if target is None:
        return

    try:
        result = subprocess.run(  # noqa: S603  # fixed argv, no shell interpolation
            ["docker", "exec", CONTAINER, "mypy", target],  # noqa: S607
            capture_output=True,
            text=True,
            timeout=90,
            shell=(sys.platform == "win32"),
        )
    except (OSError, subprocess.SubprocessError):
        return

    errors = [line for line in result.stdout.splitlines() if ": error:" in line]
    if errors:
        print(f"mypy on {path.name}:")
        for line in errors[:15]:
            print(f"  {line}")
        if len(errors) > 15:
            print(f"  ... {len(errors) - 15} more")


if __name__ == "__main__":
    main()
    sys.exit(0)
