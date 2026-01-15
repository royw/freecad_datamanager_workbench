"""Unit tests for `SpreadsheetDataSource`."""

from __future__ import annotations

from freecad.datamanager_wb.domain.parent_child_ref import ParentChildRef
from freecad.datamanager_wb.spreadsheets.spreadsheet_datasource import SpreadsheetDataSource


def test_get_child_refs_sorts(monkeypatch) -> None:
    """SpreadsheetDataSource.get_child_refs returns sorted alias refs."""
    ds = SpreadsheetDataSource()

    monkeypatch.setattr(
        "freecad.datamanager_wb.spreadsheets.spreadsheet_datasource.getSpreadsheetAliasNames",
        lambda sheet_name, *, ctx=None: ["b", "a"],
    )

    refs = ds.get_child_refs(["Sheet"])
    assert refs == [ParentChildRef(parent="Sheet", child="a"), ParentChildRef(parent="Sheet", child="b")]


def test_get_expression_items_counts_and_operator(monkeypatch) -> None:
    """SpreadsheetDataSource.get_expression_items returns reference counts and operators."""
    ds = SpreadsheetDataSource()

    def fake_refs(sheet_name: str, alias_name: str | None = None, *, ctx=None):
        assert sheet_name == "Sheet"
        assert alias_name == "foo"
        return {
            "Sheet.A1": "'foo",
            "Box.Length": "=foo+1",
        }

    monkeypatch.setattr(
        "freecad.datamanager_wb.spreadsheets.spreadsheet_datasource.getSpreadsheetAliasReferences",
        fake_refs,
    )

    items, counts = ds.get_expression_items([ParentChildRef(parent="Sheet", child="foo")])
    assert counts == {"Sheet.foo": 2}

    by_lhs = {item.lhs: item for item in items}
    assert by_lhs["Sheet.A1"].operator == ":="
    assert by_lhs["Box.Length"].operator == "="


def test_remove_unused_children(monkeypatch) -> None:
    """SpreadsheetDataSource.remove_unused_children removes only aliases with zero references."""
    ds = SpreadsheetDataSource()

    def fake_refs(sheet_name: str, alias_name: str | None = None, *, ctx=None):
        if alias_name == "used":
            return {"Box.Length": "=used+1"}
        return {}

    monkeypatch.setattr(
        "freecad.datamanager_wb.spreadsheets.spreadsheet_datasource.getSpreadsheetAliasReferences",
        fake_refs,
    )
    monkeypatch.setattr(
        "freecad.datamanager_wb.spreadsheets.spreadsheet_datasource.removeSpreadsheetAlias",
        lambda sheet_name, alias_name, *, ctx=None: True,
    )

    result = ds.remove_unused_children(
        [ParentChildRef(parent="Sheet", child="unused"), ParentChildRef(parent="Sheet", child="used")]
    )
    assert result.removed == ["Sheet.unused"]
    assert result.still_used == ["Sheet.used"]
    assert result.failed == []
