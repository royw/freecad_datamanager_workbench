from __future__ import annotations

from freecad.datamanager_wb import spreadsheet_query


def test_normalize_alias_map_inverts_when_keys_are_cells() -> None:
    raw = {"A1": "foo", "B2": "bar"}
    assert spreadsheet_query._normalize_alias_map(raw) == {"foo": "A1", "bar": "B2"}


def test_normalize_alias_map_keeps_alias_to_cell_mapping() -> None:
    raw = {"foo": "A1", "bar": "B2"}
    assert spreadsheet_query._normalize_alias_map(raw) == raw


def test_build_alias_search_regex_respects_word_boundaries() -> None:
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
