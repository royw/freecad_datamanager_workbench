"""UI-facing controller facade for the DataManager MainPanel.

 This module provides a higher-level API used by the GUI layer. It delegates
 tab-generic logic to `TabController` instances and owns document recompute and
 GUI refresh behavior.
 """

from dataclasses import dataclass

import FreeCAD as App
import FreeCADGui as Gui

from .expression_item import ExpressionItem
from .gui_selection import select_object_from_expression_item
from .parent_child_ref import ParentChildRef
from .spreadsheet_datasource import SpreadsheetDataSource
from .tab_controller import TabController
from .varset_datasource import VarsetDataSource


@dataclass(frozen=True)
class RemoveUnusedResult:
    """UI-friendly remove-unused outcome.

    This mirrors `tab_datasource.RemoveUnusedResult` but is defined here as a
    stable UI-facing type.

    Attributes:
        removed: Identifiers successfully removed.
        still_used: Identifiers skipped because they still have references.
        failed: Identifiers that could not be removed.
    """

    removed: list[str]
    still_used: list[str]
    failed: list[str]


@dataclass(frozen=True)
class PostRemoveUpdate:
    """UI update payload after remove-unused.

    Attributes:
        variable_items: Updated list of child refs to display.
        clear_expressions: Whether the expressions list should be cleared.
    """

    variable_items: list[ParentChildRef]
    clear_expressions: bool


@dataclass(frozen=True)
class RemoveUnusedAndUpdateResult:
    """Combined remove result and UI update."""

    remove_result: RemoveUnusedResult
    update: PostRemoveUpdate


class PanelController:
    """Facade used by `MainPanel` to access workbench behavior.

    Responsibilities:
    - Provide a UI-oriented API for both tabs (VarSets and Aliases).
    - Delegate tab-generic operations to two `TabController` instances.
    - Own the document refresh boundary (`doc.recompute()` + `Gui.updateGui()`).
    """

    def __init__(self) -> None:
        self._varsets_tab_controller = TabController(VarsetDataSource())
        self._aliases_tab_controller = TabController(SpreadsheetDataSource())

    def refresh_document(self) -> None:
        """Recompute the active document and refresh the FreeCAD GUI.

        Any exceptions are swallowed to keep the UI responsive.
        """
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
        """Delegate the enable/disable rule for remove-unused in the VarSets tab."""
        return self._varsets_tab_controller.should_enable_remove_unused(
            only_unused=only_unused,
            selected_count=selected_count,
        )

    def can_remove_unused(
        self,
        *,
        only_unused: bool,
        selected_items: list[ParentChildRef] | list[str],
    ) -> bool:
        """Return whether a selection is eligible for remove-unused (VarSets tab)."""
        return self._varsets_tab_controller.can_remove_unused(
            only_unused=only_unused,
            selected_items=selected_items,
        )

    def get_sorted_varsets(self, *, exclude_copy_on_change: bool = False) -> list[str]:
        """Return sorted VarSet names."""
        return self._varsets_tab_controller._data_source.get_sorted_parents(  # pylint: disable=protected-access
            exclude_copy_on_change=exclude_copy_on_change
        )

    def get_filtered_varsets(
        self,
        *,
        filter_text: str,
        exclude_copy_on_change: bool = False,
    ) -> list[str]:
        """Return VarSet names filtered by the UI filter text."""
        return self._varsets_tab_controller.get_filtered_parents(
            filter_text=filter_text,
            exclude_copy_on_change=exclude_copy_on_change,
        )

    def get_varset_variable_items(self, selected_varsets: list[str]) -> list[str]:
        """Return `VarSet.Variable` strings for the selected VarSets."""
        return [ref.text for ref in self.get_varset_variable_refs(selected_varsets)]

    def get_varset_variable_refs(self, selected_varsets: list[str]) -> list[ParentChildRef]:
        """Return structured variable refs for the selected VarSets."""
        return self._varsets_tab_controller._data_source.get_child_refs(selected_varsets)  # pylint: disable=protected-access

    def get_filtered_varset_variable_items(
        self,
        *,
        selected_varsets: list[str],
        variable_filter_text: str,
        only_unused: bool,
    ) -> list[ParentChildRef]:
        """Return filtered VarSet variable refs for the UI."""
        return self._varsets_tab_controller.get_filtered_child_items(
            selected_parents=selected_varsets,
            child_filter_text=variable_filter_text,
            only_unused=only_unused,
        )

    def get_post_remove_unused_update(
        self,
        *,
        selected_varsets: list[str],
        variable_filter_text: str,
        only_unused: bool,
    ) -> PostRemoveUpdate:
        """Compute the post-mutation UI update for the VarSets tab."""
        update = self._varsets_tab_controller.get_post_remove_unused_update(
            selected_parents=selected_varsets,
            child_filter_text=variable_filter_text,
            only_unused=only_unused,
        )
        return PostRemoveUpdate(
            variable_items=update.child_items, clear_expressions=update.clear_expressions
        )

    def remove_unused_and_get_update(
        self,
        *,
        selected_varset_variable_items: list[ParentChildRef] | list[str],
        selected_varsets: list[str],
        variable_filter_text: str,
        only_unused: bool,
    ) -> RemoveUnusedAndUpdateResult:
        """Remove unused variables and return updated UI state (VarSets tab)."""
        combined = self._varsets_tab_controller.remove_unused_and_get_update(
            selected_child_items=selected_varset_variable_items,
            selected_parents=selected_varsets,
            child_filter_text=variable_filter_text,
            only_unused=only_unused,
        )
        self.refresh_document()

        remove_result = RemoveUnusedResult(
            removed=combined.remove_result.removed,
            still_used=combined.remove_result.still_used,
            failed=combined.remove_result.failed,
        )
        update = PostRemoveUpdate(
            variable_items=combined.update.child_items,
            clear_expressions=combined.update.clear_expressions,
        )
        return RemoveUnusedAndUpdateResult(remove_result=remove_result, update=update)

    def get_expression_items(
        self, selected_vars: list[ParentChildRef] | list[str]
    ) -> tuple[list[ExpressionItem], dict[str, int]]:
        """Return expression items and counts for selected VarSet variables."""
        return self._varsets_tab_controller.get_expression_items(selected_vars)

    def get_expression_reference_counts(
        self, selected_vars: list[ParentChildRef] | list[str]
    ) -> dict[str, int]:
        """Return expression reference counts for selected VarSet variables."""
        return self._varsets_tab_controller.get_expression_reference_counts(selected_vars)

    def remove_unused_varset_variables(
        self, selected_varset_variable_items: list[ParentChildRef] | list[str]
    ) -> RemoveUnusedResult:
        """Remove unused variables (VarSets tab) and refresh the document."""
        result = self._varsets_tab_controller.remove_unused_children(selected_varset_variable_items)
        self.refresh_document()
        return RemoveUnusedResult(
            removed=result.removed,
            still_used=result.still_used,
            failed=result.failed,
        )

    def get_sorted_spreadsheets(self, *, exclude_copy_on_change: bool = False) -> list[str]:
        """Return sorted spreadsheet names."""
        return self._aliases_tab_controller._data_source.get_sorted_parents(  # pylint: disable=protected-access
            exclude_copy_on_change=exclude_copy_on_change
        )

    def get_filtered_spreadsheets(
        self,
        *,
        filter_text: str,
        exclude_copy_on_change: bool = False,
    ) -> list[str]:
        """Return spreadsheet names filtered by the UI filter text."""
        return self._aliases_tab_controller.get_filtered_parents(
            filter_text=filter_text,
            exclude_copy_on_change=exclude_copy_on_change,
        )

    def get_spreadsheet_alias_refs(self, selected_spreadsheets: list[str]) -> list[ParentChildRef]:
        """Return structured alias refs for the selected spreadsheets."""
        return self._aliases_tab_controller._data_source.get_child_refs(  # pylint: disable=protected-access
            selected_spreadsheets
        )

    def get_filtered_spreadsheet_alias_items(
        self,
        *,
        selected_spreadsheets: list[str],
        alias_filter_text: str,
        only_unused: bool,
    ) -> list[ParentChildRef]:
        """Return filtered spreadsheet alias refs for the UI."""
        return self._aliases_tab_controller.get_filtered_child_items(
            selected_parents=selected_spreadsheets,
            child_filter_text=alias_filter_text,
            only_unused=only_unused,
        )

    def get_alias_expression_items(
        self, selected_aliases: list[ParentChildRef] | list[str]
    ) -> tuple[list[ExpressionItem], dict[str, int]]:
        """Return expression items and counts for selected spreadsheet aliases."""
        return self._aliases_tab_controller.get_expression_items(selected_aliases)

    def get_alias_post_remove_unused_update(
        self,
        *,
        selected_spreadsheets: list[str],
        alias_filter_text: str,
        only_unused: bool,
    ) -> PostRemoveUpdate:
        """Compute the post-mutation UI update for the Aliases tab."""
        update = self._aliases_tab_controller.get_post_remove_unused_update(
            selected_parents=selected_spreadsheets,
            child_filter_text=alias_filter_text,
            only_unused=only_unused,
        )
        return PostRemoveUpdate(
            variable_items=update.child_items, clear_expressions=update.clear_expressions
        )

    def remove_unused_aliases_and_get_update(
        self,
        *,
        selected_alias_items: list[ParentChildRef] | list[str],
        selected_spreadsheets: list[str],
        alias_filter_text: str,
        only_unused: bool,
    ) -> RemoveUnusedAndUpdateResult:
        """Remove unused aliases and return updated UI state (Aliases tab)."""
        combined = self._aliases_tab_controller.remove_unused_and_get_update(
            selected_child_items=selected_alias_items,
            selected_parents=selected_spreadsheets,
            child_filter_text=alias_filter_text,
            only_unused=only_unused,
        )
        self.refresh_document()

        remove_result = RemoveUnusedResult(
            removed=combined.remove_result.removed,
            still_used=combined.remove_result.still_used,
            failed=combined.remove_result.failed,
        )
        update = PostRemoveUpdate(
            variable_items=combined.update.child_items,
            clear_expressions=combined.update.clear_expressions,
        )
        return RemoveUnusedAndUpdateResult(remove_result=remove_result, update=update)

    def select_expression_item(self, expression_item: ExpressionItem | str) -> None:
        """Select the FreeCAD object referenced by an expression list entry."""
        select_object_from_expression_item(expression_item)
