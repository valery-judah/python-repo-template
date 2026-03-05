from __future__ import annotations

import importlib.util
import shutil
import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import cast

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_to_package_name() -> Callable[[str], str]:
    module_path = REPO_ROOT / "copier_extensions.py"
    spec = importlib.util.spec_from_file_location("copier_extensions", module_path)
    if spec is None or spec.loader is None:
        raise AssertionError("Failed to load copier_extensions.py for render validation.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return cast(Callable[[str], str], module.to_package_name)


to_package_name = _load_to_package_name()

SLUGS = ("sample-app", "99-fast-api")
SCAFFOLD_COMMANDS = (
    ("make", "install"),
    ("make", "test"),
    ("make", "lint"),
    ("make", "type"),
    ("make", "secret-scan"),
)
FORBIDDEN_SNIPPETS = (
    "from template",
    "import template",
    "template.cli",
    "template.devtools",
    "src/template",
    'version("template")',
    "python -m template",
)


def _run(command: tuple[str, ...], cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def _render(repo_root: Path, dest: Path, repo_slug: str) -> None:
    _run(
        (
            "uv",
            "run",
            "copier",
            "copy",
            "--trust",
            str(repo_root),
            str(dest),
            "--data",
            f"repo_slug={repo_slug}",
            "--defaults",
        ),
        cwd=repo_root,
    )


def _assert_destination_layout(dest: Path) -> None:
    if not (dest / "pyproject.toml").is_file():
        raise AssertionError("Rendered repo is missing pyproject.toml at its root.")
    if (dest / "template").exists():
        raise AssertionError("Rendered repo leaked the internal template/ directory.")


def _init_git_repo(dest: Path) -> None:
    _run(("git", "init"), cwd=dest)
    _run(("git", "add", "."), cwd=dest)


def _assert_no_hard_coded_template_refs(dest: Path, package_name: str) -> None:
    for path in dest.rglob("*"):
        if not path.is_file():
            continue
        if path.name == "uv.lock":
            continue
        if path.suffix not in {".py", ".md", ".toml", ".txt", ""} and path.name != "Makefile":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for snippet in FORBIDDEN_SNIPPETS:
            if snippet in text:
                raise AssertionError(f"Found stale template reference {snippet!r} in {path}.")
    if not (dest / "src" / package_name).is_dir():
        raise AssertionError("Rendered repo is missing the derived package directory.")


def main() -> int:
    if shutil.which("uv") is None:
        raise RuntimeError("uv is required to run render validation.")

    with tempfile.TemporaryDirectory(prefix="python-repo-template-") as tmp_dir:
        base_dir = Path(tmp_dir)
        for repo_slug in SLUGS:
            dest = base_dir / repo_slug
            package_name = to_package_name(repo_slug)
            _render(repo_root=REPO_ROOT, dest=dest, repo_slug=repo_slug)
            _assert_destination_layout(dest=dest)
            _init_git_repo(dest=dest)
            _assert_no_hard_coded_template_refs(dest=dest, package_name=package_name)
            for command in SCAFFOLD_COMMANDS:
                _run(command, cwd=dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
