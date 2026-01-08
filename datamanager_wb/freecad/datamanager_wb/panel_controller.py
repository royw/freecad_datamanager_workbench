import fnmatch
from dataclasses import dataclass

import FreeCAD as App
import FreeCADGui as Gui

from .document_model import (
    get_expression_items,
    get_expression_reference_counts,
    remove_unused_varset_variables,
    get_sorted_varsets,
    get_varset_variable_items,
    get_varset_variable_refs,
)
from .expression_item import ExpressionItem
from .gui_selection import select_object_from_expression_item
from .parent_child_ref import ParentChildRef


@dataclass(frozen=True)
class RemoveUnusedResult:
    removed: list[str]
    still_used: list[str]
    failed: list[str]


@dataclass(frozen=True)
class PostRemoveUpdate:
    variable_items: list[ParentChildRef]
    clear_expressions: bool


@dataclass(frozen=True)
class RemoveUnusedAndUpdateResult:
    remove_result: RemoveUnusedResult
    update: PostRemoveUpdate


class PanelController:
    def _normalize_varset_variable_items(
        self,
        items: list[ParentChildRef] | list[str],
    ) -> list[str]:
        normalized: list[str] = []
        for item in items:
            if isinstance(item, ParentChildRef):
                normalized.append(item.text)
            else:
                normalized.append(item)
        return normalized
    def refresh_document(self) -> None:
        doc = App.ActiveDocument
        if doc is not None:
            try:
                doc.recompute()
            except Exception:  # pylint: disable=broad-exception-caught
                pass
        try:
            Gui.updateGui()
        except Exception:  # pylint: disable=broad-exception-caught
            pass

    def should_enable_remove_unused(self, *, only_unused: bool, selected_count: int) -> bool:
        return only_unused and selected_count > 0

    def can_remove_unused(
        self,
        *,
        only_unused: bool,
        selected_items: list[ParentChildRef] | list[str],
    ) -> bool:
        normalized = self._normalize_varset_variable_items(selected_items)
        return self.should_enable_remove_unused(
            only_unused=only_unused,
            selected_count=len(normalized),
        )

    def _normalize_glob_pattern(self, text: str) -> str | None:
        stripped = text.strip()
        if not stripped:
            return None

        if not any(ch in stripped for ch in "*?[]"):
            return f"*{stripped}*"

        return stripped

    def get_sorted_varsets(self, *, exclude_copy_on_change: bool = False) -> list[str]:
        return get_sorted_varsets(exclude_copy_on_change=exclude_copy_on_change)

    def get_filtered_varsets(
        self,
        *,
        filter_text: str,
        exclude_copy_on_change: bool = False,
    ) -> list[str]:
        pattern = self._normalize_glob_pattern(filter_text)
        varsets = self.get_sorted_varsets(exclude_copy_on_change=exclude_copy_on_change)
        if pattern is None:
            return varsets
        return [v for v in varsets if fnmatch.fnmatchcase(v, pattern)]

    def get_varset_variable_items(self, selected_varsets: list[str]) -> list[str]:
        return get_varset_variable_items(selected_varsets)

    def get_varset_variable_refs(self, selected_varsets: list[str]) -> list[ParentChildRef]:
        return get_varset_variable_refs(selected_varsets)

    def get_filtered_varset_variable_items(
        self,
        *,
        selected_varsets: list[str],
        variable_filter_text: str,
        only_unused: bool,
    ) -> list[ParentChildRef]:
        pattern = self._normalize_glob_pattern(variable_filter_text)
        refs = self.get_varset_variable_refs(selected_varsets)

        item_texts = [ref.text for ref in refs]

        counts: dict[str, int] = {}
        if only_unused:
            counts = self.get_expression_reference_counts(item_texts)

        filtered: list[ParentChildRef] = []
        for ref in refs:
            var_name = ref.child
            if pattern is not None and not fnmatch.fnmatchcase(var_name, pattern):
                continue
            if only_unused and counts.get(ref.text, 0) != 0:
                continue
            filtered.append(ref)

        return filtered

    def get_post_remove_unused_update(
        self,
        *,
        selected_varsets: list[str],
        variable_filter_text: str,
        only_unused: bool,
    ) -> PostRemoveUpdate:
        return PostRemoveUpdate(
            variable_items=self.get_filtered_varset_variable_items(
                selected_varsets=selected_varsets,
                variable_filter_text=variable_filter_text,
                only_unused=only_unused,
            ),
            clear_expressions=True,
        )

    def remove_unused_and_get_update(
        self,
        *,
        selected_varset_variable_items: list[ParentChildRef] | list[str],
        selected_varsets: list[str],
        variable_filter_text: str,
        only_unused: bool,
    ) -> RemoveUnusedAndUpdateResult:
        remove_result = self.remove_unused_varset_variables(selected_varset_variable_items)
        update = self.get_post_remove_unused_update(
            selected_varsets=selected_varsets,
            variable_filter_text=variable_filter_text,
            only_unused=only_unused,
        )
        return RemoveUnusedAndUpdateResult(remove_result=remove_result, update=update)

    def get_expression_items(
        self, selected_vars: list[ParentChildRef] | list[str]
    ) -> tuple[list[ExpressionItem], dict[str, int]]:
        return get_expression_items(selected_vars)

    def get_expression_reference_counts(
        self, selected_vars: list[ParentChildRef] | list[str]
    ) -> dict[str, int]:
        return get_expression_reference_counts(selected_vars)

    def remove_unused_varset_variables(
        self, selected_varset_variable_items: list[ParentChildRef] | list[str]
    ) -> RemoveUnusedResult:
        normalized = self._normalize_varset_variable_items(selected_varset_variable_items)
        removed, still_used, failed = remove_unused_varset_variables(normalized)
        self.refresh_document()
        return RemoveUnusedResult(removed=removed, still_used=still_used, failed=failed)

    def select_expression_item(self, expression_item: ExpressionItem | str) -> None:
        select_object_from_expression_item(expression_item)
