from __future__ import annotations

from template.cli import main


def test_cli_smoke(capsys) -> None:
    code = main([])
    assert code == 0
    out = capsys.readouterr().out
    assert "template" in out


def test_cli_version(capsys) -> None:
    code = main(["--version"])
    assert code == 0
    out = capsys.readouterr().out.strip()
    assert out


def test_rich_optional_import() -> None:
    try:
        import rich  # noqa: F401
    except ModuleNotFoundError:
        # Rich is intentionally optional until added via `make add-rich`.
        pass
