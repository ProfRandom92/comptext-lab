"""Deterministic local safety gate for agent-assisted PR workflows."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

RISKY_PATH_NAMES = frozenset({".env", "id_ed25519", "id_rsa"})
RISKY_PATH_SUFFIXES = (".key", ".pem")
PRIVATE_MARKERS = (
    "BEGIN PRIVATE KEY",
    "GITHUB_TOKEN=",
    "OPENAI_API_KEY=",
    "GEMINI_API_KEY=",
)


@dataclass(frozen=True, slots=True)
class GateState:
    branch: str
    status_short: tuple[str, ...]
    changed_paths: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class GateResult:
    ok: bool
    branch: str
    allow_dirty: bool
    allowed_prefixes: tuple[str, ...]
    status_short: tuple[str, ...]
    changed_paths: tuple[str, ...]
    problems: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed_prefixes": list(self.allowed_prefixes),
            "allow_dirty": self.allow_dirty,
            "branch": self.branch,
            "changed_paths": list(self.changed_paths),
            "ok": self.ok,
            "problems": list(self.problems),
            "result": "PASS" if self.ok else "FAIL",
            "status_short": list(self.status_short),
        }


def _run_git(args: list[str]) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"git executable not found while running: git {' '.join(args)}") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"git command failed with exit code {exc.returncode}: git {' '.join(args)}"
        ) from exc
    return completed.stdout


def _parse_porcelain_paths(output: str) -> tuple[str, ...]:
    if not output:
        return ()

    entries = output.split("\0")
    paths: list[str] = []
    index = 0
    while index < len(entries):
        entry = entries[index]
        if not entry:
            index += 1
            continue
        path = entry[3:]
        status = entry[:2]
        if status and any(char in {"R", "C"} for char in status):
            if index + 1 < len(entries) and entries[index + 1]:
                paths.append(entries[index + 1])
            index += 2
            continue
        paths.append(path)
        index += 1
    return tuple(paths)


def collect_gate_state() -> GateState:
    branch = _run_git(["branch", "--show-current"]).strip()
    status_short_output = _run_git(["status", "--short", "--untracked-files=all"])
    porcelain_output = _run_git(["status", "--porcelain=v1", "-z"])
    status_short = tuple(line for line in status_short_output.splitlines() if line)
    changed_paths = _parse_porcelain_paths(porcelain_output)
    return GateState(branch=branch, status_short=status_short, changed_paths=changed_paths)


def _path_in_prefix(path: str, prefix: str) -> bool:
    normalized = prefix.rstrip("/")
    return path == normalized or path.startswith(normalized + "/")


def _repo_relative_path(path: str) -> Path | None:
    candidate = (REPO_ROOT / path).resolve()
    try:
        candidate.relative_to(REPO_ROOT)
    except ValueError:
        return None
    return candidate


def _is_risky_path(path: str) -> bool:
    name = Path(path).name
    return name in RISKY_PATH_NAMES or name.endswith(RISKY_PATH_SUFFIXES)


def _read_changed_text(path: str) -> str | None:
    candidate = _repo_relative_path(path)
    if candidate is None or not candidate.is_file():
        return None
    try:
        data = candidate.read_bytes()
    except OSError:
        return None
    if b"\0" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _privacy_problems(changed_paths: tuple[str, ...]) -> tuple[str, ...]:
    problems: list[str] = []
    for path in sorted(changed_paths):
        if _is_risky_path(path):
            problems.append(f"privacy_risky_path:{path}")

        text = _read_changed_text(path)
        if text is None:
            continue
        for marker in PRIVATE_MARKERS:
            if marker in text:
                problems.append(f"privacy_marker:{marker}:{path}")
    return tuple(problems)


def evaluate_gate(
    state: GateState,
    *,
    allow_dirty: bool = False,
    allowed_prefixes: tuple[str, ...] = (),
) -> GateResult:
    problems: list[str] = []

    if state.branch == "main":
        problems.append("on_main_branch")

    if state.status_short and not allow_dirty:
        problems.append("dirty_working_tree")

    if allowed_prefixes:
        disallowed_paths = sorted(
            path
            for path in state.changed_paths
            if not any(_path_in_prefix(path, prefix) for prefix in allowed_prefixes)
        )
        if disallowed_paths:
            problems.append("changed_files_outside_allowed_prefixes")
            problems.extend(f"outside_prefix:{path}" for path in disallowed_paths)

    problems.extend(_privacy_problems(state.changed_paths))

    return GateResult(
        ok=not problems,
        branch=state.branch,
        allow_dirty=allow_dirty,
        allowed_prefixes=tuple(sorted(allowed_prefixes)),
        status_short=state.status_short,
        changed_paths=state.changed_paths,
        problems=tuple(problems),
    )


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a deterministic local safety gate for PR-ready agent work.")
    parser.add_argument("--allow-dirty", action="store_true", help="Permit a dirty working tree while still checking allowed prefixes.")
    parser.add_argument(
        "--allowed-prefix",
        action="append",
        default=[],
        help="Require changed paths to stay within this repo-relative prefix. May be repeated.",
    )
    return parser.parse_args(argv)


def _error_response(exc: RuntimeError) -> dict[str, Any]:
    return {
        "error": {
            "message": str(exc),
            "type": exc.__class__.__name__,
        },
        "ok": False,
        "result": "ERROR",
    }


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        state = collect_gate_state()
        result = evaluate_gate(
            state,
            allow_dirty=args.allow_dirty,
            allowed_prefixes=tuple(args.allowed_prefix),
        )
        sys.stdout.write(json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n")
        return 0 if result.ok else 1
    except RuntimeError as exc:
        sys.stdout.write(json.dumps(_error_response(exc), indent=2, sort_keys=True) + "\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
