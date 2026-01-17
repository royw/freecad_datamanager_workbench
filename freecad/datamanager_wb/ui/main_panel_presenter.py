# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileNotice: Part of the DataManager addon.

"""Presenter for `MainPanel`.

The presenter owns UI-facing orchestration and formatting decisions while keeping
Qt widgets in `MainPanel` as a thin view layer.
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass


@dataclass(frozen=True)
class DisplayItem:
    """An item to display in a list widget."""

    key: object
    display: str


@dataclass(frozen=True)
class ParentListState:
    """Render-state for a parent list widget (VarSets or Spreadsheets)."""

    items: list[DisplayItem]
    selected_keys: set[str]


@dataclass(frozen=True)
class ChildListState:
    """Render-state for a child list widget (variables/aliases)."""

    items: list[DisplayItem]
    selected_keys: set[object]


@dataclass(frozen=True)
class ExpressionListState:
    """Render-state for an expressions list widget."""

    items: list[DisplayItem]


@dataclass(frozen=True)
class ActiveDocumentChangePlan:
    """Presenter-defined orchestration plan for an active document change."""

    clear_varsets_selection: bool
    clear_spreadsheets_selection: bool
    repopulate_varsets: bool
    repopulate_spreadsheets: bool
    clear_varset_variable_names: bool
    clear_varset_expressions: bool
    clear_alias_names: bool
    clear_alias_expressions: bool


@dataclass(frozen=True)
class ShowPlan:
    """Presenter-defined plan for showing the panel."""

    show_standalone: bool
    reuse_subwindow: bool
    create_subwindow: bool


class MainPanelPresenter:
    """Presenter for `MainPanel` interactions and formatting."""

    def __init__(self, controller: object) -> None:
        self._controller = controller

    def get_active_document_change_plan(self) -> ActiveDocumentChangePlan:
        """Return an orchestration plan for when the active document changes."""

        return ActiveDocumentChangePlan(
            clear_varsets_selection=True,
            clear_spreadsheets_selection=True,
            repopulate_varsets=True,
            repopulate_spreadsheets=True,
            clear_varset_variable_names=True,
            clear_varset_expressions=True,
            clear_alias_names=True,
            clear_alias_expressions=True,
        )

    def should_enable_remove_unused(self, *, only_unused: bool, selected_count: int) -> bool:
        """Return whether the remove-unused action should be enabled."""

        getter = getattr(self._controller, "should_enable_remove_unused", None)
        if not callable(getter):
            return False
        value: object = getter(only_unused=only_unused, selected_count=selected_count)
        return bool(value)

    def should_enable_copy_button(self, *, list_has_focus: bool, selected_count: int) -> bool:
        """Return whether a copy button for a list should be enabled."""

        return bool(list_has_focus and selected_count > 0)

    def get_show_plan(self, *, mdi_available: bool, has_existing_subwindow: bool) -> ShowPlan:
        """Return a plan for showing the panel given the available UI host."""

        if not mdi_available:
            return ShowPlan(show_standalone=True, reuse_subwindow=False, create_subwindow=False)
        if has_existing_subwindow:
            return ShowPlan(show_standalone=False, reuse_subwindow=True, create_subwindow=False)
        return ShowPlan(show_standalone=False, reuse_subwindow=False, create_subwindow=True)

    def _get_object_label(self, object_name: str) -> str | None:
        getter = getattr(self._controller, "get_object_label", None)
        if not callable(getter):
            return None
        value: object = getter(object_name)
        if isinstance(value, str) and value:
            return value
        return None

    def format_object_name(self, object_name: str, *, use_label: bool) -> str:
        """Format an object name for UI display, optionally using object labels."""
        if not use_label:
            return object_name

        if "." in object_name:
            base_name, suffix = object_name.split(".", 1)
            base_label = self._get_object_label(base_name)
            if base_label:
                return f"{base_label}.{suffix}"
            return object_name

        label = self._get_object_label(object_name)
        return label if label else object_name

    def format_parent_child_ref(self, ref: object, *, use_label: bool) -> str:
        """Format a `ParentChildRef`-like object for display.

        The presenter treats `ref` as a duck-typed object with `parent`, `child`,
        and `text` attributes.
        """

        if not use_label:
            return str(getattr(ref, "text", ""))

        parent = getattr(ref, "parent", None)
        child = getattr(ref, "child", None)
        if not isinstance(parent, str) or not isinstance(child, str):
            return str(getattr(ref, "text", ""))

        parent_label = self._get_object_label(parent)
        if not parent_label:
            return str(getattr(ref, "text", ""))
        return f"{parent_label}.{child}"

    def format_expression_item(self, expression_item: object, *, use_label: bool) -> str:
        """Format an `ExpressionItem`-like object for display."""
        display_text = str(getattr(expression_item, "display_text", ""))
        parts = self._get_expression_item_parts(expression_item)
        if parts is None:
            return display_text

        lhs, rhs, operator, obj_name = parts
        if not self._should_use_object_label(use_label, obj_name=obj_name):
            return f"{lhs} {operator} {rhs}"

        return self._format_expression_item_with_label(lhs, rhs, operator, obj_name)

    def _get_expression_item_parts(
        self, expression_item: object
    ) -> tuple[str, str, str, str | None] | None:
        lhs = getattr(expression_item, "lhs", None)
        rhs = getattr(expression_item, "rhs", None)
        operator = getattr(expression_item, "operator", "=")
        obj_name = getattr(expression_item, "object_name", None)
        if not isinstance(lhs, str) or not isinstance(rhs, str):
            return None
        return lhs, rhs, str(operator), obj_name if isinstance(obj_name, str) else None

    def _should_use_object_label(self, use_label: bool, *, obj_name: str | None) -> bool:
        return bool(use_label and obj_name)

    def _format_expression_item_with_label(
        self, lhs: str, rhs: str, operator: str, obj_name: str
    ) -> str:
        obj_label = self._get_object_label(obj_name)
        if not obj_label:
            return f"{lhs} {operator} {rhs}"
        return f"{self._replace_lhs_object_with_label(lhs, obj_label)} {operator} {rhs}"

    def _replace_lhs_object_with_label(self, lhs: str, obj_label: str) -> str:
        if "." not in lhs:
            return lhs
        _prefix, rest = lhs.split(".", 1)
        return f"{obj_label}.{rest}"

    def get_varsets_state(
        self,
        *,
        filter_text: str,
        exclude_copy_on_change: bool,
        use_label: bool,
        selected_keys: set[str],
    ) -> ParentListState:
        """Return render state for the VarSets parent list."""
        getter = getattr(self._controller, "get_filtered_varsets", None)
        if not callable(getter):
            return ParentListState(items=[], selected_keys=set())

        raw_names: list[str] = getter(
            filter_text="" if use_label else filter_text,
            exclude_copy_on_change=exclude_copy_on_change,
        )

        items = [
            DisplayItem(key=n, display=self.format_object_name(n, use_label=use_label))
            for n in raw_names
        ]
        if use_label:
            items = self._filter_display_items(items, filter_text=filter_text)
        return ParentListState(items=items, selected_keys=set(selected_keys))

    def _normalize_glob_pattern(self, text: str) -> str | None:
        stripped = text.strip()
        if not stripped:
            return None
        if not any(ch in stripped for ch in "*?[]"):
            return f"*{stripped}*"
        return stripped

    def _filter_display_items(
        self, items: list[DisplayItem], *, filter_text: str
    ) -> list[DisplayItem]:
        pattern = self._normalize_glob_pattern(filter_text)
        if pattern is None:
            return items
        return [item for item in items if fnmatch.fnmatchcase(item.display, pattern)]

    def get_varset_variables_state(
        self,
        *,
        selected_varsets: list[str],
        variable_filter_text: str,
        only_unused: bool,
        use_label: bool,
        selected_refs: set[object],
    ) -> ChildListState:
        """Return render state for the VarSet variables list."""

        getter = getattr(self._controller, "get_filtered_varset_variable_items", None)
        if not callable(getter):
            return ChildListState(items=[], selected_keys=set())

        refs: list[object] = getter(
            selected_varsets=selected_varsets,
            variable_filter_text=variable_filter_text,
            only_unused=only_unused,
        )

        items = [
            DisplayItem(key=ref, display=self.format_parent_child_ref(ref, use_label=use_label))
            for ref in refs
        ]
        return ChildListState(items=items, selected_keys=set(selected_refs))

    def get_varset_expressions_state(
        self,
        selected_varset_variable_items: list[object],
        *,
        use_label: bool,
    ) -> ExpressionListState:
        """Return render state for the VarSet expressions list."""

        getter = getattr(self._controller, "get_expression_items", None)
        if not callable(getter):
            return ExpressionListState(items=[])

        expr_items, _counts = getter(selected_varset_variable_items)

        items = [
            DisplayItem(key=expr, display=self.format_expression_item(expr, use_label=use_label))
            for expr in expr_items
        ]
        return ExpressionListState(items=items)

    def get_aliases_state(
        self,
        *,
        selected_spreadsheets: list[str],
        alias_filter_text: str,
        only_unused: bool,
        use_label: bool,
        selected_refs: set[object],
    ) -> ChildListState:
        """Return render state for the aliases list."""

        getter = getattr(self._controller, "get_filtered_spreadsheet_alias_items", None)
        if not callable(getter):
            return ChildListState(items=[], selected_keys=set())

        refs: list[object] = getter(
            selected_spreadsheets=selected_spreadsheets,
            alias_filter_text=alias_filter_text,
            only_unused=only_unused,
        )

        items = [
            DisplayItem(key=ref, display=self.format_parent_child_ref(ref, use_label=use_label))
            for ref in refs
        ]
        return ChildListState(items=items, selected_keys=set(selected_refs))

    def get_alias_expressions_state(
        self,
        selected_alias_items: list[object],
        *,
        use_label: bool,
    ) -> ExpressionListState:
        """Return render state for the alias expressions list."""

        getter = getattr(self._controller, "get_alias_expression_items", None)
        if not callable(getter):
            return ExpressionListState(items=[])

        expr_items, _counts = getter(selected_alias_items)
        items = [
            DisplayItem(key=expr, display=self.format_expression_item(expr, use_label=use_label))
            for expr in expr_items
        ]
        return ExpressionListState(items=items)

    def get_spreadsheets_state(
        self,
        *,
        filter_text: str,
        exclude_copy_on_change: bool,
        use_label: bool,
        selected_keys: set[str],
    ) -> ParentListState:
        """Return render state for the Spreadsheets parent list."""
        getter = getattr(self._controller, "get_filtered_spreadsheets", None)
        if not callable(getter):
            return ParentListState(items=[], selected_keys=set())

        raw_names: list[str] = getter(
            filter_text="" if use_label else filter_text,
            exclude_copy_on_change=exclude_copy_on_change,
        )

        items = [
            DisplayItem(key=n, display=self.format_object_name(n, use_label=use_label))
            for n in raw_names
        ]
        if use_label:
            items = self._filter_display_items(items, filter_text=filter_text)
        return ParentListState(items=items, selected_keys=set(selected_keys))
