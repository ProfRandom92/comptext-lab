#!/usr/bin/env python3
"""Validate synthetic API/dashboard/export fixtures against the contract schema.

This is a lightweight, deterministic validator for the generated fixture. It uses
only the Python standard library and performs a small subset of JSON Schema-like
checks that match the current machine-readable contract needs.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "contracts" / "api-dashboard.schema.json"
FIXTURE_PATH = ROOT / "contracts" / "examples" / "api-dashboard.example.json"
REPORT_PATH = ROOT / "docs" / "reports" / "api-export-validation-report.md"
SUPPORTED_TYPES = {"string", "boolean", "object", "array"}
ARRAY_FIELDS = {"api_routes", "dashboard_views", "export_formats", "report_integration_points"}


def load_json(path: Path) -> tuple[Any | None, list[str]]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except json.JSONDecodeError as exc:
        return None, [f"invalid JSON at line {exc.lineno}, column {exc.colno}"]
    except OSError as exc:
        return None, [f"could not read file: {exc}"]


def type_name(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, str):
        return "string"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if value is None:
        return "null"
    return type(value).__name__


def matches_type(value: Any, expected: str) -> bool:
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    return False


def validate_schema(schema: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(schema, dict):
        return ["schema root must be an object"]
    if schema.get("type") != "object":
        errors.append("schema root type must be object")
    if not isinstance(schema.get("required"), list) or not all(isinstance(item, str) for item in schema.get("required", [])):
        errors.append("schema required must be an array of strings")
    if not isinstance(schema.get("properties"), dict):
        errors.append("schema properties must be an object")
        return errors

    for field, definition in schema["properties"].items():
        if not isinstance(definition, dict):
            errors.append(f"schema property {field} definition must be an object")
            continue
        expected = definition.get("type")
        if expected not in SUPPORTED_TYPES:
            errors.append(f"schema property {field} has unsupported type: {expected}")
    return errors


def validate_fixture(fixture: Any, schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(fixture, dict):
        return ["fixture root must be an object"]

    required = schema.get("required", [])
    properties = schema.get("properties", {})
    for field in required:
        if field not in fixture:
            errors.append(f"fixture missing required field: {field}")

    if schema.get("additionalProperties") is False:
        for field in sorted(fixture):
            if field not in properties:
                errors.append(f"fixture contains unexpected field: {field}")

    for field, definition in properties.items():
        if field not in fixture:
            continue
        expected = definition.get("type") if isinstance(definition, dict) else None
        if expected not in SUPPORTED_TYPES:
            errors.append(f"schema property {field} has unsupported type for fixture validation")
            continue
        if not matches_type(fixture[field], expected):
            errors.append(f"fixture field {field} expected {expected}, found {type_name(fixture[field])}")

    if fixture.get("synthetic") is not True:
        errors.append("fixture field synthetic must be true")

    for field in sorted(ARRAY_FIELDS):
        if field in fixture and not isinstance(fixture[field], list):
            errors.append(f"fixture field {field} must be an array")

    return errors


def build_report(schema_errors: list[str], fixture_errors: list[str]) -> str:
    failed = bool(schema_errors or fixture_errors)
    status = "fail" if failed else "pass"
    lines = [
        "# API Export Validation Report",
        "",
        "- generated_at: deterministic-api-export-validation",
        f"- status: {status}",
        f"- schema: `{SCHEMA_PATH.relative_to(ROOT).as_posix()}`",
        f"- fixture: `{FIXTURE_PATH.relative_to(ROOT).as_posix()}`",
        "- synthetic_required: true",
        "- live_server_required: false",
        "",
        "## Checks",
        "",
        "| Check | Status | Notes |",
        "| --- | --- | --- |",
        f"| Schema load and shape | {'fail' if schema_errors else 'pass'} | {'; '.join(schema_errors) if schema_errors else 'schema JSON loaded with supported field types'} |",
        f"| Fixture contract | {'fail' if fixture_errors else 'pass'} | {'; '.join(fixture_errors) if fixture_errors else 'required fields, simple types, synthetic flag, and array fields validated'} |",
        "",
        "## Safety",
        "",
        "Validation uses only local synthetic fixtures and does not contact a live server or read experiment repository data.",
        "The report intentionally records structural results only and does not print fixture payload contents.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    schema, schema_load_errors = load_json(SCHEMA_PATH)
    fixture, fixture_errors = load_json(FIXTURE_PATH)

    schema_errors = schema_load_errors[:]
    if not schema_errors:
        schema_errors = validate_schema(schema)

    if not fixture_errors and not schema_errors and isinstance(schema, dict):
        fixture_errors = validate_fixture(fixture, schema)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(build_report(schema_errors, fixture_errors), encoding="utf-8")

    if schema_errors or fixture_errors:
        print(f"API/export validation failed. See {REPORT_PATH.relative_to(ROOT)}")
        return 1

    print(f"API/export validation passed. Report written to {REPORT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
