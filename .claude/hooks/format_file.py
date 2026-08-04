"""PostToolUse:Edit|Write hook — format whatever file was just written.

Claude Code sends the tool call as JSON on stdin; the path is tool_input.file_path.
Which formatter runs depends on which repo the file landed in.

Formatting must never break an edit, so every failure here is swallowed and the
script exits 0 regardless.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
BACKEND = ROOT / "memoryful-backend"
FRONTEND = ROOT / "memoryful-frontend"

FRONTEND_SUFFIXES = {".ts", ".tsx", ".js", ".vue", ".css", ".json", ".md"}


def run(command: list[str], cwd: Path) -> None:
    try:
        subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            timeout=30,
            shell=(sys.platform == "win32"),
        )
    except (OSError, subprocess.SubprocessError):
        pass  # Formatter missing or file unparseable — leave the edit alone.


def venv_bin(name: str) -> str:
    """Prefer the backend venv's copy, fall back to whatever is on PATH."""
    exe = BACKEND / ".venv" / "Scripts" / f"{name}.exe"
    return str(exe) if exe.exists() else name


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return

    raw_path = payload.get("tool_input", {}).get("file_path")
    if not raw_path:
        return

    path = Path(raw_path).resolve()

    if path.is_relative_to(BACKEND) and path.suffix == ".py":
        run([venv_bin("black"), "--quiet", str(path)], cwd=BACKEND)
        run([venv_bin("isort"), "--quiet", str(path)], cwd=BACKEND)
        return

    if path.is_relative_to(FRONTEND) and path.suffix in FRONTEND_SUFFIXES:
        run(["npx", "--no-install", "prettier", "--write", str(path)], cwd=FRONTEND)


if __name__ == "__main__":
    main()
