from __future__ import annotations

import argparse
import importlib.util
import shutil
import subprocess
import tempfile
import tomllib
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import cast

REPO_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_EXCLUDES = (
    ".git",
    ".venv",
    ".venv-*",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".pyright",
)


def _load_to_package_name() -> Callable[[str], str]:
    module_path = REPO_ROOT / "copier_extensions.py"
    spec = importlib.util.spec_from_file_location("copier_extensions", module_path)
    if spec is None or spec.loader is None:
        raise AssertionError("Failed to load copier_extensions.py for render validation.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return cast(Callable[[str], str], module.to_package_name)


to_package_name = _load_to_package_name()

FORBIDDEN_SNIPPETS = (
    "from template",
    "import template",
    "template.cli",
    "template.devtools",
    "src/template",
    'version("template")',
    "python -m template",
)
TEXT_FILE_SUFFIXES = {".md", ".py", ".toml", ".txt", ""}
INIT_COMMANDS = (("make", "init"),)
CHECK_COMMANDS = (
    ("uv", "run", "poe", "verify"),
    ("uv", "run", "poe", "run"),
    ("uv", "run", "poe", "secret-scan"),
    ("uv", "run", "poe", "build"),
)


@dataclass(frozen=True)
class Scenario:
    repo_slug: str
    repo_name: str

    @property
    def package_name(self) -> str:
        return to_package_name(self.repo_slug)


@dataclass(frozen=True)
class RenderedRepo:
    scenario: Scenario
    root: Path

    @property
    def repo_slug(self) -> str:
        return self.scenario.repo_slug

    @property
    def repo_name(self) -> str:
        return self.scenario.repo_name

    @property
    def package_name(self) -> str:
        return self.scenario.package_name


SCENARIOS = (
    Scenario(repo_slug="sample-app", repo_name="Sample App"),
    Scenario(repo_slug="99-fast-api", repo_name="99 Fast Api"),
)
SCENARIOS_BY_SLUG = {scenario.repo_slug: scenario for scenario in SCENARIOS}

Assertion = Callable[[RenderedRepo], None]
Command = tuple[str, ...]


@dataclass(frozen=True)
class ValidationMode:
    name: str
    pre_command_assertion_groups: tuple[str, ...]
    post_init_assertion_groups: tuple[str, ...]
    commands: tuple[Command, ...]


def _run(command: tuple[str, ...], cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def _create_source_snapshot(repo_root: Path, base_dir: Path) -> Path:
    snapshot_root = base_dir / "_template_source"
    if snapshot_root.exists():
        return snapshot_root
    shutil.copytree(
        repo_root,
        snapshot_root,
        ignore=shutil.ignore_patterns(*SNAPSHOT_EXCLUDES),
    )
    return snapshot_root


def _render(source_root: Path, dest: Path, scenario: Scenario) -> None:
    _run(
        (
            "uv",
            "run",
            "copier",
            "copy",
            "--trust",
            str(source_root),
            str(dest),
            "--data",
            f"repo_slug={scenario.repo_slug}",
            "--data",
            f"repo_name={scenario.repo_name}",
            "--defaults",
        ),
        cwd=source_root,
    )


def _init_git_repo(dest: Path) -> None:
    _run(("git", "init"), cwd=dest)
    _run(("git", "add", "."), cwd=dest)


def _iter_text_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.name == "uv.lock":
            continue
        if path.name == "Makefile" or path.suffix in TEXT_FILE_SUFFIXES:
            yield path


def _read_pyproject(dest: Path) -> dict[str, object]:
    with (dest / "pyproject.toml").open("rb") as handle:
        return cast(dict[str, object], tomllib.load(handle))


def _assert_destination_layout(repo: RenderedRepo) -> None:
    if not (repo.root / "pyproject.toml").is_file():
        raise AssertionError("Rendered repo is missing pyproject.toml at its root.")
    if (repo.root / "template").exists():
        raise AssertionError("Rendered repo leaked the internal template/ directory.")
    if not (repo.root / "src" / repo.package_name).is_dir():
        raise AssertionError("Rendered repo is missing the derived package directory.")


def _assert_required_files(repo: RenderedRepo) -> None:
    required_paths = (
        repo.root / "AGENTS.md",
        repo.root / "CONTRIBUTING.md",
        repo.root / "SECURITY.md",
        repo.root / ".githooks" / "pre-commit",
        repo.root / "poe_tasks.toml",
        repo.root / "scripts" / "clean.py",
        repo.root / "tests" / "test_cli_smoke.py",
        repo.root / "tests" / "test_secret_scan.py",
        repo.root / "src" / repo.package_name / "cli.py",
        repo.root / "src" / repo.package_name / "__init__.py",
        repo.root / "src" / repo.package_name / "devtools" / "secret_scan.py",
    )
    for path in required_paths:
        if not path.exists():
            raise AssertionError(f"Rendered repo is missing required path: {path}")


def _assert_no_hard_coded_template_refs(repo: RenderedRepo) -> None:
    for path in _iter_text_files(repo.root):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for snippet in FORBIDDEN_SNIPPETS:
            if snippet in text:
                raise AssertionError(f"Found stale template reference {snippet!r} in {path}.")


def _assert_project_metadata(repo: RenderedRepo) -> None:
    pyproject = _read_pyproject(repo.root)
    project = cast(dict[str, object], pyproject["project"])
    scripts = cast(dict[str, str], project["scripts"])
    tool = cast(dict[str, object], pyproject["tool"])

    if project["name"] != repo.repo_slug:
        raise AssertionError(
            f"Expected [project].name to be {repo.repo_slug!r}, got {project['name']!r}."
        )

    entrypoint = scripts.get(repo.package_name)
    if entrypoint != f"{repo.package_name}.cli:main":
        raise AssertionError(
            f"Expected console script for {repo.package_name!r}, got {entrypoint!r}."
        )

    poe_config = cast(dict[str, str], tool.get("poe", {}))
    if poe_config.get("include") != "poe_tasks.toml":
        raise AssertionError("Expected pyproject to include poe_tasks.toml via [tool.poe].")


def _assert_readme_identity(repo: RenderedRepo) -> None:
    readme_text = (repo.root / "README.md").read_text(encoding="utf-8")
    if f"# {repo.repo_name}" not in readme_text:
        raise AssertionError("Rendered README is missing the expected project heading.")
    if repo.package_name not in readme_text:
        raise AssertionError("Rendered README is missing the expected package name.")


def _assert_init_artifacts(repo: RenderedRepo) -> None:
    if not (repo.root / "uv.lock").is_file():
        raise AssertionError("Expected make init to create uv.lock.")


ASSERTION_GROUPS: dict[str, tuple[Assertion, ...]] = {
    "render": (
        _assert_destination_layout,
        _assert_required_files,
        _assert_no_hard_coded_template_refs,
        _assert_project_metadata,
        _assert_readme_identity,
    ),
    "init": (_assert_init_artifacts,),
}
VALIDATION_MODES: dict[str, ValidationMode] = {
    "render-only": ValidationMode(
        name="render-only",
        pre_command_assertion_groups=("render",),
        post_init_assertion_groups=(),
        commands=(),
    ),
    "init": ValidationMode(
        name="init",
        pre_command_assertion_groups=("render",),
        post_init_assertion_groups=("init",),
        commands=INIT_COMMANDS,
    ),
    "full-e2e": ValidationMode(
        name="full-e2e",
        pre_command_assertion_groups=("render",),
        post_init_assertion_groups=("init",),
        commands=INIT_COMMANDS + CHECK_COMMANDS,
    ),
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render and validate generated scaffold repos.")
    parser.add_argument(
        "--mode",
        choices=tuple(VALIDATION_MODES),
        default="full-e2e",
        help="Validation depth to run against rendered repos.",
    )
    parser.add_argument(
        "--scenario",
        action="append",
        dest="scenarios",
        metavar="REPO_SLUG",
        help="Limit validation to one or more named scenarios.",
    )
    return parser.parse_args(argv)


def _select_scenarios(selected_slugs: list[str] | None) -> tuple[Scenario, ...]:
    if not selected_slugs:
        return SCENARIOS

    selected: list[Scenario] = []
    for repo_slug in selected_slugs:
        scenario = SCENARIOS_BY_SLUG.get(repo_slug)
        if scenario is None:
            available = ", ".join(sorted(SCENARIOS_BY_SLUG))
            raise SystemExit(f"Unknown scenario {repo_slug!r}. Available scenarios: {available}.")
        selected.append(scenario)
    return tuple(selected)


def _run_assertion_group(group_name: str, repo: RenderedRepo) -> None:
    for assertion in ASSERTION_GROUPS[group_name]:
        assertion(repo)


def _run_validation_mode(mode: ValidationMode, repo: RenderedRepo) -> None:
    for group_name in mode.pre_command_assertion_groups:
        print(f"==> {repo.repo_slug}: assert {group_name}")
        _run_assertion_group(group_name=group_name, repo=repo)

    init_completed = False
    for command in mode.commands:
        print(f"==> {repo.repo_slug}: {' '.join(command)}")
        _run(command, cwd=repo.root)
        if command in INIT_COMMANDS and not init_completed:
            for group_name in mode.post_init_assertion_groups:
                print(f"==> {repo.repo_slug}: assert {group_name}")
                _run_assertion_group(group_name=group_name, repo=repo)
            init_completed = True


def _run_scenario(scenario: Scenario, base_dir: Path, mode: ValidationMode) -> None:
    dest = base_dir / scenario.repo_slug
    source_root = _create_source_snapshot(repo_root=REPO_ROOT, base_dir=base_dir)
    print(f"==> render {scenario.repo_slug}")
    _render(source_root=source_root, dest=dest, scenario=scenario)
    _init_git_repo(dest=dest)

    rendered_repo = RenderedRepo(scenario=scenario, root=dest)
    _run_validation_mode(mode=mode, repo=rendered_repo)


def main(argv: list[str] | None = None) -> int:
    if shutil.which("uv") is None:
        raise RuntimeError("uv is required to run render validation.")

    args = parse_args(argv)
    mode = VALIDATION_MODES[args.mode]
    scenarios = _select_scenarios(args.scenarios)

    with tempfile.TemporaryDirectory(prefix="python-repo-template-") as tmp_dir:
        base_dir = Path(tmp_dir)
        for scenario in scenarios:
            _run_scenario(scenario=scenario, base_dir=base_dir, mode=mode)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
