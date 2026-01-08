"""Tab data source protocol used by the generic tab controller.

 Defines the `TabDataSource` protocol along with shared dataclasses used for
 remove-unused operations across different tabs (VarSets and Aliases).
 """

from dataclasses import dataclass
from typing import Protocol

from .expression_item import ExpressionItem
from .parent_child_ref import ParentChildRef


@dataclass(frozen=True)
class RemoveUnusedResult:
    removed: list[str]
    still_used: list[str]
    failed: list[str]


@dataclass(frozen=True)
class PostRemoveUpdate:
    child_items: list[ParentChildRef]
    clear_expressions: bool


@dataclass(frozen=True)
class RemoveUnusedAndUpdateResult:
    remove_result: RemoveUnusedResult
    update: PostRemoveUpdate


class TabDataSource(Protocol):
    def get_sorted_parents(self, *, exclude_copy_on_change: bool = False) -> list[str]:
        raise NotImplementedError

    def get_child_refs(self, selected_parents: list[str]) -> list[ParentChildRef]:
        raise NotImplementedError

    def get_expression_items(
        self, selected_children: list[ParentChildRef] | list[str]
    ) -> tuple[list[ExpressionItem], dict[str, int]]:
        raise NotImplementedError

    def get_expression_reference_counts(
        self, selected_children: list[ParentChildRef] | list[str]
    ) -> dict[str, int]:
        raise NotImplementedError

    def remove_unused_children(
        self, selected_children: list[ParentChildRef] | list[str]
    ) -> RemoveUnusedResult:
        raise NotImplementedError
