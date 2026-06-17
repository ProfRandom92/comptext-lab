import json
import re
from pathlib import Path

VALID_VERSION = "air-v0.1"
VALID_INTENTS = {"audit", "summarize", "validate", "transform", "search", "plan", "unknown"}
VALID_INPUT_KINDS = {"path", "text", "url", "artifact", "repo", "query"}
VALID_OUTPUT_KINDS = {"report", "json", "markdown", "artifact", "summary"}
STEP_RE = re.compile(r"^[a-z][a-z0-9_-]*$")

REQUIRED = ["version", "intent", "goal", "pipeline", "outputs"]


def fail(msg):
    raise ValueError(msg)


def validate_air(obj):
    if not isinstance(obj, dict):
        fail("AIR artifact must be an object")

    for key in REQUIRED:
        if key not in obj:
            fail(f"missing required field: {key}")

    extra = set(obj) - {"version", "intent", "goal", "inputs", "pipeline", "contracts", "outputs", "metadata"}
    if extra:
        fail(f"unknown top-level fields: {sorted(extra)}")

    if obj["version"] != VALID_VERSION:
        fail("version must be air-v0.1")

    intent = obj["intent"]
    if not isinstance(intent, dict):
        fail("intent must be an object")
    if intent.get("type") not in VALID_INTENTS:
        fail("intent.type is invalid")

    if not isinstance(obj["goal"], str) or not obj["goal"].strip():
        fail("goal must be a non-empty string")

    inputs = obj.get("inputs", [])
    if not isinstance(inputs, list):
        fail("inputs must be an array")
    for item in inputs:
        if not isinstance(item, dict):
            fail("input item must be an object")
        if item.get("kind") not in VALID_INPUT_KINDS:
            fail("input.kind is invalid")
        if not isinstance(item.get("value"), str):
            fail("input.value must be a string")

    pipeline = obj["pipeline"]
    if not isinstance(pipeline, list) or not pipeline:
        fail("pipeline must be a non-empty array")
    for step in pipeline:
        if not isinstance(step, str) or not STEP_RE.match(step):
            fail(f"invalid pipeline step: {step!r}")

    contracts = obj.get("contracts", [])
    if not isinstance(contracts, list):
        fail("contracts must be an array")
    for contract in contracts:
        if not isinstance(contract, str):
            fail("contract ids must be strings")

    outputs = obj["outputs"]
    if not isinstance(outputs, list) or not outputs:
        fail("outputs must be a non-empty array")
    for output in outputs:
        if not isinstance(output, dict):
            fail("output item must be an object")
        if output.get("kind") not in VALID_OUTPUT_KINDS:
            fail("output.kind is invalid")
        if "path" in output and not isinstance(output["path"], str):
            fail("output.path must be a string")


def main():
    ok = True
    for path in sorted(Path("fixtures/air").glob("*.air.json")):
        obj = json.loads(path.read_text(encoding="utf-8"))
        should_fail = path.name.startswith("invalid.")
        try:
            validate_air(obj)
            if should_fail:
                print(f"BAD {path}: invalid fixture unexpectedly passed")
                ok = False
            else:
                print(f"OK {path}")
        except Exception as exc:
            if should_fail:
                print(f"OK {path} failed as expected: {exc}")
            else:
                print(f"BAD {path}: {exc}")
                ok = False

    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
