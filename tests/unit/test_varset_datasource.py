"""Unit tests for VarsetDataSource.

These tests mock the FreeCAD-facing query functions so they can run without FreeCAD.
"""

from __future__ import annotations

from freecad.datamanager_wb.parent_child_ref import ParentChildRef
from freecad.datamanager_wb.varset_datasource import VarsetDataSource


def test_get_child_refs_for_virtual_varset_filters_by_group(monkeypatch) -> None:
    ds = VarsetDataSource()

    def fake_groups(varset_name: str):
        assert varset_name == "VS"
        return {"a": "Base", "b": "Group1"}

    monkeypatch.setattr("freecad.datamanager_wb.varset_datasource.getVarsetVariableGroups", fake_groups)
    monkeypatch.setattr(
        "freecad.datamanager_wb.varset_datasource.getVarsetVariableNamesForGroup",
        lambda varset_name, group: ["x"] if group == "Group1" else ["base_only"],
    )
    monkeypatch.setattr(
        "freecad.datamanager_wb.varset_datasource.getVarsetVariableNames",
        lambda varset_name: ["x", "y"],
    )

    refs = ds.get_child_refs(["VS.Group1"])
    assert refs == [ParentChildRef(parent="VS", child="x")]


def test_get_child_refs_for_non_virtual_parent_includes_all(monkeypatch) -> None:
    ds = VarsetDataSource()

    monkeypatch.setattr(
        "freecad.datamanager_wb.varset_datasource.getVarsetVariableGroups",
        lambda varset_name: {"a": "Base"},
    )
    monkeypatch.setattr(
        "freecad.datamanager_wb.varset_datasource.getVarsetVariableNames",
        lambda varset_name: ["b", "a"],
    )

    refs = ds.get_child_refs(["VS"])
    assert refs == [ParentChildRef(parent="VS", child="a"), ParentChildRef(parent="VS", child="b")]


def test_virtual_parent_with_unknown_group_falls_back_to_normal(monkeypatch) -> None:
    ds = VarsetDataSource()

    monkeypatch.setattr(
        "freecad.datamanager_wb.varset_datasource.getVarsetVariableGroups",
        lambda varset_name: {"a": "Base", "b": "Group1"},
    )
    monkeypatch.setattr(
        "freecad.datamanager_wb.varset_datasource.getVarsetVariableNames",
        lambda varset_name: ["x"],
    )

    refs = ds.get_child_refs(["VS.Unknown"])
    assert refs == [ParentChildRef(parent="VS", child="Unknown.x")]
