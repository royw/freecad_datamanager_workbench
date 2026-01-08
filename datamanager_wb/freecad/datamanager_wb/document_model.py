from .expression_item import ExpressionItem
from .parsing_helpers import parse_varset_variable_item
from .varset_tools import getVarsetReferences, getVarsets, getVarsetVariableNames


def get_sorted_varsets(*, exclude_copy_on_change: bool = False) -> list[str]:
    return sorted(getVarsets(exclude_copy_on_change=exclude_copy_on_change))


def get_varset_variable_items(selected_varset_names: list[str]) -> list[str]:
    variable_items: list[str] = []
    for varset_name in selected_varset_names:
        for var_name in getVarsetVariableNames(varset_name):
            variable_items.append(f"{varset_name}.{var_name}")

    variable_items.sort()
    return variable_items


def get_expression_items(
    selected_varset_variable_items: list[str],
) -> tuple[list[ExpressionItem], dict[str, int]]:
    expression_items: list[ExpressionItem] = []
    counts: dict[str, int] = {}

    for text in selected_varset_variable_items:
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


def get_expression_reference_counts(selected_varset_variable_items: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}

    for text in selected_varset_variable_items:
        parsed = parse_varset_variable_item(text)
        if parsed is None:
            continue
        varset_name, variable_name = parsed
        refs = getVarsetReferences(varset_name, variable_name)
        counts[text] = len(refs)

    return counts
