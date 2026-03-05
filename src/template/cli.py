from __future__ import annotations

import argparse

from template import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="template", description="Project CLI entrypoint.")
    parser.add_argument("--version", action="store_true", help="Print version and exit.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.version:
        print(__version__)
        return 0

    try:
        from rich.console import Console  # type: ignore[import-not-found]

        console = Console(
            force_terminal=False,
            color_system=None,
            markup=False,
            highlight=False,
        )
        console.print("template: OK")
    except ModuleNotFoundError:
        print("template: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
