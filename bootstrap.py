#!/usr/bin/env python3
"""One-command local setup for Chronicle.

Reproducible from a fresh clone:

    python bootstrap.py

Uses only the Python standard library and the repository's existing tooling
(venv + pip + npm). It does not install system software, does not download
model weights unless you pass --pull-model, and never touches credentials
(Chronicle needs none -- local Ollama has no API key).

What it does, in order:
  1. Check prerequisites (Python >= 3.11, Node, npm) and fail clearly if missing.
  2. Create backend/.venv and install the backend editable with its test extra.
  3. Install frontend dependencies (npm ci when a lockfile is present).
  4. Create .env from .env.example if .env is absent (non-secret config).
  5. Ensure local runtime directories exist.
  6. Report Ollama / model status without hiding the large model download.

Flags:
  --pull-model[=TAG]  Also pull the Ollama model (large download; opt-in).
                      Default tag: qwen2.5:7b-instruct.
  --skip-backend      Skip the backend steps.
  --skip-frontend     Skip the frontend steps.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
BACKEND = REPO / "backend"
VENV = BACKEND / ".venv"
DEFAULT_MODEL = "qwen2.5:7b-instruct"
MIN_PY = (3, 11)


class SetupError(RuntimeError):
    pass


def info(msg: str) -> None:
    print(f"\033[36m[setup]\033[0m {msg}")


def ok(msg: str) -> None:
    print(f"\033[32m[ ok ]\033[0m {msg}")


def warn(msg: str) -> None:
    print(f"\033[33m[warn]\033[0m {msg}")


def fail(msg: str) -> "SetupError":
    return SetupError(msg)


def venv_python() -> Path:
    return VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def run(cmd: list[str], *, cwd: Path | None = None) -> None:
    printable = " ".join(str(c) for c in cmd)
    info(f"$ {printable}" + (f"   (in {cwd})" if cwd else ""))
    result = subprocess.run(cmd, cwd=str(cwd) if cwd else None)
    if result.returncode != 0:
        raise fail(f"command failed (exit {result.returncode}): {printable}")


def require(tool: str, install_hint: str) -> str:
    path = shutil.which(tool)
    if not path:
        raise fail(f"required tool '{tool}' not found on PATH. {install_hint}")
    return path


def check_prerequisites() -> None:
    info("Checking prerequisites...")
    if sys.version_info < MIN_PY:
        raise fail(
            f"Python {MIN_PY[0]}.{MIN_PY[1]}+ required; this interpreter is "
            f"{sys.version_info.major}.{sys.version_info.minor}. "
            "Re-run with a newer Python (e.g. `py -3.12 bootstrap.py`)."
        )
    ok(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    node = require("node", "Install Node.js 20+ from https://nodejs.org (or nvm).")
    npm = require("npm", "npm ships with Node.js; reinstall Node.js from https://nodejs.org.")
    for label, exe in (("node", node), ("npm", npm)):
        try:
            v = subprocess.run([exe, "--version"], capture_output=True, text=True)
            ok(f"{label} {v.stdout.strip()}")
        except OSError:
            ok(f"{label} found at {exe}")


def setup_backend() -> None:
    info("Setting up backend...")
    if not venv_python().exists():
        run([sys.executable, "-m", "venv", str(VENV)])
        ok(f"created venv at {VENV.relative_to(REPO)}")
    else:
        ok("venv already present")
    py = str(venv_python())
    run([py, "-m", "pip", "install", "--upgrade", "pip"])
    run([py, "-m", "pip", "install", "-e", "backend[test]"], cwd=REPO)
    ok("backend installed (editable, with test extra)")


def setup_frontend() -> None:
    info("Setting up frontend...")
    npm = require("npm", "Install Node.js from https://nodejs.org.")
    cmd = [npm, "ci"] if (REPO / "package-lock.json").exists() else [npm, "install"]
    run(cmd, cwd=REPO)
    ok("frontend dependencies installed")


def setup_config() -> None:
    info("Preparing local configuration...")
    example = REPO / ".env.example"
    env = REPO / ".env"
    if example.exists() and not env.exists():
        shutil.copyfile(example, env)
        ok("created .env from .env.example (non-secret; adjust CHRONICLE_OLLAMA_BASE_URL if needed)")
    elif env.exists():
        ok(".env already present (left unchanged)")
    else:
        warn(".env.example not found; skipping config copy")


def setup_dirs() -> None:
    info("Ensuring local runtime directories...")
    for rel in ("runs", "runs/acquisition/cache", "runs/acquisition/built-corpora"):
        (BACKEND / rel).mkdir(parents=True, exist_ok=True)
    ok("runtime directories ready (backend/runs/*)")


def report_ollama(pull_model: str | None) -> None:
    info("Checking Ollama (required only for live investigation, not for tests)...")
    ollama = shutil.which("ollama")
    if not ollama:
        warn(
            "Ollama not found. Install it from https://ollama.com to run live "
            "investigations. The backend test suite uses a deterministic "
            "provider and does NOT need Ollama."
        )
        _print_model_hint()
        return
    ok(f"ollama found at {ollama}")
    try:
        listed = subprocess.run([ollama, "list"], capture_output=True, text=True, timeout=15)
        tags = listed.stdout
    except (OSError, subprocess.TimeoutExpired):
        warn("could not query `ollama list` (is the Ollama daemon running?).")
        tags = ""
    if DEFAULT_MODEL.split(":")[0] in tags:
        ok(f"an Ollama qwen2.5 model appears to be pulled:\n{tags.strip()}")
    else:
        _print_model_hint()
    if pull_model:
        warn(f"--pull-model set: downloading '{pull_model}' now (this is a multi-GB download).")
        run([ollama, "pull", pull_model])
        ok(f"pulled {pull_model}")


def _print_model_hint() -> None:
    print(
        "\n  Model download is large and NOT performed automatically:\n"
        f"    ollama pull {DEFAULT_MODEL}      # ~5 GB, the tuned default\n"
        "    ollama pull qwen2.5:3b-instruct    # ~2 GB, low-memory fallback\n"
        "  Re-run this script with --pull-model to fetch the default, or\n"
        "  --pull-model=qwen2.5:3b-instruct for the smaller one.\n"
    )


def next_steps() -> None:
    py = venv_python()
    py_rel = py.relative_to(REPO) if py.is_relative_to(REPO) else py
    print(
        "\n" + "=" * 68 + "\n"
        "Setup complete. Next steps:\n\n"
        "  Start the backend API (terminal 1):\n"
        f"    {py_rel} -m uvicorn \"chronicle.api:create_default_app\" --factory --host 127.0.0.1 --port 8000\n\n"
        "  Start the frontend (terminal 2):\n"
        "    npm run dev\n\n"
        "  Run the standard verification suite:\n"
        f"    {py_rel} -m pytest        # from backend/, or: (cd backend && .venv/... -m pytest)\n"
        "    npm run lint && npm run typecheck && npx vitest run && npm run build\n\n"
        "  Live investigation additionally needs Ollama running with a model pulled\n"
        "  (see above). See README.md for the low-memory (CHRONICLE_OLLAMA_MODEL) notes.\n"
        + "=" * 68
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pull-model", nargs="?", const=DEFAULT_MODEL, default=None,
                        help=f"also pull the Ollama model (default {DEFAULT_MODEL}); large download")
    parser.add_argument("--skip-backend", action="store_true")
    parser.add_argument("--skip-frontend", action="store_true")
    args = parser.parse_args()

    try:
        check_prerequisites()
        if not args.skip_backend:
            setup_backend()
        if not args.skip_frontend:
            setup_frontend()
        setup_config()
        setup_dirs()
        report_ollama(args.pull_model)
        next_steps()
    except SetupError as exc:
        print(f"\n\033[31m[setup failed]\033[0m {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
