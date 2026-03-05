from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from scripts.secret_scan import PATTERNS, _scan_text

VALID_GEMINI_KEY = "AIza" + "A" * 35


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )


def _run_secret_scan(repo: Path, scope: str) -> subprocess.CompletedProcess[str]:
    script_path = Path(__file__).parent.parent / "scripts" / "secret_scan.py"
    return subprocess.run(
        [sys.executable, str(script_path), "--scope", scope],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )


def _init_repo(repo: Path) -> None:
    _git(repo, "init")
    _git(repo, "config", "user.name", "Tests")
    _git(repo, "config", "user.email", "tests@example.com")


def _commit_all(repo: Path, message: str) -> None:
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", message)


def test_gemini_pattern_matches_expected_shape() -> None:
    findings = _scan_text("example.txt", f"token={VALID_GEMINI_KEY}")

    assert len(findings) == 1
    assert findings[0].pattern_name == "gemini_api_key"
    assert PATTERNS[0].regex.fullmatch(VALID_GEMINI_KEY) is not None


def test_gemini_pattern_rejects_bare_prefix() -> None:
    findings = _scan_text("example.txt", "AIza")

    assert findings == []


def test_gemini_pattern_rejects_short_example() -> None:
    findings = _scan_text("example.txt", "AIzaSHORTEXAMPLE")

    assert findings == []


def test_gemini_pattern_rejects_invalid_characters() -> None:
    invalid = "AIza" + "A" * 34 + "!"

    findings = _scan_text("example.txt", invalid)

    assert findings == []


def test_gemini_pattern_requires_boundaries() -> None:
    wrapped = f"x{VALID_GEMINI_KEY}y"

    findings = _scan_text("example.txt", wrapped)

    assert findings == []


def test_staged_scan_flags_added_key(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)

    (repo / "safe.py").write_text("print('safe')\n", encoding="utf-8")
    _commit_all(repo, "baseline")

    (repo / "safe.py").write_text(f"print('{VALID_GEMINI_KEY}')\n", encoding="utf-8")
    _git(repo, "add", "safe.py")

    result = _run_secret_scan(repo, "staged-added")

    assert result.returncode == 1
    assert "safe.py:1" in result.stderr
    assert "[REDACTED]" in result.stderr


def test_staged_scan_ignores_removed_key(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)

    (repo / "safe.py").write_text(f"print('{VALID_GEMINI_KEY}')\n", encoding="utf-8")
    _commit_all(repo, "baseline")

    (repo / "safe.py").write_text("print('safe')\n", encoding="utf-8")
    _git(repo, "add", "safe.py")

    result = _run_secret_scan(repo, "staged-added")

    assert result.returncode == 0


def test_staged_scan_ignores_unchanged_old_key(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)

    (repo / "safe.py").write_text(
        "\n".join(
            [
                f"SECRET = '{VALID_GEMINI_KEY}'",
                "VALUE = 'old'",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _commit_all(repo, "baseline")

    (repo / "safe.py").write_text(
        "\n".join(
            [
                f"SECRET = '{VALID_GEMINI_KEY}'",
                "VALUE = 'new'",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _git(repo, "add", "safe.py")

    result = _run_secret_scan(repo, "staged-added")

    assert result.returncode == 0


def test_repo_scan_flags_committed_key(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)

    (repo / "safe.py").write_text(f"print('{VALID_GEMINI_KEY}')\n", encoding="utf-8")
    _commit_all(repo, "baseline")

    result = _run_secret_scan(repo, "repo")

    assert result.returncode == 1
    assert "safe.py:1" in result.stderr


def test_repo_scan_skips_binary_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)

    (repo / "blob.bin").write_bytes(b"\0AIza" + b"A" * 35)
    _commit_all(repo, "baseline")

    result = _run_secret_scan(repo, "repo")

    assert result.returncode == 0
