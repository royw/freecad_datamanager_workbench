"""Lightweight representation of an expression binding.

This module defines a small dataclass used to display and select expression
engine entries in the UI."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ExpressionItem:
    object_name: str
    lhs: str
    rhs: str

    @property
    def display_text(self) -> str:
        return f"{self.lhs} = {self.rhs}"
