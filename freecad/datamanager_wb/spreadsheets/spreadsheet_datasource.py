# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileNotice: Part of the DataManager addon.

"""Spreadsheet-backed `TabDataSource` for the Aliases tab.

Adapts spreadsheet alias queries/mutations to the generic `TabController`.
"""

from ..domain.expression_item import ExpressionItem
from ..domain.parent_child_ref import ParentChildRef, parse_parent_child_ref
from ..domain.tab_datasource import RemoveUnusedResult, TabDataSource
from ..ports.freecad_context import FreeCadContext
from .spreadsheet_mutations import removeSpreadsheetAlias
from .spreadsheet_query import (
    getSpreadsheetAliasNames,
    getSpreadsheetAliasReferences,
    getSpreadsheets,
)


def _normalize_rhs(rhs: object) -> str:
    normalized_rhs = str(rhs).strip()
    if normalized_rhs.startswith("="):
        normalized_rhs = normalized_rhs[1:].lstrip()
    return normalized_rhs


def _is_alias_definition(*, object_name: str, parent: str, alias: str, rhs_text: str) -> bool:
    if object_name != parent:
        return False
    if not rhs_text.startswith("'"):
        return False
    return rhs_text.lstrip("'") == alias


def _to_expression_item(
    *,
    parent: str,
    alias: str,
    lhs: str,
    rhs: object,
) -> ExpressionItem:
    object_name = lhs.split(".", 1)[0].strip()
    normalized_rhs = _normalize_rhs(rhs)
    if _is_alias_definition(
        object_name=object_name, parent=parent, alias=alias, rhs_text=normalized_rhs
    ):
        return ExpressionItem(object_name=object_name, lhs=lhs, rhs=normalized_rhs, operator=":=")
    return ExpressionItem(object_name=object_name, lhs=lhs, rhs=normalized_rhs, operator="=")


class SpreadsheetDataSource(TabDataSource):
    """Adapter that exposes spreadsheet aliases through the `TabDataSource` protocol."""

    def __init__(self, *, ctx: FreeCadContext | None = None) -> None:
        self._ctx = ctx

    def get_sorted_parents(self, *, exclude_copy_on_change: bool = False) -> list[str]:
        """Return sorted spreadsheet names."""
        return sorted(getSpreadsheets(exclude_copy_on_change=exclude_copy_on_change, ctx=self._ctx))

    def get_child_refs(self, selected_parents: list[str]) -> list[ParentChildRef]:
        """Return alias refs for the selected spreadsheets."""
        items: list[ParentChildRef] = []
        for sheet_name in selected_parents:
            for alias_name in getSpreadsheetAliasNames(sheet_name, ctx=self._ctx):
                items.append(ParentChildRef(parent=sheet_name, child=alias_name))
        items.sort(key=lambda ref: ref.text)
        return items

    def get_expression_items(
        self, selected_children: list[ParentChildRef] | list[str]
    ) -> tuple[list[ExpressionItem], dict[str, int]]:
        """Return expression items referencing the selected aliases."""
        counts: dict[str, int] = {}
        expression_items: list[ExpressionItem] = []
        for ref in _normalize_alias_refs(selected_children):
            refs = getSpreadsheetAliasReferences(ref.parent, ref.child, ctx=self._ctx)
            counts[ref.text] = len(refs)
            for lhs, rhs in refs.items():
                expression_items.append(
                    _to_expression_item(parent=ref.parent, alias=ref.child, lhs=lhs, rhs=rhs)
                )

        expression_items.sort(key=lambda item: item.display_text)
        return expression_items, counts

    def get_expression_reference_counts(
        self, selected_children: list[ParentChildRef] | list[str]
    ) -> dict[str, int]:
        """Return expression reference counts for the selected aliases."""
        counts: dict[str, int] = {}
        for ref in _normalize_alias_refs(selected_children):
            refs = getSpreadsheetAliasReferences(ref.parent, ref.child, ctx=self._ctx)
            counts[ref.text] = len(refs)
        return counts

    def remove_unused_children(
        self, selected_children: list[ParentChildRef] | list[str]
    ) -> RemoveUnusedResult:
        """Remove selected aliases that have no expression references."""
        removed: list[str] = []
        still_used: list[str] = []
        failed: list[str] = []

        for ref in _normalize_alias_refs(selected_children):
            refs = getSpreadsheetAliasReferences(ref.parent, ref.child, ctx=self._ctx)
            if refs:
                still_used.append(ref.text)
                continue

            ok = removeSpreadsheetAlias(ref.parent, ref.child, ctx=self._ctx)
            if ok:
                removed.append(ref.text)
            else:
                failed.append(ref.text)

        return RemoveUnusedResult(removed=removed, still_used=still_used, failed=failed)


def _normalize_alias_refs(items: list[ParentChildRef] | list[str]) -> list[ParentChildRef]:
    normalized: list[ParentChildRef] = []
    for item in items:
        if isinstance(item, ParentChildRef):
            normalized.append(item)
        else:
            parsed = parse_parent_child_ref(item)
            if parsed is not None:
                normalized.append(parsed)
    return normalized
