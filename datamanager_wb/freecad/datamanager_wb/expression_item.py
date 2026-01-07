from dataclasses import dataclass


@dataclass(frozen=True)
class ExpressionItem:
    object_name: str
    lhs: str
    rhs: str

    @property
    def display_text(self) -> str:
        return f"{self.lhs} = {self.rhs}"
