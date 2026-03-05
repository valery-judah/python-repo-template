from __future__ import annotations

import re

_INVALID_CHARS_RE = re.compile(r"[^a-z0-9_]")


def to_package_name(value: str) -> str:
    package_name = value.lower().replace("-", "_")
    package_name = _INVALID_CHARS_RE.sub("", package_name)
    if not package_name:
        return "_"
    if not (package_name[0].isalpha() or package_name[0] == "_"):
        package_name = f"_{package_name}"
    return package_name
