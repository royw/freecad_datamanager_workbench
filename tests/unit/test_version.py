"""Unit tests for version parsing.

These tests avoid reading the real pyproject.toml by monkeypatching helpers.
"""

from __future__ import annotations

from typing import Any

import freecad.datamanager_wb.version as version


def test_get_project_version_valid() -> None:
    pyproject: dict[str, Any] = {"project": {"version": "1.2.3"}}
    assert version._get_project_version(pyproject) == "1.2.3"


def test_get_project_version_invalid_shapes() -> None:
    assert version._get_project_version({}) is None
    assert version._get_project_version({"project": []}) is None
    assert version._get_project_version({"project": {"version": 123}}) is None
    assert version._get_project_version({"project": {"version": ""}}) is None


def test_get_version_falls_back_when_read_fails(monkeypatch) -> None:
    monkeypatch.setattr(version, "_read_version_from_pyproject", lambda: None)
    assert version.get_version() == "0.0.0"


def test_get_version_returns_value_when_available(monkeypatch) -> None:
    monkeypatch.setattr(version, "_read_version_from_pyproject", lambda: "9.9.9")
    assert version.get_version() == "9.9.9"
