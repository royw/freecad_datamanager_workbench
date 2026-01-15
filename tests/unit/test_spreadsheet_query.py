from __future__ import annotations

from freecad.datamanager_wb.spreadsheets import spreadsheet_query


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
