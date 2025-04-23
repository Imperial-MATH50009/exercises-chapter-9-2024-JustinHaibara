import numbers  # noqa D100
from functools import singledispatch


class Expression:  # noqa D101

    def __init__(self, *oper):  # noqa D107
        self.operands = oper

    def __add__(self, other):  # noqa D107
        if isinstance(other, numbers.Number):
            return Add(self, Number(other))
        return Add(self, other)

    def __radd__(self, other):  # noqa D107
        if isinstance(other, numbers.Number):
            return Add(Number(other), self)
        return Add(other, self)

    def __sub__(self, other):  # noqa D107
        if isinstance(other, numbers.Number):
            return Sub(self, Number(other))
        return Sub(self, other)

    def __rsub__(self, other):  # noqa D107
        if isinstance(other, numbers.Number):
            return Sub(Number(other), self)
        return Sub(other, self)

    def __mul__(self, other):  # noqa D107
        if isinstance(other, numbers.Number):
            return Mul(self, Number(other))
        return Mul(self, other)

    def __rmul__(self, other):  # noqa D107
        if isinstance(other, numbers.Number):
            return Mul(Number(other), self)
        return Mul(other, self)

    def __truediv__(self, other):  # noqa D107
        if isinstance(other, numbers.Number):
            return Div(self, Number(other))
        return Div(self, other)

    def __rtruediv__(self, other):  # noqa D107
        if isinstance(other, numbers.Number):
            return Div(Number(other), self)
        return Div(other, self)

    def __pow__(self, other):  # noqa D107
        if isinstance(other, numbers.Number):
            return Pow(self, Number(other))
        return Pow(self, other)

    def __rpow__(self, other):  # noqa D107
        if isinstance(other, numbers.Number):
            return Pow(Number(other), self)
        return Pow(other, self)

    def __repr__(self):  # noqa D107
        raise NotImplementedError


class Operator(Expression):  # noqa D101

    def __init__(self, oper1, oper2):  # noqa D107
        super().__init__(oper1, oper2)

    def __repr__(self):  # noqa D107
        return type(self).__name__ + repr(self.operands)

    def __str__(self):  # noqa D107
        oper1, oper2 = self.operands[0], self.operands[1]
        if oper1.precedence > self.precedence:
            if oper2.precedence > self.precedence:
                return f"({str(oper1)}) {self.symbol} ({str(oper2)})"
            else:
                return f"({str(oper1)}) {self.symbol} {str(oper2)}"
        elif oper2.precedence > self.precedence:
            return f"{str(oper1)} {self.symbol} ({str(oper2)})"
        return f"{str(oper1)} {self.symbol} {str(oper2)}"


class Add(Operator):  # noqa D101

    precedence = 3
    symbol = "+"


class Mul(Operator):  # noqa D101

    precedence = 2
    symbol = "*"


class Sub(Operator):  # noqa D101

    precedence = 3
    symbol = "-"


class Div(Operator):  # noqa D101

    precedence = 2
    symbol = "/"


class Pow(Operator):  # noqa D101

    precedence = 1
    symbol = "^"


class Terminal(Expression):  # noqa D101

    precedence = 0

    def __init__(self, val):  # noqa D107
        self.value = val
        super().__init__()

    def __repr__(self):  # noqa D107
        return str(self.value)

    def __str__(self):  # noqa D107
        return str(self.value)


class Number(Terminal):  # noqa D101

    pass


class Symbol(Terminal):  # noqa D101

    pass


def postvisitor(expr, visitor, **kwargs):  # noqa D103

    stack = [expr]
    visited = {}
    while stack:
        e = stack.pop()
        unvisited_children = list()
        for o in e.operands:
            if o not in visited:
                unvisited_children.append(o)
        if unvisited_children:
            stack.append(e)
            for i in unvisited_children:
                stack.append(i)
        else:
            visited[e] = visitor(e, *(visited[o] for o in e.operands),
                                 **kwargs)
    return visited[expr]


@singledispatch
def differentiate(expr, *o, **kwargs):  # noqa D103
    raise NotImplementedError(
        f"Cannot differentiate a {type(expr).__name__}"
    )


@differentiate.register(Number)
def _(expr, *o, **kwargs):
    return Number(0.0)


@differentiate.register(Symbol)
def _(expr, *o, var, **kwargs):
    if str(expr) == var:
        return Number(1.0)
    return Number(0.0)


@differentiate.register(Add)
def _(expr, *o, **kwargs):
    return Add(differentiate(expr.operands[0], *o, **kwargs),
               differentiate(expr.operands[1], *o, **kwargs))


@differentiate.register(Mul)
def _(expr, *o, **kwargs):
    term1 = differentiate(expr.operands[0], *o, **kwargs) * expr.operands[1]
    term2 = expr.operands[0] * differentiate(expr.operands[1], *o, **kwargs)
    return Add(term1, term2)


@differentiate.register(Div)
def _(expr, *o, **kwargs):
    term1 = differentiate(expr.operands[0], *o, **kwargs) * expr.operands[1]
    term2 = expr.operands[0] * differentiate(expr.operands[1], *o, **kwargs)
    return (term1 - term2) / expr.operands[1] ** 2


@differentiate.register(Pow)
def _(expr, *o, **kwargs):
    term1 = differentiate(expr.operands[0], *o, **kwargs)
    term1 *= expr.operands[1] * expr.operands[0] ** (expr.operands[1] - 1)
    return term1
