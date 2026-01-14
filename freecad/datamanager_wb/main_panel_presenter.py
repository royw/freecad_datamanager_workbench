"""Presenter for `MainPanel`.

The presenter owns UI-facing orchestration and formatting decisions while keeping
Qt widgets in `MainPanel` as a thin view layer.
"""

from __future__ import annotations

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


class MainPanelPresenter:
    """Presenter for `MainPanel` interactions and formatting."""

    def __init__(self, controller: object) -> None:
        self._controller = controller

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

        lhs = getattr(expression_item, "lhs", None)
        rhs = getattr(expression_item, "rhs", None)
        operator = getattr(expression_item, "operator", "=")
        obj_name = getattr(expression_item, "object_name", None)

        if not isinstance(lhs, str) or not isinstance(rhs, str):
            return str(getattr(expression_item, "display_text", ""))

        if not use_label or not isinstance(obj_name, str) or not obj_name:
            return f"{lhs} {operator} {rhs}"

        obj_label = self._get_object_label(obj_name)
        if not obj_label:
            return f"{lhs} {operator} {rhs}"

        if "." in lhs:
            _prefix, rest = lhs.split(".", 1)
            lhs = f"{obj_label}.{rest}"

        return f"{lhs} {operator} {rhs}"

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

        names: list[str] = getter(
            filter_text=filter_text,
            exclude_copy_on_change=exclude_copy_on_change,
        )

        items = [
            DisplayItem(key=n, display=self.format_object_name(n, use_label=use_label))
            for n in names
        ]
        return ParentListState(items=items, selected_keys=set(selected_keys))

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

        names: list[str] = getter(
            filter_text=filter_text,
            exclude_copy_on_change=exclude_copy_on_change,
        )

        items = [
            DisplayItem(key=n, display=self.format_object_name(n, use_label=use_label))
            for n in names
        ]
        return ParentListState(items=items, selected_keys=set(selected_keys))
