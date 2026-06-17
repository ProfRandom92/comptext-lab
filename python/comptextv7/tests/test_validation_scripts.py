from __future__ import annotations
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def _run(args: list[str]) -> None:
    (ROOT / "reports").mkdir(exist_ok=True)
    subprocess.run([sys.executable] + args, cwd=ROOT, check=True)

def test_validate_replay():
    _run(["scripts/validate.py", "replay"])

def test_validate_token():
    _run(["scripts/validate.py", "token"])

def test_validate_forensic():
    _run(["scripts/validate.py", "forensic"])

def test_benchmarks():
    _run(["benchmarks/run_kvtc_v7_benchmarks.py", "--iterations", "1", "--warmups", "0"])

def test_dashboard_startup():
    _run(["dashboard/industrial_dashboard.py", "--once"])
