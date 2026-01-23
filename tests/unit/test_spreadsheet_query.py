"""Unit tests for spreadsheet alias query helpers."""

from __future__ import annotations

from freecad.DataManager.spreadsheets import spreadsheet_query


def test_normalize_alias_map_inverts_when_keys_are_cells() -> None:
    """_normalize_alias_map inverts a cell->alias mapping into alias->cell."""
    raw = {"A1": "foo", "B2": "bar"}
    assert spreadsheet_query._normalize_alias_map(raw) == {"foo": "A1", "bar": "B2"}


def test_normalize_alias_map_keeps_alias_to_cell_mapping() -> None:
    """_normalize_alias_map preserves an alias->cell mapping."""
    raw = {"foo": "A1", "bar": "B2"}
    assert spreadsheet_query._normalize_alias_map(raw) == raw


def test_build_alias_search_regex_respects_word_boundaries() -> None:
    """Alias matching treats alias tokens as word-boundary matches to avoid false positives."""
    patterns, alias_re = spreadsheet_query._build_alias_search(
        label_or_name="Sheet", alias_name="foo"
    )
    assert alias_re is not None

    assert spreadsheet_query._matches_expression(
        expr_text="foo + 1", patterns=patterns, alias_re=alias_re
    )
    assert not spreadsheet_query._matches_expression(
        expr_text="foobar + 1", patterns=patterns, alias_re=alias_re
    )


def test_get_spreadsheet_alias_references_does_not_match_other_spreadsheet_prefix(monkeypatch) -> None:
    """getSpreadsheetAliasReferences should not match CopyOnChange clones like Params001 when querying Params."""

    class _FakePort:
        def __init__(self) -> None:
            self._doc = object()

        def get_active_document(self):
            return self._doc

        def get_typed_object(self, _doc, name: str, *, type_id: str):
            _type_id = type_id

            class _Sheet:
                def __init__(self, *, sheet_name: str) -> None:
                    self.Name = sheet_name
                    self.Label = sheet_name

            return _Sheet(sheet_name=name)

    fake_port = _FakePort()

    monkeypatch.setattr(
        spreadsheet_query,
        "get_port",
        lambda _ctx=None: fake_port,
    )
    monkeypatch.setattr(
        spreadsheet_query,
        "_get_active_spreadsheet",
        lambda spreadsheet_name, *, ctx=None: fake_port.get_typed_object(
            fake_port.get_active_document(), spreadsheet_name, type_id="Spreadsheet::Sheet"
        ),
    )

    def _fake_iter_named_expression_engine_entries(_doc):
        yield "LinearPattern", "Occurrences", "<<Params>>.BoomSegments"
        yield "LinearPattern013", "Occurrences", "<<Params001>>.BoomSegments"

    monkeypatch.setattr(
        spreadsheet_query,
        "iter_named_expression_engine_entries",
        _fake_iter_named_expression_engine_entries,
    )
    monkeypatch.setattr(
        spreadsheet_query,
        "_add_internal_alias_refs",
        lambda *, sheet, alias_re, results: None,
    )

    refs = spreadsheet_query.getSpreadsheetAliasReferences("Params", "BoomSegments")
    assert list(refs.keys()) == ["LinearPattern.Occurrences"]
