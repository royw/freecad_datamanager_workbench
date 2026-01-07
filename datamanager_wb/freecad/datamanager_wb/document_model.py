from .varset_tools import getVarsetReferences, getVarsets, getVarsetVariableNames


def get_sorted_varsets() -> list[str]:
    return sorted(getVarsets())


def get_varset_variable_items(selected_varset_names: list[str]) -> list[str]:
    variable_items: list[str] = []
    for varset_name in selected_varset_names:
        for var_name in getVarsetVariableNames(varset_name):
            variable_items.append(f"{varset_name}.{var_name}")

    variable_items.sort()
    return variable_items


def get_expression_items(
    selected_varset_variable_items: list[str],
) -> tuple[list[str], dict[str, int]]:
    expression_items: list[str] = []
    counts: dict[str, int] = {}

    for text in selected_varset_variable_items:
        if "." not in text:
            continue
        varset_name, variable_name = text.split(".", 1)
        refs = getVarsetReferences(varset_name, variable_name)
        counts[text] = len(refs)
        for k, v in refs.items():
            expression_items.append(f"{k} = {v}")

    expression_items.sort()
    return expression_items, counts
