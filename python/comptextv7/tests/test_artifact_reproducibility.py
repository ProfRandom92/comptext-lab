from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from scripts.generate_layered_admissibility_artifact import (
    generate_layered_admissibility_artifact,
)
from scripts.generate_multi_family_admissibility_artifact import (
    generate_multi_family_admissibility_artifact,
)


@dataclass(frozen=True)
class DeterministicArtifactSpec:
    """Configuration for a reproducible committed artifact check."""

    name: str
    committed_path: Path
    regenerate: Callable[[Path], Path]


ARTIFACT_SPECS: tuple[DeterministicArtifactSpec, ...] = (
    DeterministicArtifactSpec(
        name="layered_admissibility_results",
        committed_path=Path("artifacts/layered_admissibility_results.json"),
        regenerate=generate_layered_admissibility_artifact,
    ),
    DeterministicArtifactSpec(
        name="multi_family_admissibility_results",
        committed_path=Path("artifacts/multi_family_admissibility_results.json"),
        regenerate=generate_multi_family_admissibility_artifact,
    ),
)


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def test_committed_deterministic_artifacts_are_reproducible(tmp_path: Path) -> None:
    for spec in ARTIFACT_SPECS:
        regenerated_path = tmp_path / spec.committed_path.name
        spec.regenerate(regenerated_path)

        regenerated_payload = _load_json(regenerated_path)
        committed_payload = _load_json(spec.committed_path)

        assert regenerated_payload == committed_payload, (
            f"Deterministic artifact drift detected for '{spec.name}'. "
            f"Regenerate with: python scripts/generate_layered_admissibility_artifact.py"
        )
