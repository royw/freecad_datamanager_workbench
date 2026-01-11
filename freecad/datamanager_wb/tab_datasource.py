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
    """Outcome of a remove-unused operation.

    Attributes:
        removed: Child identifiers that were removed successfully.
        still_used: Child identifiers that were not removed because they were
            found to still have expression references.
        failed: Child identifiers that could not be removed due to parsing,
            document errors, or other failures.
    """

    removed: list[str]
    still_used: list[str]
    failed: list[str]


@dataclass(frozen=True)
class PostRemoveUpdate:
    """UI update instructions after a remove-unused mutation.

    The generic controller computes a new list of child items (after filtering)
    and whether the expressions list should be cleared.

    Attributes:
        child_items: The filtered list of child refs that should be shown.
        clear_expressions: Whether the expressions list should be cleared.
    """

    child_items: list[ParentChildRef]
    clear_expressions: bool


@dataclass(frozen=True)
class RemoveUnusedAndUpdateResult:
    """Combined remove result and follow-up UI update."""

    remove_result: RemoveUnusedResult
    update: PostRemoveUpdate


class TabDataSource(Protocol):
    """Protocol implemented by each tab's data backend.

    The `TabController` is pure, tab-generic logic. It depends on this protocol
    to obtain parents/children, compute expression references, and perform the
    remove-unused mutation.

    Implementations should treat string child identifiers as the canonical
    `Parent.Child` form used by the UI.
    """

    def get_sorted_parents(self, *, exclude_copy_on_change: bool = False) -> list[str]:
        """Return parent names sorted for display.

        Args:
            exclude_copy_on_change: Whether to filter out parents that belong to
                copy-on-change groups (domain-specific).
        """
        raise NotImplementedError

    def get_child_refs(self, selected_parents: list[str]) -> list[ParentChildRef]:
        """Return all child refs for the given selected parents."""
        raise NotImplementedError

    def get_expression_items(
        self, selected_children: list[ParentChildRef] | list[str]
    ) -> tuple[list[ExpressionItem], dict[str, int]]:
        """Return expression items and per-child reference counts.

        Returns:
            A tuple of:
            - List of `ExpressionItem` objects suitable for populating the UI.
            - Dict mapping each selected child identifier to a reference count.
        """
        raise NotImplementedError

    def get_expression_reference_counts(
        self, selected_children: list[ParentChildRef] | list[str]
    ) -> dict[str, int]:
        """Return only the reference counts for selected children."""
        raise NotImplementedError

    def remove_unused_children(
        self, selected_children: list[ParentChildRef] | list[str]
    ) -> RemoveUnusedResult:
        """Remove the selected children if they are unused.

        Implementations must not remove items that still have expression
        references.
        """
        raise NotImplementedError
