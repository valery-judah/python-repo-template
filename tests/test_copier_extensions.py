from __future__ import annotations

import importlib.util
from collections.abc import Callable
from pathlib import Path
from typing import cast

import pytest


def _load_to_package_name() -> Callable[[str], str]:
    module_path = Path(__file__).resolve().parents[1] / "copier_extensions.py"
    spec = importlib.util.spec_from_file_location("copier_extensions", module_path)
    if spec is None or spec.loader is None:
        raise AssertionError("Failed to load copier_extensions.py for testing.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return cast(Callable[[str], str], module.to_package_name)


to_package_name = _load_to_package_name()


@pytest.mark.parametrize(
    ("repo_slug", "expected"),
    [
        ("sample-app", "sample_app"),
        ("already_ok", "already_ok"),
        ("99-fast-api", "_99_fast_api"),
        ("Mixed.Case!", "mixedcase"),
        ("---", "___"),
    ],
)
def test_to_package_name(repo_slug: str, expected: str) -> None:
    assert to_package_name(repo_slug) == expected
