"""Package version for `freecad.datamanager_wb`."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any


def _read_pyproject_toml() -> dict[str, Any] | None:
    pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
    try:
        return tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return None


def _get_project_version(pyproject: dict[str, Any]) -> str | None:
    project = pyproject.get("project")
    if not isinstance(project, dict):
        return None
    version = project.get("version")
    if not isinstance(version, str) or not version:
        return None
    return version


def _read_version_from_pyproject() -> str | None:
    pyproject = _read_pyproject_toml()
    if pyproject is None:
        return None
    return _get_project_version(pyproject)


def get_version() -> str:
    """Get the package version."""
    version = _read_version_from_pyproject()
    if version is not None:
        return version
    return "0.0.0"


__version__ = get_version()
