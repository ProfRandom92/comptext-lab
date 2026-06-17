"""Run the AEI-aligned industrial economic resilience audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.audit import run_industrial_economic_resilience_audit  # noqa: E402


def print_markdown(result) -> None:
    print(f"# {result.title}")
    print()
    print("Synthetic deterministic audit probes; not vendor certification data.")
    print()
    print(
        "| AEI category | scenario | target | measured | pass | Daimler Truck relevance |"
    )
    print("| --- | --- | ---: | ---: | :---: | --- |")
    for scenario in result.scenarios:
        print(
            "| {aei_category} | {title} | {target_value:g} {unit} | {measured_value:.4g} {unit} | {passed} | {daimler_relevance} |".format(
                **scenario.as_dict()
            )
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=3, help="Measured repetitions for latency probes (default: 3).")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of Markdown.")
    args = parser.parse_args()

    result = run_industrial_economic_resilience_audit(iterations=args.iterations)
    if args.json:
        print(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    else:
        print_markdown(result)


if __name__ == "__main__":
    main()
