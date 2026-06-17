import hashlib
import json
from pathlib import Path

CANONICALIZATION = "json-c14n-v1"
ALGORITHM = "sha256"


def canonical_json(data):
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def typed_sha256(value):
    return {
        "algorithm": ALGORITHM,
        "canonicalization": CANONICALIZATION,
        "value": value,
    }


def hash_json_value(data):
    return typed_sha256(sha256_text(canonical_json(data)))


def hash_json_file(path):
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    return hash_json_value(obj)


def event_without_event_hash(event):
    clone = json.loads(json.dumps(event, ensure_ascii=False))
    clone.pop("event_hash", None)
    return clone


def hash_event(event):
    return hash_json_value(event_without_event_hash(event))


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        raise SystemExit("usage: python scripts/canonical_json.py <json-file>")

    print(hash_json_file(sys.argv[1])["value"])
