#!/usr/bin/env python3
"""Validate deterministic agent artifact bundle payloads."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE_PATH = REPO_ROOT / "artifacts" / "agent_artifact_bundle_example.json"

REQUIRED_BUNDLE_FIELDS = (
    "ok",
    "result",
    "branch",
    "changed_files",
    "safe_pr_gate",
    "validation_evidence",
)
REQUIRED_SAFE_GATE_FIELDS = (
    "allow_dirty",
    "allowed_prefixes",
    "branch",
    "changed_paths",
    "ok",
    "problems",
    "result",
    "status_short",
)
DISALLOWED_TIME_KEYS = {
    "timestamp",
    "generated_at",
    "created_at",
    "updated_at",
    "completed_at",
    "requested_at",
}
DISALLOWED_RANDOM_ID_KEYS = {
    "generated_id",
    "random_id",
    "request_id",
    "run_id",
    "uuid",
}
UUID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
)


def _relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"missing bundle file: {_relative(path)}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid JSON in bundle file: {_relative(path)}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"bundle file must contain a JSON object: {_relative(path)}")
    return payload


def _is_string_list(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _expected_result(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def _bundle_from_payload(payload: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    bundle = payload.get("bundle", payload)
    if isinstance(bundle, dict):
        return bundle, []
    return None, ["bundle must be a JSON object"]


def _scan_for_nondeterministic_fields(value: object, path: str = "$") -> list[str]:
    issues: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_path = f"{path}.{key}"
            normalized = key.lower()
            if normalized in DISALLOWED_TIME_KEYS:
                issues.append(f"{key_path}: timestamp-like field is not allowed")
            if normalized in DISALLOWED_RANDOM_ID_KEYS:
                issues.append(f"{key_path}: random-looking generated id field is not allowed")
            issues.extend(_scan_for_nondeterministic_fields(child, key_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            issues.extend(_scan_for_nondeterministic_fields(child, f"{path}[{index}]"))
    elif isinstance(value, str) and UUID_PATTERN.fullmatch(value):
        issues.append(f"{path}: UUID-like value is not allowed")
    return issues


def validate_bundle_payload(payload: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    issues.extend(_scan_for_nondeterministic_fields(payload))

    bundle, bundle_issues = _bundle_from_payload(payload)
    issues.extend(bundle_issues)
    if bundle is None:
        return {"issues": sorted(issues), "ok": False, "result": "FAIL"}

    for field in REQUIRED_BUNDLE_FIELDS:
        if field not in bundle:
            issues.append(f"bundle missing required field: {field}")

    ok = bundle.get("ok")
    result = bundle.get("result")
    branch = bundle.get("branch")
    changed_files = bundle.get("changed_files")
    safe_pr_gate = bundle.get("safe_pr_gate")
    validation_evidence = bundle.get("validation_evidence")

    if not isinstance(ok, bool):
        issues.append("bundle.ok must be a boolean")
    if not isinstance(result, str):
        issues.append("bundle.result must be a string")
    if isinstance(ok, bool) and isinstance(result, str) and result != _expected_result(ok):
        issues.append("bundle.result must match bundle.ok")
    if not isinstance(branch, str):
        issues.append("bundle.branch must be a string")
    if not _is_string_list(changed_files):
        issues.append("bundle.changed_files must be a list of strings")

    if not isinstance(safe_pr_gate, dict):
        issues.append("bundle.safe_pr_gate must be a JSON object")
    else:
        issues.extend(_validate_safe_pr_gate(safe_pr_gate, ok))

    if not isinstance(validation_evidence, list):
        issues.append("bundle.validation_evidence must be a list")
    else:
        issues.extend(_validate_validation_evidence(validation_evidence))

    return {"issues": sorted(issues), "ok": not issues, "result": "PASS" if not issues else "FAIL"}


def _validate_safe_pr_gate(safe_pr_gate: dict[str, Any], bundle_ok: object) -> list[str]:
    issues: list[str] = []
    for field in REQUIRED_SAFE_GATE_FIELDS:
        if field not in safe_pr_gate:
            issues.append(f"bundle.safe_pr_gate missing required field: {field}")

    gate_ok = safe_pr_gate.get("ok")
    gate_result = safe_pr_gate.get("result")
    if not isinstance(gate_ok, bool):
        issues.append("bundle.safe_pr_gate.ok must be a boolean")
    if not isinstance(gate_result, str):
        issues.append("bundle.safe_pr_gate.result must be a string")
    if isinstance(gate_ok, bool) and isinstance(gate_result, str) and gate_result != _expected_result(gate_ok):
        issues.append("bundle.safe_pr_gate.result must match bundle.safe_pr_gate.ok")
    if isinstance(bundle_ok, bool) and isinstance(gate_ok, bool) and bundle_ok != gate_ok:
        issues.append("bundle.ok must match bundle.safe_pr_gate.ok")
    if not isinstance(safe_pr_gate.get("allow_dirty"), bool):
        issues.append("bundle.safe_pr_gate.allow_dirty must be a boolean")
    if not isinstance(safe_pr_gate.get("branch"), str):
        issues.append("bundle.safe_pr_gate.branch must be a string")
    for field in ("allowed_prefixes", "changed_paths", "problems", "status_short"):
        if not _is_string_list(safe_pr_gate.get(field)):
            issues.append(f"bundle.safe_pr_gate.{field} must be a list of strings")
    return issues


def _validate_validation_evidence(validation_evidence: list[object]) -> list[str]:
    issues: list[str] = []
    for index, entry in enumerate(validation_evidence):
        if not isinstance(entry, dict):
            issues.append(f"bundle.validation_evidence[{index}] must be a JSON object")
            continue
        if not isinstance(entry.get("command"), str):
            issues.append(f"bundle.validation_evidence[{index}].command must be a string")
        if not isinstance(entry.get("result"), str):
            issues.append(f"bundle.validation_evidence[{index}].result must be a string")
    return issues


def validate_bundle_file(path: Path) -> dict[str, Any]:
    payload = _load_json_object(path)
    result = validate_bundle_payload(payload)
    return {
        "bundle": _relative(path),
        "issues": result["issues"],
        "ok": result["ok"],
        "result": result["result"],
    }


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a deterministic agent artifact bundle.")
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE_PATH, help="Bundle JSON path.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        result = validate_bundle_file(args.bundle)
    except RuntimeError as exc:
        result = {
            "error": {
                "message": str(exc),
                "type": exc.__class__.__name__,
            },
            "ok": False,
            "result": "ERROR",
        }
    sys.stdout.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
