"""Unit tests for VarsetDataSource.

These tests mock the FreeCAD-facing query functions so they can run without FreeCAD.
"""

from __future__ import annotations

from freecad.DataManager.domain.parent_child_ref import ParentChildRef
from freecad.DataManager.varsets.varset_datasource import VarsetDataSource


def test_get_child_refs_for_virtual_varset_filters_by_group(monkeypatch) -> None:
    """VarsetDataSource.get_child_refs filters variables by virtual varset group selection."""
    ds = VarsetDataSource()

    def fake_groups(varset_name: str, *, ctx=None):
        assert varset_name == "VS"
        return {"a": "Base", "b": "Group1"}

    monkeypatch.setattr("freecad.DataManager.varsets.varset_datasource.getVarsetVariableGroups", fake_groups)
    monkeypatch.setattr(
        "freecad.DataManager.varsets.varset_datasource.getVarsetVariableNamesForGroup",
        lambda varset_name, group, *, ctx=None: ["x"] if group == "Group1" else ["base_only"],
    )
    monkeypatch.setattr(
        "freecad.DataManager.varsets.varset_datasource.getVarsetVariableNames",
        lambda varset_name, *, ctx=None: ["x", "y"],
    )

    refs = ds.get_child_refs(["VS.Group1"])
    assert refs == [ParentChildRef(parent="VS", child="x")]


def test_get_child_refs_for_non_virtual_parent_includes_all(monkeypatch) -> None:
    """VarsetDataSource.get_child_refs returns all variables for a non-virtual varset parent."""
    ds = VarsetDataSource()

    monkeypatch.setattr(
        "freecad.DataManager.varsets.varset_datasource.getVarsetVariableGroups",
        lambda varset_name, *, ctx=None: {"a": "Base", "b": "Group1"},
    )
    monkeypatch.setattr(
        "freecad.DataManager.varsets.varset_datasource.getVarsetVariableNames",
        lambda varset_name, *, ctx=None: ["b", "a"],
    )

    refs = ds.get_child_refs(["VS"])
    assert refs == [ParentChildRef(parent="VS", child="a"), ParentChildRef(parent="VS", child="b")]


def test_virtual_parent_with_unknown_group_falls_back_to_normal(monkeypatch) -> None:
    """Unknown virtual group selection falls back to treating the selection as a normal variable prefix."""
    ds = VarsetDataSource()

    monkeypatch.setattr(
        "freecad.DataManager.varsets.varset_datasource.getVarsetVariableGroups",
        lambda varset_name, *, ctx=None: {"a": "Base", "b": "Group1"},
    )
    monkeypatch.setattr(
        "freecad.DataManager.varsets.varset_datasource.getVarsetVariableNames",
        lambda varset_name, *, ctx=None: ["x"],
    )

    refs = ds.get_child_refs(["VS.Unknown"])
    assert refs == [ParentChildRef(parent="VS", child="Unknown.x")]
