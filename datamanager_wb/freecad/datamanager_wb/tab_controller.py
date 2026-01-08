"""Generic tab controller shared by VarSets and Aliases.

 Implements filtering, only-unused logic, enable-state rules, and remove-unused
 orchestration against a `TabDataSource`.
 """

import fnmatch

from .parent_child_ref import ParentChildRef
from .tab_datasource import (
    PostRemoveUpdate,
    RemoveUnusedAndUpdateResult,
    RemoveUnusedResult,
    TabDataSource,
)


class TabController:
    def __init__(self, data_source: TabDataSource) -> None:
        self._data_source = data_source

    def should_enable_remove_unused(self, *, only_unused: bool, selected_count: int) -> bool:
        return only_unused and selected_count > 0

    def can_remove_unused(
        self,
        *,
        only_unused: bool,
        selected_items: list[ParentChildRef] | list[str],
    ) -> bool:
        normalized = self._normalize_items(selected_items)
        return self.should_enable_remove_unused(
            only_unused=only_unused, selected_count=len(normalized)
        )

    def _normalize_items(self, items: list[ParentChildRef] | list[str]) -> list[str]:
        normalized: list[str] = []
        for item in items:
            if isinstance(item, ParentChildRef):
                normalized.append(item.text)
            else:
                normalized.append(item)
        return normalized

    def _normalize_glob_pattern(self, text: str) -> str | None:
        stripped = text.strip()
        if not stripped:
            return None

        if not any(ch in stripped for ch in "*?[]"):
            return f"*{stripped}*"

        return stripped

    def get_filtered_parents(
        self,
        *,
        filter_text: str,
        exclude_copy_on_change: bool = False,
    ) -> list[str]:
        pattern = self._normalize_glob_pattern(filter_text)
        parents = self._data_source.get_sorted_parents(
            exclude_copy_on_change=exclude_copy_on_change
        )
        if pattern is None:
            return parents
        return [p for p in parents if fnmatch.fnmatchcase(p, pattern)]

    def get_filtered_child_items(
        self,
        *,
        selected_parents: list[str],
        child_filter_text: str,
        only_unused: bool,
    ) -> list[ParentChildRef]:
        pattern = self._normalize_glob_pattern(child_filter_text)
        refs = self._data_source.get_child_refs(selected_parents)

        counts: dict[str, int] = {}
        if only_unused:
            counts = self._data_source.get_expression_reference_counts([ref.text for ref in refs])

        filtered: list[ParentChildRef] = []
        for ref in refs:
            if pattern is not None and not fnmatch.fnmatchcase(ref.child, pattern):
                continue
            if only_unused and counts.get(ref.text, 0) != 0:
                continue
            filtered.append(ref)
        return filtered

    def get_post_remove_unused_update(
        self,
        *,
        selected_parents: list[str],
        child_filter_text: str,
        only_unused: bool,
    ) -> PostRemoveUpdate:
        return PostRemoveUpdate(
            child_items=self.get_filtered_child_items(
                selected_parents=selected_parents,
                child_filter_text=child_filter_text,
                only_unused=only_unused,
            ),
            clear_expressions=True,
        )

    def remove_unused_and_get_update(
        self,
        *,
        selected_child_items: list[ParentChildRef] | list[str],
        selected_parents: list[str],
        child_filter_text: str,
        only_unused: bool,
    ) -> RemoveUnusedAndUpdateResult:
        remove_result = self._data_source.remove_unused_children(selected_child_items)
        update = self.get_post_remove_unused_update(
            selected_parents=selected_parents,
            child_filter_text=child_filter_text,
            only_unused=only_unused,
        )
        return RemoveUnusedAndUpdateResult(remove_result=remove_result, update=update)

    def get_expression_items(self, selected_child_items: list[ParentChildRef] | list[str]):
        return self._data_source.get_expression_items(selected_child_items)

    def get_expression_reference_counts(
        self, selected_child_items: list[ParentChildRef] | list[str]
    ):
        return self._data_source.get_expression_reference_counts(selected_child_items)

    def remove_unused_children(
        self, selected_child_items: list[ParentChildRef] | list[str]
    ) -> RemoveUnusedResult:
        return self._data_source.remove_unused_children(selected_child_items)
