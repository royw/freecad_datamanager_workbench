"""Spreadsheet-backed `TabDataSource` for the Aliases tab.

 Adapts spreadsheet alias queries/mutations to the generic `TabController`.
 """

from .expression_item import ExpressionItem
from .parent_child_ref import ParentChildRef
from .spreadsheet_mutations import removeSpreadsheetAlias
from .spreadsheet_query import (
    getSpreadsheetAliasNames,
    getSpreadsheetAliasReferences,
    getSpreadsheets,
)
from .tab_datasource import RemoveUnusedResult, TabDataSource


class SpreadsheetDataSource(TabDataSource):
    """Adapter that exposes spreadsheet aliases through the `TabDataSource` protocol."""

    def get_sorted_parents(self, *, exclude_copy_on_change: bool = False) -> list[str]:
        """Return sorted spreadsheet names."""
        return sorted(getSpreadsheets(exclude_copy_on_change=exclude_copy_on_change))

    def get_child_refs(self, selected_parents: list[str]) -> list[ParentChildRef]:
        """Return alias refs for the selected spreadsheets."""
        items: list[ParentChildRef] = []
        for sheet_name in selected_parents:
            for alias_name in getSpreadsheetAliasNames(sheet_name):
                items.append(ParentChildRef(parent=sheet_name, child=alias_name))
        items.sort(key=lambda ref: ref.text)
        return items

    def get_expression_items(
        self, selected_children: list[ParentChildRef] | list[str]
    ) -> tuple[list[ExpressionItem], dict[str, int]]:
        """Return expression items referencing the selected aliases."""
        expression_items: list[ExpressionItem] = []
        counts: dict[str, int] = {}

        for ref in _normalize_alias_refs(selected_children):
            refs = getSpreadsheetAliasReferences(ref.parent, ref.child)
            counts[ref.text] = len(refs)
            for lhs, rhs in refs.items():
                object_name = lhs.split(".", 1)[0].strip()
                expression_items.append(ExpressionItem(object_name=object_name, lhs=lhs, rhs=rhs))

        expression_items.sort(key=lambda item: item.display_text)
        return expression_items, counts

    def get_expression_reference_counts(
        self, selected_children: list[ParentChildRef] | list[str]
    ) -> dict[str, int]:
        """Return expression reference counts for the selected aliases."""
        counts: dict[str, int] = {}
        for ref in _normalize_alias_refs(selected_children):
            refs = getSpreadsheetAliasReferences(ref.parent, ref.child)
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
            refs = getSpreadsheetAliasReferences(ref.parent, ref.child)
            if refs:
                still_used.append(ref.text)
                continue

            ok = removeSpreadsheetAlias(ref.parent, ref.child)
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
            if "." not in item:
                continue
            parent, child = item.split(".", 1)
            if parent and child:
                normalized.append(ParentChildRef(parent=parent, child=child))
    return normalized
