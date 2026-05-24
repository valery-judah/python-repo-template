from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest


def _load_render_validate_module() -> Any:
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "render_validate.py"
    spec = importlib.util.spec_from_file_location("render_validate", module_path)
    if spec is None or spec.loader is None:
        raise AssertionError("Failed to load scripts/render_validate.py for testing.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


render_validate = _load_render_validate_module()


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _make_rendered_repo(tmp_path: Path) -> Any:
    scenario = render_validate.Scenario(repo_slug="sample-app", repo_name="Sample App")
    root = tmp_path / scenario.repo_slug

    _write_text(
        root / "pyproject.toml",
        """
[project]
name = "sample-app"

[project.scripts]
sample_app = "sample_app.cli:main"

[tool.poe]
include = "poe_tasks.toml"
""".strip()
        + "\n",
    )
    _write_text(root / "README.md", "# Sample App\n\nPackage: sample_app\n")
    _write_text(root / "AGENTS.md", "# Agents\n")
    _write_text(root / "CONTRIBUTING.md", "# Contributing\n")
    _write_text(root / "SECURITY.md", "# Security\n")
    _write_text(root / "docs" / "README.md", "# Documentation Index\n")
    _write_text(root / "docs" / "evergreen" / "mvp.md", "# MVP\n")
    _write_text(root / "docs" / "evergreen" / "architecture.md", "# Architecture\n")
    _write_text(root / "docs" / "evergreen" / "api-contracts.md", "# API Contracts\n")
    _write_text(root / "docs" / "evergreen" / "runbook.md", "# Runbook\n")
    _write_text(root / "docs" / "product" / "spec.md", "# Product Spec\n")
    _write_text(root / "docs" / "product" / "concepts.md", "# Product Concepts\n")
    _write_text(root / ".githooks" / "pre-commit", "#!/bin/sh\n")
    _write_text(root / "poe_tasks.toml", '[tasks.verify]\ncmd = "pytest"\n')
    _write_text(root / "scripts" / "clean.py", "print('clean')\n")
    _write_text(root / "tests" / "test_cli_smoke.py", "from sample_app.cli import main\n")
    _write_text(
        root / "tests" / "test_secret_scan.py", "from sample_app.devtools.secret_scan import main\n"
    )
    _write_text(root / "src" / "sample_app" / "__init__.py", '__all__ = ["__version__"]\n')
    _write_text(root / "src" / "sample_app" / "cli.py", 'print("sample_app")\n')
    _write_text(root / "src" / "sample_app" / "devtools" / "__init__.py", "")
    _write_text(root / "src" / "sample_app" / "devtools" / "secret_scan.py", "PATTERNS = []\n")

    return render_validate.RenderedRepo(scenario=scenario, root=root)


def test_project_metadata_assertion_accepts_expected_values(tmp_path: Path) -> None:
    repo = _make_rendered_repo(tmp_path)

    render_validate._assert_project_metadata(repo)


def test_readme_identity_assertion_rejects_missing_heading(tmp_path: Path) -> None:
    repo = _make_rendered_repo(tmp_path)
    _write_text(repo.root / "README.md", "# Wrong Name\n\nPackage: sample_app\n")

    with pytest.raises(AssertionError, match="expected project heading"):
        render_validate._assert_readme_identity(repo)


def test_template_reference_assertion_rejects_stale_identity(tmp_path: Path) -> None:
    repo = _make_rendered_repo(tmp_path)
    _write_text(repo.root / "docs" / "bad.md", "import template\n")

    with pytest.raises(AssertionError, match="stale template reference"):
        render_validate._assert_no_hard_coded_template_refs(repo)


def test_init_artifacts_assertion_requires_lockfile(tmp_path: Path) -> None:
    repo = _make_rendered_repo(tmp_path)

    with pytest.raises(AssertionError, match="make init to create uv.lock"):
        render_validate._assert_init_artifacts(repo)


def test_required_files_assertion_rejects_missing_secret_scan(tmp_path: Path) -> None:
    repo = _make_rendered_repo(tmp_path)
    (repo.root / "src" / "sample_app" / "devtools" / "secret_scan.py").unlink()

    with pytest.raises(AssertionError, match="missing required path"):
        render_validate._assert_required_files(repo)


def test_required_files_assertion_rejects_missing_docs_scaffold(tmp_path: Path) -> None:
    repo = _make_rendered_repo(tmp_path)
    (repo.root / "docs" / "evergreen" / "runbook.md").unlink()

    with pytest.raises(AssertionError, match="missing required path"):
        render_validate._assert_required_files(repo)


def test_parse_args_defaults_to_full_e2e() -> None:
    args = render_validate.parse_args([])

    assert args.mode == "full-e2e"
    assert args.scenarios is None
    assert args.template_source == "local"
    assert args.published_template_source == render_validate.DEFAULT_PUBLISHED_TEMPLATE_SOURCE


def test_select_scenarios_rejects_unknown_slug() -> None:
    with pytest.raises(SystemExit, match="Unknown scenario"):
        render_validate._select_scenarios(["missing"])


def test_select_scenarios_preserves_requested_order() -> None:
    scenarios = render_validate._select_scenarios(["99-fast-api", "sample-app"])

    assert [scenario.repo_slug for scenario in scenarios] == ["99-fast-api", "sample-app"]


def test_run_validation_mode_runs_init_assertions_after_init_command(tmp_path: Path) -> None:
    repo = _make_rendered_repo(tmp_path)
    mode = render_validate.VALIDATION_MODES["init"]
    calls: list[tuple[str, str]] = []

    def fake_run_assertion_group(group_name: str, repo: Any) -> None:
        calls.append(("assert", group_name))

    def fake_run(command: tuple[str, ...], cwd: Path) -> None:
        calls.append(("command", " ".join(command)))
        if command == ("make", "init"):
            (cwd / "uv.lock").write_text("", encoding="utf-8")

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(render_validate, "_run_assertion_group", fake_run_assertion_group)
    monkeypatch.setattr(render_validate, "_run", fake_run)
    try:
        render_validate._run_validation_mode(mode=mode, repo=repo)
    finally:
        monkeypatch.undo()

    assert calls == [
        ("assert", "render"),
        ("command", "make init"),
        ("assert", "init"),
    ]


def test_run_validation_mode_full_e2e_uses_poe_commands(tmp_path: Path) -> None:
    repo = _make_rendered_repo(tmp_path)
    mode = render_validate.VALIDATION_MODES["full-e2e"]
    calls: list[tuple[str, str]] = []

    def fake_run_assertion_group(group_name: str, repo: Any) -> None:
        calls.append(("assert", group_name))

    def fake_run(command: tuple[str, ...], cwd: Path) -> None:
        calls.append(("command", " ".join(command)))
        if command == ("make", "init"):
            (cwd / "uv.lock").write_text("", encoding="utf-8")

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(render_validate, "_run_assertion_group", fake_run_assertion_group)
    monkeypatch.setattr(render_validate, "_run", fake_run)
    try:
        render_validate._run_validation_mode(mode=mode, repo=repo)
    finally:
        monkeypatch.undo()

    assert calls == [
        ("assert", "render"),
        ("command", "make init"),
        ("assert", "init"),
        ("command", "uv run poe verify"),
        ("command", "uv run poe run"),
        ("command", "uv run poe secret-scan"),
        ("command", "uv run poe build"),
    ]


def test_resolve_template_render_source_local_uses_snapshot(tmp_path: Path) -> None:
    source_root = tmp_path / "_template_source"
    source_root.mkdir()

    def fake_create_source_snapshot(*, repo_root: Path, base_dir: Path) -> Path:
        assert repo_root == render_validate.REPO_ROOT
        assert base_dir == tmp_path
        return source_root

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(render_validate, "_create_source_snapshot", fake_create_source_snapshot)
    try:
        source = render_validate._resolve_template_render_source(
            "local",
            base_dir=tmp_path,
            published_template_source="gh:example/template",
        )
    finally:
        monkeypatch.undo()

    assert source == render_validate.TemplateRenderSource(
        name="local",
        command_prefix=("uv", "run", "copier", "copy"),
        template_src=str(source_root),
        cwd=source_root,
    )


def test_resolve_template_render_source_published_uses_github_source(tmp_path: Path) -> None:
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.delenv("PYTHON_REPO_TEMPLATE_PUBLISHED_REF", raising=False)
    try:
        source = render_validate._resolve_template_render_source(
            "published",
            base_dir=tmp_path,
            published_template_source="gh:example/template",
        )
    finally:
        monkeypatch.undo()

    assert source == render_validate.TemplateRenderSource(
        name="published",
        command_prefix=("uvx", "copier", "copy"),
        template_src="gh:example/template",
        cwd=render_validate.REPO_ROOT,
    )


def test_resolve_template_render_source_published_uses_env_ref(tmp_path: Path) -> None:
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("PYTHON_REPO_TEMPLATE_PUBLISHED_REF", "v9.9.9")
    try:
        source = render_validate._resolve_template_render_source(
            "published",
            base_dir=tmp_path,
            published_template_source="gh:example/template",
        )
    finally:
        monkeypatch.undo()

    assert source == render_validate.TemplateRenderSource(
        name="published",
        command_prefix=("uvx", "copier", "copy"),
        template_src="gh:example/template",
        cwd=render_validate.REPO_ROOT,
        vcs_ref="v9.9.9",
    )


def test_render_uses_vcs_ref_when_present(tmp_path: Path) -> None:
    calls: list[tuple[tuple[str, ...], Path]] = []
    source = render_validate.TemplateRenderSource(
        name="published",
        command_prefix=("uvx", "copier", "copy"),
        template_src="gh:example/template",
        cwd=render_validate.REPO_ROOT,
        vcs_ref="v1.2.3",
    )
    scenario = render_validate.Scenario(repo_slug="sample-app", repo_name="Sample App")
    dest = tmp_path / "sample-app"

    def fake_run(command: tuple[str, ...], cwd: Path) -> None:
        calls.append((command, cwd))

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(render_validate, "_run", fake_run)
    try:
        render_validate._render(source=source, dest=dest, scenario=scenario)
    finally:
        monkeypatch.undo()

    assert calls == [
        (
            (
                "uvx",
                "copier",
                "copy",
                "--trust",
                "--vcs-ref",
                "v1.2.3",
                "gh:example/template",
                str(dest),
                "--data",
                "repo_slug=sample-app",
                "--data",
                "repo_name=Sample App",
                "--defaults",
            ),
            render_validate.REPO_ROOT,
        )
    ]
