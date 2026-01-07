def parse_varset_variable_item(text: str) -> tuple[str, str] | None:
    if "." not in text:
        return None
    varset_name, variable_name = text.split(".", 1)
    if not varset_name or not variable_name:
        return None
    return varset_name, variable_name


def parse_expression_item_object_name(text: str) -> str | None:
    left = text.split("=", 1)[0].strip()
    obj_name = left.split(".", 1)[0].strip()
    if not obj_name:
        return None
    return obj_name
