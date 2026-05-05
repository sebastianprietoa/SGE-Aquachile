from __future__ import annotations

import ast
import operator
from dataclasses import dataclass
from typing import Iterable


@dataclass(slots=True)
class VariableValidationIssue:
    variable_code: str
    message: str
    severity: str


def calculate_expected_consumption(intercept: float, coefficients: dict[str, float] | None, variable_values: dict[str, float]) -> float | None:
    coefficients = coefficients or {}
    missing_codes = [code for code in coefficients if code not in variable_values]
    if missing_codes:
        return None
    total = float(intercept or 0.0)
    for code, coefficient in coefficients.items():
        total += float(coefficient) * float(variable_values[code])
    return round(total, 4)


def calculate_difference(real_consumption: float | None, expected_consumption: float | None) -> float | None:
    if real_consumption is None or expected_consumption is None:
        return None
    return round(float(real_consumption) - float(expected_consumption), 4)


def calculate_percentage_difference(difference: float | None, expected_consumption: float | None) -> float | None:
    if difference is None or expected_consumption in (None, 0):
        return None
    return round((float(difference) / float(expected_consumption)) * 100, 4)


def classify_compliance(percentage_difference: float | None, has_all_required: bool, real_consumption: float | None, expected_consumption: float | None) -> str:
    if not has_all_required or real_consumption is None or expected_consumption in (None, 0):
        return "incomplete"
    if percentage_difference is None:
        return "incomplete"
    if abs(percentage_difference) <= 10:
        return "compliant"
    if abs(percentage_difference) <= 20:
        return "warning"
    return "non_compliant"


def calculate_ide_value(real_consumption: float | None, denominator_value: float | None) -> float | None:
    if real_consumption is None or denominator_value in (None, 0):
        return None
    return round(float(real_consumption) / float(denominator_value), 4)


def get_denominator_value(denominator_code: str | None, variable_values: dict[str, float]) -> float | None:
    if not denominator_code:
        return None
    return variable_values.get(denominator_code)


_ALLOWED_BINOPS: dict[type[ast.AST], object] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}
_ALLOWED_UNARYOPS: dict[type[ast.AST], object] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def evaluate_formula(formula_text: str | None, variable_values: dict[str, float]) -> float | None:
    if not formula_text:
        return None

    expression = formula_text.replace("^", "**")
    tree = ast.parse(expression, mode="eval")

    def _eval(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.Name):
            if node.id not in variable_values:
                raise KeyError(node.id)
            return float(variable_values[node.id])
        if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
            left = _eval(node.left)
            right = _eval(node.right)
            return float(_ALLOWED_BINOPS[type(node.op)](left, right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARYOPS:
            operand = _eval(node.operand)
            return float(_ALLOWED_UNARYOPS[type(node.op)](operand))
        raise ValueError(f"Unsupported formula element: {ast.dump(node, include_attributes=False)}")

    try:
        return round(_eval(tree), 4)
    except (KeyError, ZeroDivisionError, ValueError, SyntaxError):
        return None


def calculate_ide_from_formula(formula_text: str | None, variable_values: dict[str, float]) -> float | None:
    return evaluate_formula(formula_text, variable_values)


def validate_variable_ranges(
    baseline_variables: Iterable[tuple[str, float | None, float | None, bool]],
    variable_values: dict[str, float],
) -> list[VariableValidationIssue]:
    issues: list[VariableValidationIssue] = []
    for code, min_value, max_value, required in baseline_variables:
        if code not in variable_values:
            if required:
                issues.append(VariableValidationIssue(code, "Variable requerida no informada", "critical"))
            continue
        value = float(variable_values[code])
        if min_value is not None and value < min_value:
            issues.append(VariableValidationIssue(code, f"Valor bajo mínimo permitido ({min_value})", "medium"))
        if max_value is not None and value > max_value:
            issues.append(VariableValidationIssue(code, f"Valor sobre máximo permitido ({max_value})", "high"))
    return issues


def has_all_required_variables(required_codes: Iterable[str], variable_values: dict[str, float]) -> bool:
    return all(code in variable_values for code in required_codes)
