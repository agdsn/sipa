from __future__ import annotations

from importlib.resources import files
from pathlib import Path


def get_package_path(suffix: str = "") -> str:
    fs_path = Path(__file__).resolve().parent
    if fs_path.is_dir():
        return str(fs_path / suffix)

    pkg_path = files("sipa")
    if pkg_path.is_dir():
        return str(pkg_path / suffix)

    raise AssertionError


