from __future__ import annotations

import json

import pytest

from src.core.kvtc_v7 import KVTCV7Engine


def _sample_xentry_log(repetitions: int = 45) -> str:
    lines: list[str] = []
    for idx in range(repetitions):
        second = idx % 60
        severity = "ERROR" if idx % 3 else "WARN"
        lines.append(
            "2026-05-10T12:00:{second:02d}Z {severity} ECU=MCM DTC:P0301 SPN 1234 FMI 5 "
            "engine misfire cylinder=1 temperature=97C pressure=2.4bar voltage=23.9V "
            "XENTRY guided-test says combustion irregularity detected on cylinder one"
            .format(second=second, severity=severity)
        )
    return "\n".join(lines)


def test_compress_builds_four_layers_and_valid_json_payload() -> None:
    engine = KVTCV7Engine(window_seconds=30)

    result = engine.compress(_sample_xentry_log())
    payload = json.loads(result.text)

    assert payload["v"] == "KVTC7"
    assert payload["h"]["n"] == 45
    assert payload["d"]
    assert payload["m"]
    assert payload["w"]["s"] == 30
    assert result.header.event_count == 45
    assert result.middle.families
    assert result.window.bursts
    assert result.frame.dictionary


def test_extreme_consonant_mapping_preserves_diagnostic_entropy() -> None:
    engine = KVTCV7Engine()

    signature = engine.extreme_consonant_map("engine misfire cylinder=1 temperature=97C P0301 voltage=24V")

    assert "ENG" in signature
    assert "MSFR" in signature
    assert "P0301" in signature
    assert "97C" in signature
    assert "AE" not in signature


def test_family_consonant_mapping_collapses_drifting_measurements() -> None:
    engine = KVTCV7Engine()

    first = engine.extreme_consonant_map(
        "ECU=MCM P0301 engine misfire cylinder=1 temperature=97C pressure=2.4bar voltage=23.9V",
        preserve_measurements=False,
        family_mode=True,
    )
    second = engine.extreme_consonant_map(
        "ECU=MCM P0301 engine misfire cylinder=1 temperature=103C pressure=2.9bar voltage=24.4V",
        preserve_measurements=False,
        family_mode=True,
    )

    assert first == second
    assert "P0301" in first
    assert "#C" in first
    assert "#BAR" in first
    assert "97C" not in first
    assert "103C" not in first


def test_ecu_field_value_is_used_as_event_context() -> None:
    engine = KVTCV7Engine()

    result = engine.compress("2026-05-10T12:00:00Z ERROR ECU=MCM P0301 engine misfire voltage=24V")

    assert result.events[0].ecu == "MCM"
    assert result.middle.families[0].startswith("MCM:ERR:P0301")


def test_compression_reduces_repetitive_xentry_logs_below_target_budget() -> None:
    engine = KVTCV7Engine(window_seconds=60, max_families=4, max_bursts=2)

    result = engine.compress(_sample_xentry_log(repetitions=80))

    assert result.original_tokens > 1_000
    assert result.compressed_tokens < 100
    assert result.reduction_percent >= 95.0


def test_sparse_micro_frame_avoids_metadata_expansion_for_tiny_notes() -> None:
    engine = KVTCV7Engine()

    result = engine.compress(
        "\n".join(
            (
                "2026-05-10T15:00:00Z INFO ECU=MCM startup complete voltage=24.1V",
                "2026-05-10T15:00:03Z WARN ECU=ABS C0035 intermittent wheel speed sensor",
                "manual note: customer reports rare vibration after pothole impact",
            )
        )
    )
    assert result.text.startswith("K7m|")
    assert result.compressed_tokens < result.original_tokens
    assert result.frame.dictionary


def test_invalid_engine_configuration_is_rejected() -> None:
    with pytest.raises(ValueError):
        KVTCV7Engine(window_seconds=0)
