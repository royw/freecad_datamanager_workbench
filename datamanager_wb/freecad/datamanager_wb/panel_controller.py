from .document_model import get_expression_items, get_sorted_varsets, get_varset_variable_items
from .gui_selection import select_object_from_expression_item


class PanelController:
    def get_sorted_varsets(self) -> list[str]:
        return get_sorted_varsets()

    def get_varset_variable_items(self, selected_varsets: list[str]) -> list[str]:
        return get_varset_variable_items(selected_varsets)

    def get_expression_items(self, selected_vars: list[str]) -> tuple[list[str], dict[str, int]]:
        return get_expression_items(selected_vars)

    def select_expression_item(self, expression_item_text: str) -> None:
        select_object_from_expression_item(expression_item_text)
