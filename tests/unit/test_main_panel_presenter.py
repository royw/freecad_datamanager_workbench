from __future__ import annotations

from freecad.datamanager_wb.expression_item import ExpressionItem
from freecad.datamanager_wb.main_panel_presenter import MainPanelPresenter
from freecad.datamanager_wb.parent_child_ref import ParentChildRef


class FakeController:
    def __init__(self) -> None:
        self.labels: dict[str, str] = {}
        self.varsets: list[str] = []
        self.sheets: list[str] = []

    def get_object_label(self, object_name: str) -> str | None:
        return self.labels.get(object_name)

    def get_filtered_varsets(self, *, filter_text: str, exclude_copy_on_change: bool = False) -> list[str]:
        return list(self.varsets)

    def get_filtered_spreadsheets(
        self, *, filter_text: str, exclude_copy_on_change: bool = False
    ) -> list[str]:
        return list(self.sheets)

    def get_filtered_varset_variable_items(
        self,
        *,
        selected_varsets: list[str],
        variable_filter_text: str,
        only_unused: bool,
    ) -> list[ParentChildRef]:
        return [ParentChildRef(parent=v, child="X") for v in selected_varsets]

    def get_expression_items(self, selected_vars: list[ParentChildRef] | list[str]):
        return [ExpressionItem(object_name="Box", lhs="Box.Length", rhs="1")], {}

    def get_filtered_spreadsheet_alias_items(
        self,
        *,
        selected_spreadsheets: list[str],
        alias_filter_text: str,
        only_unused: bool,
    ) -> list[ParentChildRef]:
        return [ParentChildRef(parent=s, child="Alias") for s in selected_spreadsheets]

    def get_alias_expression_items(self, selected_aliases: list[ParentChildRef] | list[str]):
        return [ExpressionItem(object_name="Sheet", lhs="Sheet.Alias", rhs="42")], {}


def test_format_object_name_label_mode_uses_label() -> None:
    ctrl = FakeController()
    ctrl.labels["Box"] = "BoxLabel"

    p = MainPanelPresenter(ctrl)
    assert p.format_object_name("Box", use_label=True) == "BoxLabel"


def test_format_object_name_label_mode_handles_dotted_names() -> None:
    ctrl = FakeController()
    ctrl.labels["Box"] = "BoxLabel"

    p = MainPanelPresenter(ctrl)
    assert p.format_object_name("Box.Length", use_label=True) == "BoxLabel.Length"


def test_format_object_name_label_mode_falls_back_to_name() -> None:
    ctrl = FakeController()
    p = MainPanelPresenter(ctrl)

    assert p.format_object_name("Missing", use_label=True) == "Missing"
    assert p.format_object_name("Missing.Prop", use_label=True) == "Missing.Prop"


def test_get_varsets_state_formats_display_and_preserves_selection() -> None:
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
    ctrl = FakeController()
    ctrl.labels["Box"] = "BoxLabel"

    p = MainPanelPresenter(ctrl)
    state = p.get_varset_expressions_state([ParentChildRef(parent="Var", child="X")], use_label=True)

    assert len(state.items) == 1
    assert "BoxLabel.Length" in state.items[0].display


def test_get_aliases_state_formats_parent_child_with_label() -> None:
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
    ctrl = FakeController()
    ctrl.labels["Sheet"] = "SheetLabel"

    p = MainPanelPresenter(ctrl)
    state = p.get_alias_expressions_state([ParentChildRef(parent="Sheet", child="Alias")], use_label=True)

    assert len(state.items) == 1
    assert "SheetLabel.Alias" in state.items[0].display


def test_get_active_document_change_plan_clears_and_repopulates() -> None:
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
