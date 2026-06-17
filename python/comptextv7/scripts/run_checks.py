#!/usr/bin/env python3
"""Run deterministic local checks that are safe for agent-authored PRs."""

from __future__ import annotations

import fnmatch
import importlib.util
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "docs" / "reports" / "check-report.md"
SKIP_DIRS = {".git", ".hg", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".tox", ".venv", "__pycache__", "build", "dist", "node_modules", "site-packages", "venv"}
PYTHON_PROJECT_FILES = {"pyproject.toml", "requirements.txt", "setup.py"}
NODE_PROJECT_FILES = {"package.json", "pnpm-lock.yaml", "package-lock.json", "yarn.lock"}
TEST_PATTERNS = ("test_*.py", "*_test.py", "*_tests.py", "*.test.js", "*.test.jsx", "*.test.ts", "*.test.tsx", "*.spec.js", "*.spec.jsx", "*.spec.ts", "*.spec.tsx")


@dataclass
class CheckResult:
    name: str
    command: str
    status: str
    returncode: int | None
    note: str = ""


def iter_repo_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if path.is_file():
            files.append(rel)
    return sorted(files, key=lambda item: item.as_posix())


def has_python_tests(files: list[Path]) -> bool:
    return any(path.suffix == ".py" and (path.name.startswith("test_") or path.name.endswith(("_test.py", "_tests.py")) or "tests" in path.parts) for path in files)


def has_node_tests(files: list[Path]) -> bool:
    return any(fnmatch.fnmatch(path.name, pattern) for path in files for pattern in TEST_PATTERNS if not pattern.endswith(".py"))


def run_command(command: list[str], cwd: Path, display_command: list[str] | None = None) -> CheckResult:
    display_parts = display_command if display_command is not None else command
    display = " ".join(display_parts)
    completed = subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = sanitize_output(completed.stdout.strip())
    status = "pass" if completed.returncode == 0 else "fail"
    note = output[-4000:] if output else "completed with no output"
    return CheckResult(name=display, command=display, status=status, returncode=completed.returncode, note=note)


def sanitize_output(output: str) -> str:
    """Avoid echoing common secret-bearing lines into reports."""
    blocked = ("token", "secret", "password", "cookie", "authorization", "api_key", "apikey")
    safe_lines: list[str] = []
    for line in output.splitlines():
        lower = line.lower()
        if any(marker in lower for marker in blocked):
            safe_lines.append("[redacted line containing sensitive marker]")
        else:
            safe_lines.append(line)
    return "\n".join(safe_lines)


def package_scripts(package_json: Path) -> dict[str, str]:
    try:
        data = json.loads(package_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    scripts = data.get("scripts", {})
    if not isinstance(scripts, dict):
        return {}
    return {str(key): str(value) for key, value in scripts.items()}


def markdown_result(result: CheckResult) -> str:
    text = [f"### {result.name}\n\n", f"- status: `{result.status}`\n", f"- command: `{result.command}`\n"]
    if result.returncode is not None:
        text.append(f"- returncode: `{result.returncode}`\n")
    if result.note:
        text.append("\n```text\n")
        text.append(result.note)
        text.append("\n```\n")
    text.append("\n")
    return "".join(text)


def main() -> int:
    files = iter_repo_files(ROOT)
    python_project = any(path.name in PYTHON_PROJECT_FILES for path in files)
    node_project = any(path.name in NODE_PROJECT_FILES for path in files)
    project_type = "mixed Python/Node" if python_project and node_project else "Python" if python_project else "Node" if node_project else "unknown"
    results: list[CheckResult] = []

    scripts = sorted((ROOT / "scripts").glob("*.py")) if (ROOT / "scripts").exists() else []
    if scripts:
        command = [sys.executable, "-m", "py_compile", *[path.relative_to(ROOT).as_posix() for path in scripts]]
        display = ["python", "-m", "py_compile", *[path.relative_to(ROOT).as_posix() for path in scripts]]
        results.append(run_command(command, ROOT, display))
    elif python_project:
        results.append(CheckResult("python script compile", "python -m py_compile scripts/*.py", "skip", None, "no scripts/*.py files detected"))

    if python_project:
        if has_python_tests(files):
            if importlib.util.find_spec("pytest") is None:
                results.append(CheckResult("pytest", "python -m pytest", "skip", None, "pytest is not available; optional tool missing"))
            else:
                results.append(run_command([sys.executable, "-m", "pytest"], ROOT, ["python", "-m", "pytest"]))
        else:
            results.append(CheckResult("pytest", "python -m pytest", "skip", None, "no tests detected"))

    package_files = [ROOT / path for path in files if path.name == "package.json"]
    if node_project and package_files:
        npm = shutil.which("npm")
        for package_file in package_files:
            if python_project and package_file.parent == ROOT:
                continue
            rel_dir = package_file.parent.relative_to(ROOT).as_posix() or "."
            scripts_map = package_scripts(package_file)
            for script_name in ("test", "lint"):
                label = f"npm run {script_name} ({rel_dir})" if script_name != "test" else f"npm test ({rel_dir})"
                command = "npm test" if script_name == "test" else "npm run lint"
                if script_name not in scripts_map:
                    results.append(CheckResult(label, command, "skip", None, f"no {script_name} script detected in {package_file.relative_to(ROOT).as_posix()}"))
                elif npm is None:
                    results.append(CheckResult(label, command, "skip", None, "npm is not available; optional tool missing"))
                else:
                    npm_command = ["npm", "test"] if script_name == "test" else ["npm", "run", "lint"]
                    results.append(run_command(npm_command, package_file.parent))
    elif node_project:
        if has_node_tests(files):
            results.append(CheckResult("node tests", "npm test", "skip", None, "node test files detected, but no package.json was found"))
        else:
            results.append(CheckResult("node tests", "npm test", "skip", None, "no tests detected"))

    if not python_project and not node_project:
        results.append(CheckResult("project detection", "n/a", "skip", None, "no Python or Node project files detected"))

    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    body = [
        "# Agent Check Report\n\n",
        f"- timestamp: `{timestamp}`\n",
        f"- detected_project_type: `{project_type}`\n",
        "- safety: `local deterministic checks only; no dependency installation; no network required`\n\n",
        "## Results\n\n",
    ]
    body.extend(markdown_result(result) for result in results)
    failed = [result for result in results if result.status == "fail"]
    if failed:
        body.append("## Outcome\n\n- status: `fail`\n- reason: one or more available checks failed.\n")
    else:
        body.append("## Outcome\n\n- status: `pass`\n- note: missing optional tools or tests are reported as skips, not failures.\n")
    REPORT_PATH.write_text("".join(body), encoding="utf-8")
    print(f"wrote {REPORT_PATH.relative_to(ROOT).as_posix()}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
