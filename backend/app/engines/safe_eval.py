"""Safe arithmetic formula evaluator used for every configurable formula.

Only numbers, named variables, + - * / // % **, comparisons (return 1/0) and
min/max/ceil/floor/round/abs are allowed. No attribute access and no other
calls, so formulas stored in the database cannot execute code.
"""
import ast
import math
import operator as op

_BIN = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv,
        ast.FloorDiv: op.floordiv, ast.Mod: op.mod, ast.Pow: op.pow}
_CMP = {ast.Gt: op.gt, ast.Lt: op.lt, ast.GtE: op.ge, ast.LtE: op.le,
        ast.Eq: op.eq, ast.NotEq: op.ne}
_FUNCS = {"min": min, "max": max, "ceil": math.ceil, "floor": math.floor,
          "round": round, "abs": abs}


class FormulaError(ValueError):
    pass


def evaluate(expr, variables: dict) -> float:
    if isinstance(expr, (int, float)):
        return float(expr)
    try:
        tree = ast.parse(str(expr).strip(), mode="eval")
    except SyntaxError as e:
        raise FormulaError(f"Invalid formula '{expr}': {e.msg}") from e

    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) \
                and not isinstance(n.value, bool):
            return n.value
        if isinstance(n, ast.Name):
            if n.id in variables:
                return variables[n.id]
            raise FormulaError(f"Unknown variable '{n.id}' in formula '{expr}'")
        if isinstance(n, ast.BinOp) and type(n.op) in _BIN:
            a, b = ev(n.left), ev(n.right)
            if isinstance(n.op, ast.Pow) and abs(b) > 8:
                raise FormulaError("Exponent too large")
            return _BIN[type(n.op)](a, b)
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.USub, ast.UAdd)):
            v = ev(n.operand)
            return -v if isinstance(n.op, ast.USub) else v
        if isinstance(n, ast.Compare):
            left = ev(n.left)
            for o, c in zip(n.ops, n.comparators):
                right = ev(c)
                if type(o) not in _CMP or not _CMP[type(o)](left, right):
                    return 0.0
                left = right
            return 1.0
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
                and n.func.id in _FUNCS and not n.keywords:
            return _FUNCS[n.func.id](*[ev(a) for a in n.args])
        raise FormulaError(f"Unsupported syntax in formula '{expr}'")

    try:
        return float(ev(tree))
    except ZeroDivisionError as e:
        raise FormulaError(f"Division by zero in formula '{expr}'") from e
