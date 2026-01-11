"""Package version for `freecad.datamanager_wb`."""

from __future__ import annotations

import tomllib
from pathlib import Path


def _read_version_from_pyproject() -> str | None:
    pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
    try:
        data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    except OSError:
        return None
    except tomllib.TOMLDecodeError:
        return None

    project = data.get("project")
    if not isinstance(project, dict):
        return None
    version = project.get("version")
    if not isinstance(version, str) or not version:
        return None
    return version


def get_version() -> str:
    """Get the package version."""
    version = _read_version_from_pyproject()
    if version is not None:
        return version
    return "0.0.0"


__version__ = get_version()
