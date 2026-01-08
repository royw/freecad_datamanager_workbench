"""Document-level querying and mutations for VarSets.

This module provides the higher-level operations used by the panel controller
and data sources to list varsets/variables, compute expression references, and
remove unused variables.
"""

from .expression_item import ExpressionItem
from .parent_child_ref import ParentChildRef
from .parsing_helpers import parse_varset_variable_item
from .varset_mutations import removeVarsetVariable
from .varset_query import getVarsetReferences, getVarsets, getVarsetVariableNames


def _normalize_varset_variable_items(
    selected_varset_variable_items: list[ParentChildRef] | list[str],
) -> list[str]:
    normalized: list[str] = []
    for item in selected_varset_variable_items:
        if isinstance(item, ParentChildRef):
            normalized.append(item.text)
        else:
            normalized.append(item)
    return normalized


def get_sorted_varsets(*, exclude_copy_on_change: bool = False) -> list[str]:
    return sorted(getVarsets(exclude_copy_on_change=exclude_copy_on_change))


def get_varset_variable_items(selected_varset_names: list[str]) -> list[str]:
    return [ref.text for ref in get_varset_variable_refs(selected_varset_names)]


def get_varset_variable_refs(selected_varset_names: list[str]) -> list[ParentChildRef]:
    variable_items: list[str] = []
    for varset_name in selected_varset_names:
        for var_name in getVarsetVariableNames(varset_name):
            variable_items.append(f"{varset_name}.{var_name}")

    variable_items.sort()
    refs: list[ParentChildRef] = []
    for text in variable_items:
        parsed = parse_varset_variable_item(text)
        if parsed is None:
            continue
        parent, child = parsed
        refs.append(ParentChildRef(parent=parent, child=child))
    return refs


def get_expression_items(
    selected_varset_variable_items: list[ParentChildRef] | list[str],
) -> tuple[list[ExpressionItem], dict[str, int]]:
    expression_items: list[ExpressionItem] = []
    counts: dict[str, int] = {}

    for text in _normalize_varset_variable_items(selected_varset_variable_items):
        parsed = parse_varset_variable_item(text)
        if parsed is None:
            continue
        varset_name, variable_name = parsed
        refs = getVarsetReferences(varset_name, variable_name)
        counts[text] = len(refs)
        for k, v in refs.items():
            object_name = k.split(".", 1)[0].strip()
            expression_items.append(ExpressionItem(object_name=object_name, lhs=k, rhs=v))

    expression_items.sort(key=lambda item: item.display_text)
    return expression_items, counts


def get_expression_reference_counts(
    selected_varset_variable_items: list[ParentChildRef] | list[str],
) -> dict[str, int]:
    counts: dict[str, int] = {}

    for text in _normalize_varset_variable_items(selected_varset_variable_items):
        parsed = parse_varset_variable_item(text)
        if parsed is None:
            continue
        varset_name, variable_name = parsed
        refs = getVarsetReferences(varset_name, variable_name)
        counts[text] = len(refs)

    return counts


def remove_unused_varset_variables(
    selected_varset_variable_items: list[ParentChildRef] | list[str],
) -> tuple[list[str], list[str], list[str]]:
    removed: list[str] = []
    still_used: list[str] = []
    failed: list[str] = []

    for text in _normalize_varset_variable_items(selected_varset_variable_items):
        parsed = parse_varset_variable_item(text)
        if parsed is None:
            failed.append(text)
            continue
        varset_name, variable_name = parsed
        refs = getVarsetReferences(varset_name, variable_name)
        if refs:
            still_used.append(text)
            continue
        ok = removeVarsetVariable(varset_name, variable_name)
        if ok:
            removed.append(text)
        else:
            failed.append(text)

    return removed, still_used, failed
