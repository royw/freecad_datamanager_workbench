"""Unit tests for version parsing.

These tests avoid reading the real pyproject.toml by monkeypatching helpers.
"""

from __future__ import annotations

from typing import Any

import freecad.DataManager.version as version


def test_get_project_version_valid() -> None:
    """_get_project_version returns the version string for a valid pyproject shape."""
    pyproject: dict[str, Any] = {"project": {"version": "1.2.3"}}
    assert version._get_project_version(pyproject) == "1.2.3"


def test_get_project_version_invalid_shapes() -> None:
    """_get_project_version returns None for invalid pyproject shapes."""
    assert version._get_project_version({}) is None
    assert version._get_project_version({"project": []}) is None
    assert version._get_project_version({"project": {"version": 123}}) is None
    assert version._get_project_version({"project": {"version": ""}}) is None


def test_get_version_falls_back_when_read_fails(monkeypatch) -> None:
    """get_version falls back to 0.0.0 when reading pyproject fails."""
    monkeypatch.setattr(version, "_read_version_from_pyproject", lambda: None)
    assert version.get_version() == "0.0.0"


def test_get_version_returns_value_when_available(monkeypatch) -> None:
    """get_version returns the read version when available."""
    monkeypatch.setattr(version, "_read_version_from_pyproject", lambda: "9.9.9")
    assert version.get_version() == "9.9.9"
