"""Presenter for `MainPanel`.

The presenter owns UI-facing orchestration and formatting decisions while keeping
Qt widgets in `MainPanel` as a thin view layer.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DisplayItem:
    """An item to display in a list widget."""

    key: str
    display: str


@dataclass(frozen=True)
class ParentListState:
    """Render-state for a parent list widget (VarSets or Spreadsheets)."""

    items: list[DisplayItem]
    selected_keys: set[str]


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
