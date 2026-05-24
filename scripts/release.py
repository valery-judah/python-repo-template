from __future__ import annotations

import argparse
import re
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REMOTE = "origin"
VERSION_TAG_PATTERN = re.compile(r"^v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


class ReleaseError(RuntimeError):
    """Raised when git-backed release actions cannot complete."""


@dataclass(frozen=True, order=True)
class SemVer:
    major: int
    minor: int
    patch: int


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create the next semantic release tag from existing git tags."
    )
    parser.add_argument("bump", choices=("patch", "minor", "major"))
    parser.add_argument("--remote", default=DEFAULT_REMOTE, help="Git remote to fetch and push.")
    parser.add_argument(
        "--no-fetch",
        action="store_true",
        help="Skip `git fetch --tags` before calculating the next release tag.",
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help="Push the current branch and the created tag to the configured remote.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the next tag without creating or pushing it.",
    )
    return parser.parse_args(argv)


def parse_version_tag(tag: str) -> SemVer | None:
    match = VERSION_TAG_PATTERN.fullmatch(tag.strip())
    if match is None:
        return None
    major, minor, patch = (int(part) for part in match.groups())
    return SemVer(major=major, minor=minor, patch=patch)


def format_version_tag(version: SemVer) -> str:
    return f"v{version.major}.{version.minor}.{version.patch}"


def latest_version_tag(tags: Sequence[str]) -> SemVer | None:
    versions = [version for tag in tags if (version := parse_version_tag(tag)) is not None]
    if not versions:
        return None
    return max(versions)


def bump_version(version: SemVer, bump: str) -> SemVer:
    if bump == "patch":
        return SemVer(version.major, version.minor, version.patch + 1)
    if bump == "minor":
        return SemVer(version.major, version.minor + 1, 0)
    if bump == "major":
        return SemVer(version.major + 1, 0, 0)
    raise AssertionError(f"Unsupported bump kind: {bump!r}.")


def determine_next_tag(tags: Sequence[str], bump: str) -> tuple[str | None, str]:
    latest = latest_version_tag(tags)
    if latest is None:
        latest_label = None
        base_version = SemVer(0, 0, 0)
    else:
        latest_label = format_version_tag(latest)
        base_version = latest
    next_tag = format_version_tag(bump_version(base_version, bump))
    return latest_label, next_tag


def _run_git(*args: str) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() or exc.stdout.strip() or f"git {' '.join(args)} failed"
        raise ReleaseError(detail) from exc
    return completed.stdout.strip()


def fetch_tags(remote: str) -> None:
    _run_git("fetch", "--tags", remote)


def list_tags() -> list[str]:
    output = _run_git("tag", "--list")
    return [line.strip() for line in output.splitlines() if line.strip()]


def create_tag(tag: str) -> None:
    _run_git("tag", tag)


def current_branch() -> str:
    return _run_git("branch", "--show-current").strip()


def push_release(remote: str, branch: str, tag: str) -> None:
    _run_git("push", remote, branch)
    _run_git("push", remote, tag)


def run_release(args: argparse.Namespace) -> int:
    if not args.no_fetch:
        fetch_tags(args.remote)

    latest_tag, next_tag = determine_next_tag(list_tags(), args.bump)
    latest_display = latest_tag if latest_tag is not None else "none"
    print(f"Latest tag: {latest_display}")
    print(f"Next tag: {next_tag}")

    if args.dry_run:
        return 0

    create_tag(next_tag)
    print(f"Created tag: {next_tag}")

    if not args.push:
        return 0

    branch = current_branch()
    if not branch:
        raise ReleaseError("Cannot push a release from detached HEAD.")
    push_release(args.remote, branch, next_tag)
    print(f"Pushed branch `{branch}` and tag `{next_tag}` to `{args.remote}`.")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        return run_release(args)
    except ReleaseError as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    raise SystemExit(main())
