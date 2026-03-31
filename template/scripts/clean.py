from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CleanupTarget:
    relative_path: str
    kind: str


STATIC_TARGETS: tuple[CleanupTarget, ...] = (
    CleanupTarget(".pytest_cache", "dir"),
    CleanupTarget(".ruff_cache", "dir"),
    CleanupTarget(".mypy_cache", "dir"),
    CleanupTarget(".pyright", "dir"),
    CleanupTarget("htmlcov", "dir"),
    CleanupTarget("build", "dir"),
    CleanupTarget("dist", "dir"),
    CleanupTarget("pyright_output.json", "file"),
    CleanupTarget(".coverage", "file"),
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def iter_targets(root: Path) -> list[CleanupTarget]:
    targets: dict[tuple[str, str], CleanupTarget] = {}

    for target in STATIC_TARGETS:
        path = root / target.relative_path
        if path.exists():
            targets[(target.relative_path, target.kind)] = target

    for path in root.glob(".coverage.*"):
        if path.is_file():
            target = CleanupTarget(str(path.relative_to(root)), "file")
            targets[(target.relative_path, target.kind)] = target

    for path in root.rglob("__pycache__"):
        if path.is_dir():
            target = CleanupTarget(str(path.relative_to(root)), "dir")
            targets[(target.relative_path, target.kind)] = target

    for path in root.glob(".venv*"):
        if path.is_dir():
            target = CleanupTarget(str(path.relative_to(root)), "dir")
            targets[(target.relative_path, target.kind)] = target

    for path in root.glob("*.egg-info"):
        if path.is_dir():
            target = CleanupTarget(str(path.relative_to(root)), "dir")
            targets[(target.relative_path, target.kind)] = target

    return sorted(targets.values(), key=lambda target: target.relative_path)


def remove_target(root: Path, target: CleanupTarget) -> None:
    path = root / target.relative_path
    if target.kind == "dir":
        shutil.rmtree(path)
    else:
        path.unlink()


def main() -> int:
    root = repo_root()
    targets = iter_targets(root)

    if not targets:
        print("Nothing to remove.")
        return 0

    for target in targets:
        remove_target(root, target)

    print(f"Removed {len(targets)} path(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
