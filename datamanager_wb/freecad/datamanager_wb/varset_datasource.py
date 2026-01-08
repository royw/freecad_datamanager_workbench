from .document_model import (
    get_expression_items,
    get_expression_reference_counts,
    get_sorted_varsets,
    get_varset_variable_refs,
    remove_unused_varset_variables,
)
from .expression_item import ExpressionItem
from .parent_child_ref import ParentChildRef
from .tab_datasource import RemoveUnusedResult, TabDataSource


class VarsetDataSource(TabDataSource):
    def get_sorted_parents(self, *, exclude_copy_on_change: bool = False) -> list[str]:
        return get_sorted_varsets(exclude_copy_on_change=exclude_copy_on_change)

    def get_child_refs(self, selected_parents: list[str]) -> list[ParentChildRef]:
        return get_varset_variable_refs(selected_parents)

    def get_expression_items(
        self, selected_children: list[ParentChildRef] | list[str]
    ) -> tuple[list[ExpressionItem], dict[str, int]]:
        return get_expression_items(selected_children)

    def get_expression_reference_counts(
        self, selected_children: list[ParentChildRef] | list[str]
    ) -> dict[str, int]:
        return get_expression_reference_counts(selected_children)

    def remove_unused_children(
        self, selected_children: list[ParentChildRef] | list[str]
    ) -> RemoveUnusedResult:
        removed, still_used, failed = remove_unused_varset_variables(selected_children)
        return RemoveUnusedResult(removed=removed, still_used=still_used, failed=failed)
