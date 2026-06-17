from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.validation.forensic import run_forensic_audit, write_report
from src.validation.golden_corpus import write_golden_corpus
from src.validation.replay import replay_summary, run_replay
from src.validation.token_telemetry import drift_fingerprint, tokenizer_version


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["golden", "forensic", "replay", "token", "all"])
    args = parser.parse_args()
    Path("reports").mkdir(exist_ok=True)
    if args.command in {"golden", "all"}:
        hashes = write_golden_corpus()
        print(json.dumps({"golden_hashes": hashes}, indent=2, sort_keys=True))
    if args.command in {"forensic", "all"}:
        results = run_forensic_audit()
        write_report(Path("RECONSTRUCTION_DRIFT_REPORT.md"), results, "Reconstruction Drift Report")
        write_report(Path("FORENSIC_AUDIT.md"), results, "Semantic Forensic Audit")
        print(json.dumps([result.as_dict() for result in results], indent=2, sort_keys=True))
        if not all(result.passed for result in results):
            return 1
    if args.command in {"replay", "all"}:
        summary = replay_summary(run_replay())
        Path("reports/replay_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps(summary, indent=2, sort_keys=True))
    if args.command in {"token", "all"}:
        print(json.dumps({"tokenizer_version": tokenizer_version(), "drift_fingerprint": drift_fingerprint()}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
