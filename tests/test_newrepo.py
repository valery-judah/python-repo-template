from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

LAUNCHER = Path(__file__).resolve().parents[1] / "scripts/devex/newrepo"
BASH = shutil.which("bash") or "/bin/bash"


@pytest.fixture
def launcher_env(tmp_path: Path) -> dict[str, str]:
    bindir = tmp_path / "bin"
    bindir.mkdir()
    for name in ("uvx", "task", "git"):
        executable = bindir / name
        executable.write_text(
            f"#!{sys.executable}\n"
            "import json, os, sys\n"
            "from pathlib import Path\n"
            "name = Path(sys.argv[0]).name\n"
            "with open(os.environ['COMMAND_LOG'], 'a') as log:\n"
            "    log.write(json.dumps([name, os.getcwd(), sys.argv[1:]]) + '\\n')\n"
            "sys.exit(7 if os.environ.get('FAIL_TOOL') == name else 0)\n"
        )
        executable.chmod(0o755)
    return {
        **os.environ,
        "HOME": str(tmp_path / "home"),
        "PATH": f"{bindir}:{os.environ['PATH']}",
        "COMMAND_LOG": str(tmp_path / "commands.jsonl"),
    }


def run_launcher(
    cwd: Path, env: dict[str, str], *args: str, launcher: Path = LAUNCHER
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [BASH, str(launcher), *args], cwd=cwd, env=env, text=True, capture_output=True
    )


@pytest.mark.parametrize("absolute", [False, True])
def test_registered_launcher_creates_and_initializes(
    tmp_path: Path, launcher_env: dict[str, str], absolute: bool
) -> None:
    result = run_launcher(tmp_path, launcher_env, "--register")
    assert result.returncode == 0, result.stderr
    registered = Path(launcher_env["HOME"]) / ".local/bin/newrepo"
    assert registered.resolve() == LAUNCHER
    assert 'export PATH="$HOME/.local/bin:$PATH"' in result.stdout
    assert run_launcher(tmp_path, launcher_env, "--register").returncode == 0
    destination = tmp_path / "parent with spaces/sample-app"
    arg = str(destination) if absolute else "parent with spaces/sample-app/"
    result = run_launcher(tmp_path, launcher_env, arg, launcher=registered)
    assert result.returncode == 0, result.stderr
    commands = [
        json.loads(line) for line in Path(launcher_env["COMMAND_LOG"]).read_text().splitlines()
    ]
    assert commands == [
        [
            "uvx",
            str(tmp_path),
            [
                "copier",
                "copy",
                "--trust",
                "-l",
                "--vcs-ref",
                "HEAD",
                str(LAUNCHER.parents[2]),
                str(destination),
            ],
        ],
        ["task", str(destination), ["repo:init"]],
    ]
    assert "Next: cd " in result.stdout


@pytest.mark.parametrize("symlink", [False, True])
def test_registration_preserves_existing_command(
    tmp_path: Path, launcher_env: dict[str, str], symlink: bool
) -> None:
    registered = Path(launcher_env["HOME"]) / ".local/bin/newrepo"
    registered.parent.mkdir(parents=True)
    if symlink:
        registered.symlink_to(tmp_path / "missing")
    else:
        registered.write_text("existing command")
    result = run_launcher(tmp_path, launcher_env, "--register")
    assert result.returncode != 0
    assert "Refusing to replace" in result.stderr
    if symlink:
        assert registered.readlink() == tmp_path / "missing"
    else:
        assert registered.read_text() == "existing command"


@pytest.mark.parametrize("symlink", [False, True])
def test_existing_destination_is_untouched(
    tmp_path: Path, launcher_env: dict[str, str], symlink: bool
) -> None:
    destination = tmp_path / "existing"
    if symlink:
        destination.symlink_to(tmp_path / "missing")
    else:
        destination.mkdir()
        (destination / "keep").write_text("original")
    result = run_launcher(tmp_path, launcher_env, "existing/")
    assert result.returncode != 0
    assert "Destination already exists" in result.stderr
    assert not Path(launcher_env["COMMAND_LOG"]).exists()
    if not symlink:
        assert (destination / "keep").read_text() == "original"


@pytest.mark.parametrize("failure", ["uvx", "task"])
def test_failure_stops_initialization(
    tmp_path: Path, launcher_env: dict[str, str], failure: str
) -> None:
    launcher_env["FAIL_TOOL"] = failure
    result = run_launcher(tmp_path, launcher_env, "sample-app")
    assert result.returncode == 7
    assert "Initialization failed; files remain" in result.stderr
    assert "Created " not in result.stdout
    commands = Path(launcher_env["COMMAND_LOG"]).read_text().splitlines()
    assert len(commands) == (1 if failure == "uvx" else 2)


@pytest.mark.parametrize("missing", ["uvx", "task", "git"])
def test_missing_prerequisite_prevents_creation(
    tmp_path: Path, launcher_env: dict[str, str], missing: str
) -> None:
    bindir = tmp_path / "isolated-bin"
    bindir.mkdir()
    for name in ("dirname", "basename", "uvx", "task", "git"):
        if name == missing:
            continue
        source = shutil.which(name, path=launcher_env["PATH"])
        assert source is not None
        (bindir / name).symlink_to(source)
    launcher_env["PATH"] = str(bindir)
    result = run_launcher(tmp_path, launcher_env, "sample-app")
    assert result.returncode != 0
    assert f"Missing required executable: {missing}" in result.stderr
    assert not (tmp_path / "sample-app").exists()
