#!/usr/bin/env python3
"""Validate Comptextv7 machine-readable contract schemas and examples.

This script intentionally implements a small deterministic subset of JSON
Schema-like checks with only the Python standard library. It validates contract
schemas, validates synthetic examples against matching schemas, and writes a
Markdown report for CI artifacts.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS_DIR = ROOT / "contracts"
EXAMPLES_DIR = CONTRACTS_DIR / "examples"
REPORT_PATH = ROOT / "docs" / "reports" / "contract-validation-report.md"
SCHEMA_SUFFIX = ".schema.json"
EXAMPLE_SUFFIX = ".example.json"
SUPPORTED_TYPES = {"string", "number", "integer", "boolean", "object", "array", "null"}
SCHEMA_REQUIRED_FIELDS = {"title", "description", "type", "required", "properties"}


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
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if value is None:
        return "null"
    return type(value).__name__


def schema_types(schema_type: Any) -> list[str]:
    if isinstance(schema_type, str):
        return [schema_type]
    if isinstance(schema_type, list) and all(isinstance(item, str) for item in schema_type):
        return schema_type
    return []


def validate_schema_type(schema_type: Any, location: str) -> list[str]:
    types = schema_types(schema_type)
    if not types or any(item not in SUPPORTED_TYPES for item in types):
        return [f"{location} has unsupported or missing type"]
    return []


def matches_type(value: Any, expected: Any) -> bool:
    return any(matches_single_type(value, item) for item in schema_types(expected))


def matches_single_type(value: Any, expected: str) -> bool:
    if expected == "string":
        return isinstance(value, str)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "null":
        return value is None
    return False


def validate_schema_shape(schema: Any, path: Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(schema, dict):
        return ["schema root must be an object"]

    missing = sorted(SCHEMA_REQUIRED_FIELDS.difference(schema))
    for field in missing:
        errors.append(f"schema missing required metadata field: {field}")

    schema_type = schema.get("type")
    type_errors = validate_schema_type(schema_type, "schema root")
    if type_errors:
        errors.extend(type_errors)
    elif "object" not in schema_types(schema_type):
        errors.append("schema root type must be object")
    if not isinstance(schema.get("required"), list) or not all(
        isinstance(item, str) for item in schema.get("required", [])
    ):
        errors.append("schema required must be an array of strings")
    if not isinstance(schema.get("properties"), dict):
        errors.append("schema properties must be an object")
    if "additionalProperties" in schema and not isinstance(schema["additionalProperties"], bool):
        errors.append("schema additionalProperties must be boolean when present")

    properties = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
    required = schema.get("required") if isinstance(schema.get("required"), list) else []
    for field in required:
        if field not in properties:
            errors.append(f"required field {field!r} is not declared in properties")

    for property_name, definition in properties.items():
        errors.extend(validate_property_definition(definition, f"properties.{property_name}"))

    if path.parent.name == "examples":
        errors.append("schema file must not live under contracts/examples")
    return errors


def validate_property_definition(definition: Any, location: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(definition, dict):
        return [f"{location} definition must be an object"]

    expected_type = definition.get("type")
    errors.extend(validate_schema_type(expected_type, location))

    if "object" in schema_types(expected_type):
        nested_properties = definition.get("properties")
        nested_required = definition.get("required", [])
        if nested_properties is not None and not isinstance(nested_properties, dict):
            errors.append(f"{location}.properties must be an object")
        if not isinstance(nested_required, list) or not all(isinstance(item, str) for item in nested_required):
            errors.append(f"{location}.required must be an array of strings when present")
        if isinstance(nested_properties, dict):
            for field in nested_required:
                if field not in nested_properties:
                    errors.append(f"{location} required field {field!r} is not declared")
            for property_name, nested_definition in nested_properties.items():
                errors.extend(
                    validate_property_definition(nested_definition, f"{location}.properties.{property_name}")
                )
    return errors


def validate_instance(instance: Any, schema: dict[str, Any], location: str) -> list[str]:
    errors: list[str] = []
    expected_type = schema.get("type")
    if expected_type and not matches_type(instance, expected_type):
        return [f"{location} expected {expected_type}, found {type_name(instance)}"]
    if not isinstance(instance, dict):
        return errors

    required = schema.get("required", [])
    properties = schema.get("properties", {})
    for field in required:
        if field not in instance:
            errors.append(f"{location} missing required field: {field}")

    if schema.get("additionalProperties") is False:
        for field in sorted(instance):
            if field not in properties:
                errors.append(f"{location} contains unexpected field: {field}")

    for field, definition in properties.items():
        if field not in instance:
            continue
        if not isinstance(definition, dict):
            errors.append(f"{location}.{field} has invalid schema definition")
            continue
        field_type = definition.get("type")
        type_errors = validate_schema_type(field_type, f"{location}.{field}")
        if type_errors:
            errors.extend(
                error.replace("unsupported or missing type", "unsupported schema type")
                for error in type_errors
            )
            continue
        value = instance[field]
        if not matches_type(value, field_type):
            errors.append(f"{location}.{field} expected {field_type}, found {type_name(value)}")
            continue
        if isinstance(value, dict) and "object" in schema_types(field_type):
            errors.extend(validate_instance(value, definition, f"{location}.{field}"))
    return errors


def schema_for_example(example_path: Path, schemas: dict[str, dict[str, Any]]) -> tuple[dict[str, Any] | None, str]:
    stem = example_path.name.removesuffix(EXAMPLE_SUFFIX)
    schema_name = f"{stem}{SCHEMA_SUFFIX}"
    return schemas.get(schema_name), schema_name


def markdown_report(
    schema_results: list[tuple[Path, list[str]]],
    example_results: list[tuple[Path, str, list[str]]],
) -> str:
    failed = any(errors for _, errors in schema_results) or any(errors for _, _, errors in example_results)
    status = "fail" if failed else "pass"
    lines = [
        "# Contract Validation Report",
        "",
        "- generated_at: deterministic-contract-validation",
        f"- status: {status}",
        f"- schema_count: {len(schema_results)}",
        f"- example_count: {len(example_results)}",
        "",
        "## Schemas",
        "",
        "| File | Status | Notes |",
        "| --- | --- | --- |",
    ]
    for path, errors in schema_results:
        rel = path.relative_to(ROOT).as_posix()
        note = "; ".join(errors) if errors else "valid JSON and required schema metadata present"
        lines.append(f"| `{rel}` | {'fail' if errors else 'pass'} | {note} |")

    lines.extend([
        "",
        "## Examples",
        "",
        "| File | Schema | Status | Notes |",
        "| --- | --- | --- | --- |",
    ])
    for path, schema_name, errors in example_results:
        rel = path.relative_to(ROOT).as_posix()
        note = "; ".join(errors) if errors else "valid synthetic example structure"
        lines.append(f"| `{rel}` | `{schema_name}` | {'fail' if errors else 'pass'} | {note} |")

    lines.extend([
        "",
        "## Safety",
        "",
        "This validator checks structure only. Contract examples are expected to remain synthetic and must not include secrets, raw production logs, customer data, or proprietary documents.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    schema_paths = sorted(path for path in CONTRACTS_DIR.rglob(f"*{SCHEMA_SUFFIX}") if EXAMPLES_DIR not in path.parents)
    example_paths = sorted(EXAMPLES_DIR.glob(f"*{EXAMPLE_SUFFIX}"))
    schemas: dict[str, dict[str, Any]] = {}
    schema_results: list[tuple[Path, list[str]]] = []

    for path in schema_paths:
        schema, errors = load_json(path)
        if not errors:
            errors = validate_schema_shape(schema, path)
        if not errors and isinstance(schema, dict):
            schemas[path.name] = schema
        schema_results.append((path, errors))

    example_results: list[tuple[Path, str, list[str]]] = []
    for path in example_paths:
        instance, errors = load_json(path)
        schema, schema_name = schema_for_example(path, schemas)
        if schema is None:
            errors.append(f"matching schema not found: {schema_name}")
        if not errors and schema is not None:
            errors = validate_instance(instance, schema, path.name)
        example_results.append((path, schema_name, errors))

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(markdown_report(schema_results, example_results), encoding="utf-8")

    has_errors = any(errors for _, errors in schema_results) or any(
        errors for _, _, errors in example_results
    )
    if has_errors:
        print(f"Contract validation failed. See {REPORT_PATH.relative_to(ROOT)}")
        return 1

    print(f"Contract validation passed. Report written to {REPORT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
