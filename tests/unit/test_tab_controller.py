from freecad.datamanager_wb.parent_child_ref import ParentChildRef
from freecad.datamanager_wb.tab_controller import TabController
from freecad.datamanager_wb.tab_datasource import RemoveUnusedResult


class FakeDataSource:
    def __init__(self):
        self.parents = ["A", "B", "CopyOnChange1"]
        self.children = {
            "A": [ParentChildRef(parent="A", child="x"), ParentChildRef(parent="A", child="y")],
            "B": [ParentChildRef(parent="B", child="z")],
        }
        self.counts = {
            "A.x": 0,
            "A.y": 2,
            "B.z": 0,
        }

    def get_sorted_parents(self, *, exclude_copy_on_change: bool = False) -> list[str]:
        if exclude_copy_on_change:
            return [p for p in self.parents if not p.startswith("CopyOnChange")]
        return sorted(self.parents)

    def get_child_refs(self, selected_parents: list[str]):
        refs = []
        for p in selected_parents:
            refs.extend(self.children.get(p, []))
        return sorted(refs, key=lambda r: r.text)

    def get_expression_items(self, selected_children):
        # Not needed for these tests
        return [], {k: self.counts.get(k, 0) for k in _normalize(selected_children)}

    def get_expression_reference_counts(self, selected_children):
        return {k: self.counts.get(k, 0) for k in _normalize(selected_children)}

    def remove_unused_children(self, selected_children):
        removed = []
        still_used = []
        failed = []
        for k in _normalize(selected_children):
            if self.counts.get(k, 0) != 0:
                still_used.append(k)
                continue
            removed.append(k)
        return RemoveUnusedResult(removed=removed, still_used=still_used, failed=failed)


def _normalize(items):
    out = []
    for i in items:
        out.append(i.text if isinstance(i, ParentChildRef) else i)
    return out


def test_get_filtered_parents_plain_substring_becomes_glob():
    c = TabController(FakeDataSource())
    assert c.get_filtered_parents(filter_text="A") == ["A"]


def test_get_filtered_child_items_only_unused_filters_by_counts():
    c = TabController(FakeDataSource())
    items = c.get_filtered_child_items(selected_parents=["A"], child_filter_text="", only_unused=True)
    assert [i.text for i in items] == ["A.x"]


def test_remove_unused_and_get_update_returns_post_update_items():
    c = TabController(FakeDataSource())
    result = c.remove_unused_and_get_update(
        selected_child_items=[ParentChildRef(parent="A", child="x"), ParentChildRef(parent="A", child="y")],
        selected_parents=["A"],
        child_filter_text="",
        only_unused=True,
    )
    assert result.remove_result.removed == ["A.x"]
    assert "A.y" in result.remove_result.still_used
    assert [r.text for r in result.update.child_items] == ["A.x"]
