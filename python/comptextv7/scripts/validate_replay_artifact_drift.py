#!/usr/bin/env python3
"""Validate deterministic replay artifacts and published benchmark summaries.

The checks in this module intentionally stay lightweight: they rebuild the
fixture-bound replay artifacts with the existing deterministic generators,
serialize them with the repository's stable JSON/Markdown renderers, and compare
those bytes with the committed review artifacts. The same generated values are
also used to verify the README and comparative degradation documentation so
published benchmark numbers cannot silently drift from generator output.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tests.utils.agent_trace_replay_runner import build_agent_trace_replay_artifact
from tests.utils.agent_trace_replay_runner import stable_json_dump as stable_agent_json_dump
from tests.utils.iterative_replay_degradation_runner import build_comparative_replay_degradation_artifact
from tests.utils.iterative_replay_degradation_runner import build_iterative_replay_degradation_artifact
from tests.utils.iterative_replay_degradation_runner import build_replay_sensitivity_analysis_artifact
from tests.utils.iterative_replay_degradation_runner import stable_json_dump as stable_iterative_json_dump
from tests.utils.paper_replay_runner import build_paper_replay_artifact
from tests.utils.paper_replay_runner import stable_json_dump as stable_paper_json_dump
from tests.utils.replay_degradation_summary import render_replay_degradation_profile_comparison
from tests.utils.replay_degradation_summary import render_replay_degradation_summary
from tests.utils.replay_degradation_summary import render_replay_sensitivity_analysis

PAPER_ARTIFACT_PATH = REPO_ROOT / "artifacts" / "paper_replay_results.json"
AGENT_TRACE_ARTIFACT_PATH = REPO_ROOT / "artifacts" / "agent_trace_replay_results.json"
ITERATIVE_ARTIFACT_PATH = REPO_ROOT / "artifacts" / "iterative_replay_degradation_results.json"
ITERATIVE_SUMMARY_PATH = REPO_ROOT / "artifacts" / "iterative_replay_degradation_results.summary.md"
README_PATH = REPO_ROOT / "README.md"
ITERATIVE_DOC_PATH = REPO_ROOT / "docs" / "iterative_replay_degradation.md"

PROFILE_ORDER = ("CONSERVATIVE", "BALANCED", "AGGRESSIVE")


@dataclass(frozen=True, slots=True)
class DriftCheckFailure:
    """Reviewer-readable drift failure detail."""

    name: str
    message: str
    diff: str = ""

    def format(self) -> str:
        body = [f"[{self.name}] {self.message}"]
        if self.diff:
            body.extend(["", self.diff.rstrip()])
        return "\n".join(body)


def _relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _unified_diff(*, expected: str, actual: str, expected_label: str, actual_label: str) -> str:
    return "".join(
        difflib.unified_diff(
            expected.splitlines(keepends=True),
            actual.splitlines(keepends=True),
            fromfile=expected_label,
            tofile=actual_label,
            lineterm="",
        )
    )


def _compare_text(*, name: str, expected: str, actual: str, expected_label: str, actual_label: str) -> list[DriftCheckFailure]:
    if expected == actual:
        return []
    return [
        DriftCheckFailure(
            name=name,
            message=(
                "deterministic output drifted; regenerate or intentionally update "
                f"{actual_label} after reviewing the mismatch surface"
            ),
            diff=_unified_diff(
                expected=expected,
                actual=actual,
                expected_label=expected_label,
                actual_label=actual_label,
            ),
        )
    ]


def _committed_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _format_rate(value: object) -> str:
    return f"{float(value):.6f}"


def _profile_aggregate_by_name(comparative_artifact: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    profiles = comparative_artifact.get("profiles", [])
    if not isinstance(profiles, list):
        return {}
    result: dict[str, Mapping[str, object]] = {}
    for profile in profiles:
        if not isinstance(profile, dict):
            continue
        name = profile.get("profile")
        aggregate = profile.get("aggregate")
        if isinstance(name, str) and isinstance(aggregate, dict):
            result[name] = aggregate
    return result


def _expected_readme_metrics(
    *,
    paper_artifact: Mapping[str, object],
    agent_artifact: Mapping[str, object],
    comparative_artifact: Mapping[str, object],
) -> dict[str, str]:
    paper_aggregate = paper_artifact["aggregate"]
    agent_aggregate = agent_artifact["aggregate"]
    assert isinstance(paper_aggregate, dict)
    assert isinstance(agent_aggregate, dict)
    profiles = _profile_aggregate_by_name(comparative_artifact)
    return {
        "Agent trace replay consistency": _format_rate(agent_aggregate["avg_replay_consistency"]),
        "Paper replay consistency": _format_rate(paper_aggregate["avg_replay_consistency"]),
        "`CONSERVATIVE` replay consistency": _format_rate(profiles["CONSERVATIVE"]["average_replay_consistency"]),
        "`BALANCED` replay consistency": _format_rate(profiles["BALANCED"]["average_replay_consistency"]),
        "`AGGRESSIVE` replay consistency": _format_rate(profiles["AGGRESSIVE"]["average_replay_consistency"]),
        "Paper avg compression": _format_rate(paper_aggregate["avg_compression_ratio"]),
        "Agent avg compression": _format_rate(agent_aggregate["avg_compression_ratio"]),
        "Agent replay consistency": _format_rate(agent_aggregate["avg_replay_consistency"]),
        "Agent operational drift": _format_rate(agent_aggregate["avg_operational_drift_rate"]),
    }


def _extract_readme_metric(readme: str, label: str) -> str | None:
    escaped_label = re.escape(label)
    match = re.search(rf"^\|\s*{escaped_label}\s*\|\s*`([^`]+)`\s*\|$", readme, flags=re.MULTILINE)
    return match.group(1) if match else None


def _validate_readme_metrics(
    *,
    paper_artifact: Mapping[str, object],
    agent_artifact: Mapping[str, object],
    comparative_artifact: Mapping[str, object],
) -> list[DriftCheckFailure]:
    readme = _committed_text(README_PATH)
    failures: list[DriftCheckFailure] = []
    for label, expected in _expected_readme_metrics(
        paper_artifact=paper_artifact,
        agent_artifact=agent_artifact,
        comparative_artifact=comparative_artifact,
    ).items():
        actual = _extract_readme_metric(readme, label)
        if actual != expected:
            failures.append(
                DriftCheckFailure(
                    name="README benchmark values",
                    message=(
                        f"{_relative(README_PATH)} metric {label!r} is {actual!r}; "
                        f"expected {expected!r} from deterministic artifacts"
                    ),
                )
            )

    balanced_labels = _profile_aggregate_by_name(comparative_artifact)["BALANCED"]["aggregated_failure_labels"]
    missing_labels = [label for label in balanced_labels if f"`{label}`" not in readme]
    if missing_labels:
        failures.append(
            DriftCheckFailure(
                name="README comparative labels",
                message=(
                    f"{_relative(README_PATH)} is missing expected BALANCED failure labels "
                    f"derived from the comparative artifact: {missing_labels!r}"
                ),
            )
        )
    return failures


def _profile_markdown_rows(comparative_artifact: Mapping[str, object]) -> list[str]:
    return [line for line in render_replay_degradation_profile_comparison(comparative_artifact) if line.startswith("| `")]


def _validate_comparative_docs(comparative_artifact: Mapping[str, object]) -> list[DriftCheckFailure]:
    expected_rows = _profile_markdown_rows(comparative_artifact)
    doc_text = _committed_text(ITERATIVE_DOC_PATH)
    failures: list[DriftCheckFailure] = []
    for row in expected_rows:
        if row not in doc_text:
            failures.append(
                DriftCheckFailure(
                    name="comparative replay degradation docs",
                    message=(
                        f"{_relative(ITERATIVE_DOC_PATH)} is missing or has drifted from generated row: {row}"
                    ),
                )
            )
    return failures


def _sensitivity_markdown_rows(sensitivity_artifact: Mapping[str, object]) -> list[str]:
    artifact = {"sensitivity_analysis": sensitivity_artifact}
    prefixes = ("| baseline", "| budget", "| extended")
    return [line for line in render_replay_sensitivity_analysis(artifact) if line.startswith(prefixes)]


def _validate_sensitivity_docs(sensitivity_artifact: Mapping[str, object]) -> list[DriftCheckFailure]:
    expected_rows = _sensitivity_markdown_rows(sensitivity_artifact)
    doc_text = _committed_text(ITERATIVE_DOC_PATH)
    failures: list[DriftCheckFailure] = []
    for row in expected_rows:
        if row not in doc_text:
            failures.append(
                DriftCheckFailure(
                    name="replay sensitivity analysis docs",
                    message=(
                        f"{_relative(ITERATIVE_DOC_PATH)} is missing or has drifted from generated row: {row}"
                    ),
                )
            )
    return failures


def _validate_profile_order(comparative_artifact: Mapping[str, object]) -> list[DriftCheckFailure]:
    profiles = comparative_artifact.get("profiles", [])
    actual = tuple(profile.get("profile") for profile in profiles if isinstance(profile, dict)) if isinstance(profiles, list) else ()
    if actual == PROFILE_ORDER:
        return []
    return [
        DriftCheckFailure(
            name="comparative replay degradation profile order",
            message=f"expected profile order {PROFILE_ORDER!r}; got {actual!r}",
        )
    ]


def run_drift_checks() -> list[DriftCheckFailure]:
    """Return all deterministic replay artifact/doc drift failures."""

    paper_artifact = build_paper_replay_artifact()
    agent_artifact = build_agent_trace_replay_artifact()
    iterative_artifact = build_iterative_replay_degradation_artifact()
    comparative_artifact = build_comparative_replay_degradation_artifact()
    sensitivity_artifact = build_replay_sensitivity_analysis_artifact()

    generated_paper_json = stable_paper_json_dump(paper_artifact)
    generated_agent_json = stable_agent_json_dump(agent_artifact)
    generated_iterative_json = stable_iterative_json_dump(iterative_artifact)
    generated_iterative_summary = render_replay_degradation_summary(iterative_artifact)

    failures: list[DriftCheckFailure] = []
    failures.extend(
        _compare_text(
            name="paper replay artifact",
            expected=generated_paper_json,
            actual=_committed_text(PAPER_ARTIFACT_PATH),
            expected_label="generated paper replay artifact",
            actual_label=_relative(PAPER_ARTIFACT_PATH),
        )
    )
    failures.extend(
        _compare_text(
            name="agent trace replay artifact",
            expected=generated_agent_json,
            actual=_committed_text(AGENT_TRACE_ARTIFACT_PATH),
            expected_label="generated agent trace replay artifact",
            actual_label=_relative(AGENT_TRACE_ARTIFACT_PATH),
        )
    )
    failures.extend(
        _compare_text(
            name="iterative replay degradation artifact",
            expected=generated_iterative_json,
            actual=_committed_text(ITERATIVE_ARTIFACT_PATH),
            expected_label="generated iterative replay degradation artifact",
            actual_label=_relative(ITERATIVE_ARTIFACT_PATH),
        )
    )
    failures.extend(
        _compare_text(
            name="iterative replay degradation Markdown summary",
            expected=generated_iterative_summary,
            actual=_committed_text(ITERATIVE_SUMMARY_PATH),
            expected_label="generated iterative replay degradation summary",
            actual_label=_relative(ITERATIVE_SUMMARY_PATH),
        )
    )
    failures.extend(
        _compare_text(
            name="committed iterative JSON to Markdown summary",
            expected=render_replay_degradation_summary(json.loads(_committed_text(ITERATIVE_ARTIFACT_PATH))),
            actual=_committed_text(ITERATIVE_SUMMARY_PATH),
            expected_label="summary rendered from committed iterative JSON",
            actual_label=_relative(ITERATIVE_SUMMARY_PATH),
        )
    )
    failures.extend(
        _validate_readme_metrics(
            paper_artifact=paper_artifact,
            agent_artifact=agent_artifact,
            comparative_artifact=comparative_artifact,
        )
    )
    failures.extend(_validate_comparative_docs(comparative_artifact))
    failures.extend(_validate_sensitivity_docs(sensitivity_artifact))
    failures.extend(_validate_profile_order(comparative_artifact))
    return failures


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fail if deterministic replay artifacts or published replay summary values drift from generator output."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable failure details as JSON.",
    )
    return parser.parse_args(argv)


def _failure_payload(failures: Iterable[DriftCheckFailure]) -> list[dict[str, str]]:
    return [{"name": failure.name, "message": failure.message, "diff": failure.diff} for failure in failures]


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    failures = run_drift_checks()
    if args.json:
        print(json.dumps({"failures": _failure_payload(failures)}, ensure_ascii=False, indent=2, sort_keys=True))
    elif failures:
        print("deterministic replay artifact drift detected:\n")
        print("\n\n".join(failure.format() for failure in failures))
    else:
        print("deterministic replay artifact drift checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
