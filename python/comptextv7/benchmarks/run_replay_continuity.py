"""Generate CompText V7 replay continuity benchmark artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.validation.replay_continuity import write_benchmark_artifacts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=100, help="Replay chain length; supports 10, 25, 50, and 100 iteration adversarial chains.")
    parser.add_argument("--output-dir", type=Path, default=Path("reports/replay_continuity"))
    args = parser.parse_args()
    paths = write_benchmark_artifacts(args.output_dir, iterations=args.iterations)
    print(json.dumps({key: str(value) for key, value in paths.items()}, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
