from __future__ import annotations

import importlib.util
import sys
from argparse import Namespace
from pathlib import Path
from typing import Any

import pytest


def _load_release_module() -> Any:
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "release.py"
    spec = importlib.util.spec_from_file_location("release", module_path)
    if spec is None or spec.loader is None:
        raise AssertionError("Failed to load scripts/release.py for testing.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


release = _load_release_module()


def test_parse_version_tag_accepts_semver_tags() -> None:
    assert release.parse_version_tag("v12.34.56") == release.SemVer(12, 34, 56)


def test_parse_version_tag_rejects_non_release_tags() -> None:
    assert release.parse_version_tag("0.1.2") is None
    assert release.parse_version_tag("release-1") is None
    assert release.parse_version_tag("v1.2") is None


def test_latest_version_tag_ignores_non_matching_tags() -> None:
    latest = release.latest_version_tag(["notes", "v0.1.9", "v1.0.0", "v0.12.0"])

    assert latest == release.SemVer(1, 0, 0)


@pytest.mark.parametrize(
    ("bump", "expected"),
    [
        ("patch", "v0.1.3"),
        ("minor", "v0.2.0"),
        ("major", "v1.0.0"),
    ],
)
def test_determine_next_tag_from_latest_release(bump: str, expected: str) -> None:
    latest_tag, next_tag = release.determine_next_tag(["v0.1.2", "v0.1.1"], bump)

    assert latest_tag == "v0.1.2"
    assert next_tag == expected


def test_determine_next_tag_without_existing_releases_starts_from_zero() -> None:
    latest_tag, next_tag = release.determine_next_tag([], "patch")

    assert latest_tag is None
    assert next_tag == "v0.0.1"


def test_run_release_fetches_creates_and_pushes(capsys: pytest.CaptureFixture[str]) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_fetch_tags(remote: str) -> None:
        calls.append(("fetch", remote))

    def fake_list_tags() -> list[str]:
        calls.append(("list_tags",))
        return ["v0.1.2"]

    def fake_create_tag(tag: str) -> None:
        calls.append(("create_tag", tag))

    def fake_current_branch() -> str:
        calls.append(("current_branch",))
        return "main"

    def fake_push_release(remote: str, branch: str, tag: str) -> None:
        calls.append(("push_release", remote, branch, tag))

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(release, "fetch_tags", fake_fetch_tags)
    monkeypatch.setattr(release, "list_tags", fake_list_tags)
    monkeypatch.setattr(release, "create_tag", fake_create_tag)
    monkeypatch.setattr(release, "current_branch", fake_current_branch)
    monkeypatch.setattr(release, "push_release", fake_push_release)
    try:
        exit_code = release.run_release(
            Namespace(
                bump="patch",
                remote="origin",
                no_fetch=False,
                push=True,
                dry_run=False,
            )
        )
    finally:
        monkeypatch.undo()

    assert exit_code == 0
    assert calls == [
        ("fetch", "origin"),
        ("list_tags",),
        ("create_tag", "v0.1.3"),
        ("current_branch",),
        ("push_release", "origin", "main", "v0.1.3"),
    ]
    assert capsys.readouterr().out == (
        "Latest tag: v0.1.2\n"
        "Next tag: v0.1.3\n"
        "Created tag: v0.1.3\n"
        "Pushed branch `main` and tag `v0.1.3` to `origin`.\n"
    )


def test_run_release_dry_run_skips_mutation(capsys: pytest.CaptureFixture[str]) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_fetch_tags(remote: str) -> None:
        calls.append(("fetch", remote))

    def fake_list_tags() -> list[str]:
        calls.append(("list_tags",))
        return ["v0.1.2"]

    def fail_create_tag(tag: str) -> None:
        raise AssertionError(f"create_tag should not run during dry-run: {tag}")

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(release, "fetch_tags", fake_fetch_tags)
    monkeypatch.setattr(release, "list_tags", fake_list_tags)
    monkeypatch.setattr(release, "create_tag", fail_create_tag)
    try:
        exit_code = release.run_release(
            Namespace(
                bump="minor",
                remote="origin",
                no_fetch=False,
                push=False,
                dry_run=True,
            )
        )
    finally:
        monkeypatch.undo()

    assert exit_code == 0
    assert calls == [("fetch", "origin"), ("list_tags",)]
    assert capsys.readouterr().out == "Latest tag: v0.1.2\nNext tag: v0.2.0\n"


def test_run_release_rejects_detached_head_push() -> None:
    def fake_fetch_tags(remote: str) -> None:
        assert remote == "origin"

    def fake_list_tags() -> list[str]:
        return ["v0.1.2"]

    def fake_create_tag(tag: str) -> None:
        assert tag == "v0.1.3"

    def fake_current_branch() -> str:
        return ""

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(release, "fetch_tags", fake_fetch_tags)
    monkeypatch.setattr(release, "list_tags", fake_list_tags)
    monkeypatch.setattr(release, "create_tag", fake_create_tag)
    monkeypatch.setattr(release, "current_branch", fake_current_branch)
    try:
        with pytest.raises(release.ReleaseError, match="detached HEAD"):
            release.run_release(
                Namespace(
                    bump="patch",
                    remote="origin",
                    no_fetch=False,
                    push=True,
                    dry_run=False,
                )
            )
    finally:
        monkeypatch.undo()
