from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from jinja2 import Environment

REPO_ROOT = Path(__file__).resolve().parents[1]
TASK = shutil.which("task")


@pytest.fixture(params=[False, True], ids=["root", "generated"])
def workflow(request: pytest.FixtureRequest, tmp_path: Path) -> tuple[Path, bool]:
    generated = bool(request.param)
    source = REPO_ROOT / "template/Taskfile.yml.jinja" if generated else REPO_ROOT / "Taskfile.yml"
    text = source.read_text()
    if generated:
        text = Environment().from_string(text).render(package_name="_99_fast_api")
        assert "{{.CLI_ARGS}}" in text
        assert "python -m _99_fast_api.cli" in text
    (tmp_path / "Taskfile.yml").write_text(text)
    return tmp_path, generated


def _stub_tools(root: Path) -> dict[str, str]:
    bindir = root / "bin"
    bindir.mkdir()
    for name in ("uv", "git"):
        path = bindir / name
        path.write_text(
            f"#!{sys.executable}\n"
            "import json, os, sys\n"
            "with open(os.environ['COMMAND_LOG'], 'a') as log:\n"
            "    log.write(json.dumps(sys.argv[1:]) + '\\n')\n"
            "sys.exit(7 if os.environ.get('FAIL_COMMAND') in sys.argv[1:] else 0)\n"
        )
        path.chmod(0o755)
    return {
        **os.environ,
        "PATH": f"{bindir}:{os.environ['PATH']}",
        "COMMAND_LOG": str(root / "log"),
    }


def _commands(root: Path) -> list[list[str]]:
    return [json.loads(line) for line in (root / "log").read_text().splitlines()]


def _task(root: Path, env: dict[str, str], *args: str) -> subprocess.CompletedProcess[str]:
    if TASK is None:
        pytest.skip("Go Task v3 is required for workflow integration tests")
    return subprocess.run([TASK, *args], cwd=root, env=env, capture_output=True, text=True)


def test_task_catalog_and_quoted_arguments(workflow: tuple[Path, bool]) -> None:
    root, _ = workflow
    env = _stub_tools(root)
    for args in [(), ("help",)]:
        result = _task(root, env, *args)
        assert result.returncode == 0, result.stderr
        assert "quality:verify:" in result.stdout
        names = {
            line.split()[1].removesuffix(":")
            for line in result.stdout.splitlines()
            if line.startswith("* ")
        }
        assert {
            "default",
            "help",
            "repo:sync",
            "repo:hooks",
            "quality:verify",
            "quality:check",
            "quality:test",
            "security:scan:staged",
        } <= names
        assert all(":" in name for name in names - {"default", "help"})
    result = _task(root, env, "quality:test", "--", "-k", "smoke or cli")
    assert result.returncode == 0, result.stderr
    assert _commands(root) == [["run", "pytest", "-k", "smoke or cli"]]


@pytest.mark.parametrize(
    ("name", "fail", "expected"),
    [
        ("quality:fmt", "format", [["run", "ruff", "format", "."]]),
        (
            "quality:verify",
            "pyright",
            [
                ["run", "ruff", "format", ".", "--check"],
                ["run", "ruff", "check", "."],
                ["run", "pyright"],
            ],
        ),
        ("quality:check", "format", [["run", "ruff", "format", ".", "--check"]]),
        ("setup", "sync", [["sync", "--group", "dev"]]),
    ],
)
def test_composites_stop_on_failure(
    workflow: tuple[Path, bool], name: str, fail: str, expected: list[list[str]]
) -> None:
    root, generated = workflow
    env = _stub_tools(root)
    env["FAIL_COMMAND"] = fail
    if name == "setup":
        name = "repo:init" if generated else "repo:install"
    result = _task(root, env, name)
    assert result.returncode != 0
    assert _commands(root) == expected


@pytest.mark.parametrize("failure", [None, "security:scan:staged"])
def test_hook_command_order(workflow: tuple[Path, bool], failure: str | None) -> None:
    root, generated = workflow
    env = _stub_tools(root)
    task = root / "bin/task"
    shutil.copyfile(root / "bin/uv", task)
    task.chmod(0o755)
    if failure:
        env["FAIL_COMMAND"] = failure
    source = "template/.githooks/pre-commit.jinja" if generated else ".githooks/pre-commit"
    result = subprocess.run(["/bin/sh", str(REPO_ROOT / source)], cwd=root, env=env)
    assert (result.returncode != 0) == bool(failure)
    expected = [["security:scan:staged"]]
    if not generated and not failure:
        expected.append(["quality:test"])
    assert _commands(root) == expected


@pytest.mark.parametrize("missing", ["uv", "task"])
def test_hooks_report_missing_tools(workflow: tuple[Path, bool], missing: str) -> None:
    root, generated = workflow
    bindir = root / "bin"
    bindir.mkdir()
    present = bindir / ("task" if missing == "uv" else "uv")
    present.write_text("#!/bin/sh\nexit 0\n")
    present.chmod(0o755)
    source = "template/.githooks/pre-commit.jinja" if generated else ".githooks/pre-commit"
    result = subprocess.run(
        ["/bin/sh", str(REPO_ROOT / source)],
        cwd=root,
        env={**os.environ, "PATH": str(bindir)},
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert missing in result.stderr
    assert "PATH" in result.stderr


def test_check_runs_verification_before_rendering(workflow: tuple[Path, bool]) -> None:
    root, generated = workflow
    env = _stub_tools(root)
    result = _task(root, env, "quality:check")
    assert result.returncode == 0, result.stderr
    expected = [
        ["run", "ruff", "format", ".", "--check"],
        ["run", "ruff", "check", "."],
        ["run", "pyright"],
        ["run", "pytest"],
    ]
    if not generated:
        expected.append(["run", "python", "scripts/render_validate.py", "--mode", "full-e2e"])
    assert _commands(root) == expected


def test_setup_syncs_before_installing_hooks(workflow: tuple[Path, bool]) -> None:
    root, generated = workflow
    env = _stub_tools(root)
    home = root / "home"
    (home / "agent-docs").mkdir(parents=True)
    env["HOME"] = str(home)
    result = _task(root, env, "repo:init" if generated else "repo:install")
    assert result.returncode == 0, result.stderr
    expected = [["sync", "--group", "dev"]]
    if generated:
        expected.append(["rev-parse", "--is-inside-work-tree"])
    expected.append(["config", "core.hooksPath", ".githooks"])
    assert _commands(root) == expected
    if generated:
        assert (root / "agent-docs").readlink() == home / "agent-docs"


@pytest.mark.parametrize("existing", ["none", "directory", "file", "symlink", "dangling"])
def test_shared_agent_docs_link(workflow: tuple[Path, bool], existing: str, tmp_path: Path) -> None:
    root, generated = workflow
    if not generated:
        pytest.skip("Shared docs are linked only in generated projects")
    home = tmp_path / "home with spaces"
    shared = home / "agent-docs"
    shared.mkdir(parents=True)
    (shared / "guide.md").write_text("shared docs")
    link = root / "agent-docs"
    other = tmp_path / "other-docs"
    if existing == "directory":
        link.mkdir()
    elif existing == "file":
        link.write_text("keep me")
    elif existing in {"symlink", "dangling"}:
        if existing == "symlink":
            other.mkdir()
        link.symlink_to(other)
    env = {**os.environ, "HOME": str(home)}
    for _ in range(2):
        result = _task(root, env, "repo:agent-docs")
        assert result.returncode == 0, result.stderr
    if existing == "none":
        assert link.readlink() == shared
        assert (link / "guide.md").read_text() == "shared docs"
    elif existing == "directory":
        assert link.is_dir() and not link.is_symlink()
        assert list(link.iterdir()) == []
    elif existing == "file":
        assert link.read_text() == "keep me"
    else:
        assert link.readlink() == other
    assert (shared / "guide.md").read_text() == "shared docs"


def test_missing_shared_docs_can_be_linked_later(workflow: tuple[Path, bool]) -> None:
    root, generated = workflow
    if not generated:
        pytest.skip("Shared docs are linked only in generated projects")
    home = root / "home"
    env = {**os.environ, "HOME": str(home)}
    result = _task(root, env, "repo:agent-docs")
    assert result.returncode == 0, result.stderr
    assert "Skipping link" in result.stdout
    assert not (root / "agent-docs").is_symlink()
    (home / "agent-docs").mkdir(parents=True)
    result = _task(root, env, "repo:agent-docs")
    assert result.returncode == 0, result.stderr
    assert (root / "agent-docs").readlink() == home / "agent-docs"
