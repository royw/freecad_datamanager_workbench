from __future__ import annotations

from freecad.datamanager_wb.main_panel_presenter import MainPanelPresenter


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
