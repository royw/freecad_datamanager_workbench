from __future__ import annotations

from freecad.datamanager_wb.domain.expression_item import ExpressionItem
from freecad.datamanager_wb.main_panel_presenter import MainPanelPresenter
from freecad.datamanager_wb.domain.parent_child_ref import ParentChildRef


class FakeController:
    def __init__(self) -> None:
        self.labels: dict[str, str] = {}
        self.varsets: list[str] = []
        self.sheets: list[str] = []

    def get_object_label(self, object_name: str) -> str | None:
        return self.labels.get(object_name)

    def get_filtered_varsets(
        self, *, filter_text: str, exclude_copy_on_change: bool = False
    ) -> list[str]:
        _filter_text = filter_text
        _exclude_copy_on_change = exclude_copy_on_change
        return list(self.varsets)

    def get_filtered_spreadsheets(
        self, *, filter_text: str, exclude_copy_on_change: bool = False
    ) -> list[str]:
        _filter_text = filter_text
        _exclude_copy_on_change = exclude_copy_on_change
        return list(self.sheets)

    def get_filtered_varset_variable_items(
        self,
        *,
        selected_varsets: list[str],
        variable_filter_text: str,
        only_unused: bool,
    ) -> list[ParentChildRef]:
        _variable_filter_text = variable_filter_text
        _only_unused = only_unused
        return [ParentChildRef(parent=v, child="X") for v in selected_varsets]

    def get_expression_items(self, selected_vars: list[ParentChildRef] | list[str]):
        _selected_vars = selected_vars
        return [ExpressionItem(object_name="Box", lhs="Box.Length", rhs="1")], {}

    def get_filtered_spreadsheet_alias_items(
        self,
        *,
        selected_spreadsheets: list[str],
        alias_filter_text: str,
        only_unused: bool,
    ) -> list[ParentChildRef]:
        _alias_filter_text = alias_filter_text
        _only_unused = only_unused
        return [ParentChildRef(parent=s, child="Alias") for s in selected_spreadsheets]

    def get_alias_expression_items(self, selected_aliases: list[ParentChildRef] | list[str]):
        _selected_aliases = selected_aliases
        return [ExpressionItem(object_name="Sheet", lhs="Sheet.Alias", rhs="42")], {}

    def should_enable_remove_unused(self, *, only_unused: bool, selected_count: int) -> bool:
        return bool(only_unused and selected_count > 0)


def test_format_object_name_label_mode_uses_label() -> None:
    """format_object_name uses object labels when label mode is enabled."""
    ctrl = FakeController()
    ctrl.labels["Box"] = "BoxLabel"

    p = MainPanelPresenter(ctrl)
    assert p.format_object_name("Box", use_label=True) == "BoxLabel"


def test_format_object_name_label_mode_handles_dotted_names() -> None:
    """format_object_name preserves the property suffix when formatting dotted names."""
    ctrl = FakeController()
    ctrl.labels["Box"] = "BoxLabel"

    p = MainPanelPresenter(ctrl)
    assert p.format_object_name("Box.Length", use_label=True) == "BoxLabel.Length"


def test_format_object_name_label_mode_falls_back_to_name() -> None:
    """format_object_name falls back to the original name when no label is available."""
    ctrl = FakeController()
    p = MainPanelPresenter(ctrl)

    assert p.format_object_name("Missing", use_label=True) == "Missing"
    assert p.format_object_name("Missing.Prop", use_label=True) == "Missing.Prop"


def test_get_varsets_state_formats_display_and_preserves_selection() -> None:
    """get_varsets_state formats items and preserves selected keys."""
    ctrl = FakeController()
    ctrl.varsets = ["A", "B.Prop"]
    ctrl.labels["B"] = "Bee"

    p = MainPanelPresenter(ctrl)
    state = p.get_varsets_state(
        filter_text="",
        exclude_copy_on_change=False,
        use_label=True,
        selected_keys={"A"},
    )

    assert [i.key for i in state.items] == ["A", "B.Prop"]
    assert [i.display for i in state.items] == ["A", "Bee.Prop"]
    assert state.selected_keys == {"A"}


def test_get_varset_variables_state_formats_parent_child_with_label() -> None:
    """get_varset_variables_state formats parent.child refs using labels when enabled."""
    ctrl = FakeController()
    ctrl.labels["Var"] = "VarLabel"

    p = MainPanelPresenter(ctrl)
    state = p.get_varset_variables_state(
        selected_varsets=["Var"],
        variable_filter_text="",
        only_unused=False,
        use_label=True,
        selected_refs=set(),
    )

    assert len(state.items) == 1
    assert state.items[0].display == "VarLabel.X"


def test_get_varset_expressions_state_formats_expression_with_label() -> None:
    """get_varset_expressions_state formats expression items using labels when enabled."""
    ctrl = FakeController()
    ctrl.labels["Box"] = "BoxLabel"

    p = MainPanelPresenter(ctrl)
    state = p.get_varset_expressions_state([ParentChildRef(parent="Var", child="X")], use_label=True)

    assert len(state.items) == 1
    assert "BoxLabel.Length" in state.items[0].display


def test_get_aliases_state_formats_parent_child_with_label() -> None:
    """get_aliases_state formats alias parent.child refs using labels when enabled."""
    ctrl = FakeController()
    ctrl.labels["Sheet"] = "SheetLabel"

    p = MainPanelPresenter(ctrl)
    state = p.get_aliases_state(
        selected_spreadsheets=["Sheet"],
        alias_filter_text="",
        only_unused=False,
        use_label=True,
        selected_refs=set(),
    )

    assert len(state.items) == 1
    assert state.items[0].display == "SheetLabel.Alias"


def test_get_alias_expressions_state_formats_expression_with_label() -> None:
    """get_alias_expressions_state formats alias expression items using labels when enabled."""
    ctrl = FakeController()
    ctrl.labels["Sheet"] = "SheetLabel"

    p = MainPanelPresenter(ctrl)
    state = p.get_alias_expressions_state([ParentChildRef(parent="Sheet", child="Alias")], use_label=True)

    assert len(state.items) == 1
    assert "SheetLabel.Alias" in state.items[0].display


def test_get_active_document_change_plan_clears_and_repopulates() -> None:
    """get_active_document_change_plan requests clearing and repopulating all UI lists."""
    p = MainPanelPresenter(FakeController())
    plan = p.get_active_document_change_plan()

    assert plan.clear_varsets_selection
    assert plan.clear_spreadsheets_selection
    assert plan.repopulate_varsets
    assert plan.repopulate_spreadsheets
    assert plan.clear_varset_variable_names
    assert plan.clear_varset_expressions
    assert plan.clear_alias_names
    assert plan.clear_alias_expressions


def test_should_enable_remove_unused_delegates_to_controller() -> None:
    """should_enable_remove_unused delegates enablement logic to the controller."""
    p = MainPanelPresenter(FakeController())
    assert not p.should_enable_remove_unused(only_unused=False, selected_count=1)
    assert not p.should_enable_remove_unused(only_unused=True, selected_count=0)
    assert p.should_enable_remove_unused(only_unused=True, selected_count=2)


def test_should_enable_copy_button_requires_focus_and_selection() -> None:
    """should_enable_copy_button requires list focus and a non-empty selection."""
    p = MainPanelPresenter(FakeController())
    assert not p.should_enable_copy_button(list_has_focus=False, selected_count=1)
    assert not p.should_enable_copy_button(list_has_focus=True, selected_count=0)
    assert p.should_enable_copy_button(list_has_focus=True, selected_count=2)


def test_get_show_plan_without_mdi_shows_standalone() -> None:
    """get_show_plan chooses standalone display when MDI is not available."""
    p = MainPanelPresenter(FakeController())
    plan = p.get_show_plan(mdi_available=False, has_existing_subwindow=False)
    assert plan.show_standalone
    assert not plan.reuse_subwindow
    assert not plan.create_subwindow


def test_get_show_plan_with_existing_subwindow_reuses() -> None:
    """get_show_plan reuses an existing MDI subwindow when present."""
    p = MainPanelPresenter(FakeController())
    plan = p.get_show_plan(mdi_available=True, has_existing_subwindow=True)
    assert not plan.show_standalone
    assert plan.reuse_subwindow
    assert not plan.create_subwindow


def test_get_show_plan_with_mdi_creates_subwindow() -> None:
    """get_show_plan creates a new MDI subwindow when MDI is available and none exists."""
    p = MainPanelPresenter(FakeController())
    plan = p.get_show_plan(mdi_available=True, has_existing_subwindow=False)
    assert not plan.show_standalone
    assert not plan.reuse_subwindow
    assert plan.create_subwindow
