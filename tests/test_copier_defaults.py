from __future__ import annotations

import shutil
import tomllib
from pathlib import Path

import pytest
from copier import run_copy

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("destination", "override", "slug", "package"),
    [
        ("convert-pdf", None, "convert-pdf", "convert_pdf"),
        ("nested/sample-app/", None, "sample-app", "sample_app"),
        ("99-fast-api", None, "99-fast-api", "_99_fast_api"),
        (".", None, "existing-project", "existing_project"),
        ("convert-pdf", "custom-app", "custom-app", "custom_app"),
    ],
)
def test_destination_folder_default_and_override(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    destination: str,
    override: str | None,
    slug: str,
    package: str,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    shutil.copyfile(REPO_ROOT / "copier.yml", source / "copier.yml")
    shutil.copytree(REPO_ROOT / "template", source / "template")
    working_dir = tmp_path / "existing-project"
    working_dir.mkdir()
    monkeypatch.chdir(working_dir)

    run_copy(
        str(source),
        destination,
        data={} if override is None else {"repo_slug": override},
        defaults=True,
        unsafe=True,
        quiet=True,
        skip_tasks=True,
    )

    root = working_dir / destination
    metadata = tomllib.loads((root / "pyproject.toml").read_text())
    assert metadata["project"]["name"] == slug
    assert metadata["project"]["scripts"] == {package: f"{package}.cli:main"}
    assert (root / "src" / package / "cli.py").is_file()
    assert (root / "README.md").read_text().startswith(f"# {slug}\n")
    assert f"python -m {package}.cli" in (root / "Taskfile.yml").read_text()
