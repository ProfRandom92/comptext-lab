#!/usr/bin/env python3
"""Generate a deterministic safe repository intake report.

The report is intentionally lightweight: it inspects file names and paths only,
avoids network access, and does not read potentially sensitive project payloads.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "docs" / "reports" / "repo-intake-report.md"

SKIP_DIRS = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "site-packages",
    "venv",
}

PYTHON_PROJECT_FILES = {"pyproject.toml", "requirements.txt", "setup.py"}
NODE_PROJECT_FILES = {"package.json", "pnpm-lock.yaml", "package-lock.json", "yarn.lock"}
API_PATTERNS = ("api", "route", "routes", "server", "app")
DASHBOARD_PATTERNS = ("dashboard", "ui", "frontend", "web", "components")
REPORT_PATTERNS = ("export", "report", "reports", "csv", "json")
TEST_DIR_NAMES = {"test", "tests", "spec", "specs"}
TEST_SUFFIXES = ("_test.py", "_tests.py", ".test.js", ".test.jsx", ".test.ts", ".test.tsx", ".spec.js", ".spec.jsx", ".spec.ts", ".spec.tsx")


def iter_repo_files(root: Path) -> list[Path]:
    """Return repository files in stable order, excluding bulky generated trees."""
    files: list[Path] = []
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if path.is_file():
            files.append(path.relative_to(root))
    return sorted(files, key=lambda item: item.as_posix())


def has_pattern(path: Path, patterns: Iterable[str]) -> bool:
    value = path.as_posix().lower()
    return any(pattern in value for pattern in patterns)


def is_readme(path: Path) -> bool:
    return path.name.lower().startswith("readme")


def is_workflow(path: Path) -> bool:
    return path.parts[:2] == (".github", "workflows") and path.suffix.lower() in {".yml", ".yaml"}


def is_test_file(path: Path) -> bool:
    name = path.name.lower()
    if name.startswith("test_") and path.suffix == ".py":
        return True
    return name.endswith(TEST_SUFFIXES)


def is_test_dir(path: Path) -> bool:
    return any(part.lower() in TEST_DIR_NAMES for part in path.parts[:-1])


def detect_project_type(python_files: list[Path], node_files: list[Path]) -> str:
    if python_files and node_files:
        return "mixed Python/Node"
    if python_files:
        return "Python"
    if node_files:
        return "Node"
    return "unknown"


def infer_test_commands(files: list[Path], python_project: bool, node_project: bool) -> list[str]:
    commands: list[str] = []
    has_tests = any(is_test_file(path) or is_test_dir(path) for path in files)
    if python_project:
        commands.append("python -m py_compile scripts/*.py")
        if has_tests:
            commands.append("python -m pytest")
    if node_project and any(path.name == "package.json" for path in files):
        commands.append("npm test (only where package.json defines a test script)")
        commands.append("npm run lint (only where package.json defines a lint script)")
    if not commands:
        commands.append("No deterministic test command inferred; start with python scripts/run_checks.py.")
    return commands


def bullet_list(items: Iterable[Path | str], empty: str, limit: int = 80) -> str:
    values = [item.as_posix() if isinstance(item, Path) else item for item in items]
    if not values:
        return f"- {empty}\n"
    shown = values[:limit]
    rendered = "".join(f"- `{value}`\n" for value in shown)
    remaining = len(values) - len(shown)
    if remaining > 0:
        rendered += f"- ...and {remaining} more.\n"
    return rendered


def main() -> int:
    files = iter_repo_files(ROOT)

    readmes = [path for path in files if is_readme(path)]
    python_files = [path for path in files if path.name in PYTHON_PROJECT_FILES]
    node_files = [path for path in files if path.name in NODE_PROJECT_FILES]
    test_dirs = sorted({Path(path.parts[0]) if path.parts else path for path in files if is_test_dir(path)}, key=lambda item: item.as_posix())
    test_files = [path for path in files if is_test_file(path)]
    workflows = [path for path in files if is_workflow(path)]
    api_areas = [path for path in files if has_pattern(path, API_PATTERNS)]
    dashboard_areas = [path for path in files if has_pattern(path, DASHBOARD_PATTERNS)]
    report_areas = [path for path in files if has_pattern(path, REPORT_PATTERNS)]

    important = defaultdict(list)
    important["README files"] = readmes
    important["Python project files"] = python_files
    important["Node project files"] = node_files
    important["GitHub workflow files"] = workflows
    important["Test folders"] = test_dirs
    important["Test files"] = test_files

    project_type = detect_project_type(python_files, node_files)
    test_commands = infer_test_commands(files, bool(python_files), bool(node_files))
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    sections = [
        "# Repository Intake Report\n\n",
        f"- timestamp: `{timestamp}`\n",
        f"- repository_root: `{ROOT.name}`\n",
        f"- detected_project_type: `{project_type}`\n\n",
        "## Detected important files\n\n",
    ]

    for label, values in important.items():
        sections.append(f"### {label}\n\n")
        sections.append(bullet_list(values, "None detected."))
        sections.append("\n")

    sections.extend(
        [
            "## Detected test commands\n\n",
            bullet_list(test_commands, "No tests detected."),
            "\n",
            "## Detected API areas\n\n",
            bullet_list(api_areas, "No API-related paths detected."),
            "\n",
            "## Detected dashboard areas\n\n",
            bullet_list(dashboard_areas, "No dashboard-related paths detected."),
            "\n",
            "## Detected export/report areas\n\n",
            bullet_list(report_areas, "No export/report-related paths detected."),
            "\n",
            "## Empty-state note\n\n",
        ]
    )

    if not files:
        sections.append("No repository files were detected after excluding generated directories. Add source files, docs, or tests before enabling stronger checks.\n\n")
    else:
        sections.append("Repository files were detected; review the categorized paths above before making runtime, API, dashboard, or export changes.\n\n")

    sections.extend(
        [
            "## Next recommended checks\n\n",
            "- Run `python scripts/run_checks.py` for deterministic local validation.\n",
            "- Review `docs/AGENT_WORKFLOW.md` before agent-authored changes.\n",
            "- Review `docs/API_SURFACE.md` before API, dashboard, or export contract changes.\n",
            "- Use sanitized benchmark/regression summaries from `ProfRandom92/Comptext-Daimler-Experiment-` only as review evidence.\n\n",
            "## Safety notes\n\n",
            "- This intake reads paths and file names only; it does not inspect raw payloads.\n",
            "- Do not commit secrets, tokens, cookies, raw production logs, customer data, or proprietary documents.\n",
            "- Treat Daimler-related context as sensitive and use synthetic examples only.\n",
            "- Keep Comptextv7 decoupled from benchmark runtime code unless a future issue explicitly approves coupling.\n",
        ]
    )

    REPORT_PATH.write_text("".join(sections), encoding="utf-8")
    print(f"wrote {REPORT_PATH.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
