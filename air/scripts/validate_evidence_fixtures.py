import json
import re
from pathlib import Path

from canonical_json import ALGORITHM, CANONICALIZATION, hash_event, hash_json_file

HASH_RE = re.compile(r"^[a-f0-9]{64}$")
TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
EVENT_TYPES = {"start", "step", "artifact", "end", "error", "verification"}
EXECUTOR_TYPES = {"agent", "human", "system"}


def fail(msg):
    raise ValueError(msg)


def validate_typed_hash(obj, label):
    if not isinstance(obj, dict):
        fail(f"{label} must be a typed hash object")
    for key in ["algorithm", "canonicalization", "value"]:
        if key not in obj:
            fail(f"{label} missing {key}")
    if obj["algorithm"] != ALGORITHM:
        fail(f"{label} unsupported algorithm: {obj['algorithm']}")
    if obj["canonicalization"] != CANONICALIZATION:
        fail(f"{label} unsupported canonicalization: {obj['canonicalization']}")
    if not HASH_RE.match(obj["value"]):
        fail(f"{label} invalid hash value")


def assert_same_hash(actual, expected, label):
    validate_typed_hash(actual, label)
    validate_typed_hash(expected, label + " expected")
    if actual != expected:
        fail(f"{label} mismatch: expected {expected['value']}, got {actual['value']}")


def validate_artifact_hash(path, hash_obj, label):
    expected = hash_json_file(path)
    assert_same_hash(hash_obj, expected, label)


def validate_evidence_event(event, index):
    prefix = f"Event[{index}]"

    for field in ["event_id", "air_ref", "timestamp", "executor", "event_type", "event_hash"]:
        if field not in event:
            fail(f"{prefix} missing required field: {field}")

    air_ref = event["air_ref"]
    if not isinstance(air_ref, dict):
        fail(f"{prefix} air_ref must be object")
    if "path" not in air_ref or "hash" not in air_ref:
        fail(f"{prefix} air_ref missing path or hash")
    validate_artifact_hash(air_ref["path"], air_ref["hash"], f"{prefix} air_ref.hash")

    if not TIMESTAMP_RE.match(event["timestamp"]):
        fail(f"{prefix} invalid timestamp")

    executor = event["executor"]
    if not isinstance(executor, dict):
        fail(f"{prefix} executor must be object")
    if executor.get("type") not in EXECUTOR_TYPES:
        fail(f"{prefix} invalid executor.type")

    if event["event_type"] not in EVENT_TYPES:
        fail(f"{prefix} invalid event_type")

    if "parent_event_hash" in event:
        validate_typed_hash(event["parent_event_hash"], f"{prefix} parent_event_hash")

    for collection in ["inputs", "outputs"]:
        for i, item in enumerate(event.get(collection, [])):
            if "key" not in item or "hash" not in item:
                fail(f"{prefix} {collection}[{i}] missing key or hash")
            validate_typed_hash(item["hash"], f"{prefix} {collection}[{i}].hash")

    expected_event_hash = hash_event(event)
    assert_same_hash(event["event_hash"], expected_event_hash, f"{prefix} event_hash")


def validate_evidence_file(path):
    events = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(events, list):
        fail("Evidence fixture must be an array of events")
    if not events:
        fail("Evidence fixture must not be empty")

    previous_hash = None

    for index, event in enumerate(events):
        validate_evidence_event(event, index)

        if index == 0:
            if "parent_event_hash" in event:
                fail("Event[0] must not have parent_event_hash")
        else:
            if "parent_event_hash" not in event:
                fail(f"Event[{index}] missing parent_event_hash")
            assert_same_hash(
                event["parent_event_hash"],
                previous_hash,
                f"Event[{index}] parent_event_hash"
            )

        previous_hash = event["event_hash"]


def main():
    ok = True
    paths = sorted(Path("fixtures/evidence").glob("*.events.json"))

    if not paths:
        print("BAD no evidence fixtures found")
        raise SystemExit(1)

    for path in paths:
        try:
            validate_evidence_file(path)
            print(f"OK {path}")
        except Exception as exc:
            ok = False
            print(f"BAD {path}: {exc}")

    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
