import argparse
import json
from pathlib import Path

from .build import build_demo


def main() -> None:
    parser = argparse.ArgumentParser(description="Build PressLens's deterministic simulated analytics snapshot.")
    parser.add_argument("--output-dir", type=Path, default=Path("data/demo"))
    parser.add_argument("--sessions", type=int, default=6000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    print(json.dumps(build_demo(args.output_dir, count=args.sessions, seed=args.seed), indent=2))


if __name__ == "__main__":
    main()
