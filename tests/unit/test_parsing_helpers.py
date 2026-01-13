"""Unit tests for parsing helpers and ParentChildRef utilities."""

from __future__ import annotations

from freecad.datamanager_wb.parent_child_ref import ParentChildRef, normalize_parent_child_items, parse_parent_child_ref
from freecad.datamanager_wb.parsing_helpers import parse_expression_item_object_name, parse_varset_variable_item


def test_parse_parent_child_ref_success() -> None:
    ref = parse_parent_child_ref("A.B")
    assert ref == ParentChildRef(parent="A", child="B")
    assert ref.text == "A.B"


def test_parse_parent_child_ref_rejects_missing_or_empty_parts() -> None:
    assert parse_parent_child_ref("A") is None
    assert parse_parent_child_ref(".B") is None
    assert parse_parent_child_ref("A.") is None


def test_normalize_parent_child_items_handles_mixed_types() -> None:
    items: list[ParentChildRef] | list[str] = [ParentChildRef("A", "x"), "B.y"]
    assert normalize_parent_child_items(items) == ["A.x", "B.y"]


def test_parse_varset_variable_item_delegates_to_parent_child_parser() -> None:
    assert parse_varset_variable_item("VarSet.Length") == ("VarSet", "Length")
    assert parse_varset_variable_item("NoDot") is None


def test_parse_expression_item_object_name_parses_lhs_before_equals() -> None:
    assert parse_expression_item_object_name("Obj.Length = 1") == "Obj"
    assert parse_expression_item_object_name("Obj.Length:= 1") == "Obj"
    assert parse_expression_item_object_name("NoDot = 1") is None
