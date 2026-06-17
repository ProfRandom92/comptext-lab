from __future__ import annotations

import hashlib
from pathlib import Path

from src.validation.forensic import MAX_ALLOWED_CRITICAL_LOSS, MAX_ALLOWED_HIGH_LOSS, run_forensic_audit
from src.validation.golden_corpus import write_golden_corpus
from src.validation.replay import assert_stable_replay, run_replay
from src.validation.token_telemetry import SUPPORTED_ENCODINGS, count_tokens, drift_fingerprint


def test_golden_corpus_hashes_are_stable() -> None:
    hashes = write_golden_corpus()

    assert set(hashes) == {
        "can_bus_reference.jsonl",
        "scada_reference.jsonl",
        "sparse_alarm_reference.jsonl",
        "mixed_incident_reference.jsonl",
    }
    for filename, digest in hashes.items():
        content = Path("datasets/golden", filename).read_bytes()
        assert hashlib.sha256(content).hexdigest() == digest


def test_token_telemetry_supports_required_encodings_deterministically() -> None:
    text = "2026-01-01T00:00:02Z CRITICAL source=PLC-7 VALVE-STUCK anchor=ANOM-SCADA-VALVE-0001"

    first = [count_tokens(text, encoding) for encoding in SUPPORTED_ENCODINGS]
    second = [count_tokens(text, encoding) for encoding in SUPPORTED_ENCODINGS]

    assert [item.count for item in first] == [item.count for item in second]
    assert [item.digest for item in first] == [item.digest for item in second]
    assert drift_fingerprint() == drift_fingerprint()


def test_forensic_audit_preserves_anomalies_and_thresholds() -> None:
    write_golden_corpus()
    results = run_forensic_audit()

    assert MAX_ALLOWED_CRITICAL_LOSS == 0
    assert MAX_ALLOWED_HIGH_LOSS == 0
    assert results
    assert all(result.passed for result in results)
    assert all(result.anomaly_survivability == 1.0 for result in results)
    assert all(result.anchor_retention == 1.0 for result in results)


def test_replay_hashes_are_stable_across_passes() -> None:
    write_golden_corpus()
    passes = run_replay(passes=3)

    assert_stable_replay(passes)
    assert len(passes) == 12
