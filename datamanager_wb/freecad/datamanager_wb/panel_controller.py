from .document_model import (
    get_expression_items,
    get_expression_reference_counts,
    get_sorted_varsets,
    get_varset_variable_items,
)
from .expression_item import ExpressionItem
from .gui_selection import select_object_from_expression_item


class PanelController:
    def get_sorted_varsets(self, *, exclude_copy_on_change: bool = False) -> list[str]:
        return get_sorted_varsets(exclude_copy_on_change=exclude_copy_on_change)

    def get_varset_variable_items(self, selected_varsets: list[str]) -> list[str]:
        return get_varset_variable_items(selected_varsets)

    def get_expression_items(
        self, selected_vars: list[str]
    ) -> tuple[list[ExpressionItem], dict[str, int]]:
        return get_expression_items(selected_vars)

    def get_expression_reference_counts(self, selected_vars: list[str]) -> dict[str, int]:
        return get_expression_reference_counts(selected_vars)

    def select_expression_item(self, expression_item: ExpressionItem | str) -> None:
        select_object_from_expression_item(expression_item)
