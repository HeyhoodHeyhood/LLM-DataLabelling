"""
auto-anno-skill: CLI entry point

Usage:
    python -m annotool.cli --config configs/image.yaml
"""

import argparse
import sys

from annotool.pipeline import run
from annotool.utils import load_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="annotool",
        description="Automatic image annotation using OpenAI Vision API.",
    )
    parser.add_argument(
        "--config",
        required=True,
        metavar="PATH",
        help="Path to YAML config file (e.g. configs/image.yaml)",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    config = load_config(args.config)
    run(config)


if __name__ == "__main__":
    main()
