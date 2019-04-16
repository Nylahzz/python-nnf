import functools
import operator

import typing as t

from nnf import NNF, And, Var, Or, Name, true, false

T = t.TypeVar('T')


def eval(
        node: NNF,
        add: t.Callable[[T, T], T],
        mul: t.Callable[[T, T], T],
        add_neut: T,
        mul_neut: T,
        labeling: t.Callable[[Var], T],
) -> T:
    if node == true:
        return mul_neut
    if node == false:
        return add_neut
    if isinstance(node, Var):
        return labeling(node)
    if isinstance(node, Or):
        return functools.reduce(
            add,
            (eval(child, add, mul, add_neut, mul_neut, labeling)
             for child in node.children),
            add_neut
        )
    if isinstance(node, And):
        return functools.reduce(
            mul,
            (eval(child, add, mul, add_neut, mul_neut, labeling)
             for child in node.children),
            mul_neut
        )
    raise TypeError(type(node))


def SAT(node: NNF) -> bool:
    return eval(node, operator.or_, operator.and_, False, True,
                lambda leaf: True)


def NUM_SAT(node: NNF) -> int:
    # Non-idempotent +
    # Non-neutral +
    # General ×
    # = sd-DNNF
    return eval(node, operator.add, operator.mul, 0, 1, lambda leaf: 1)


GradProb = t.Tuple[float, float]


def GRAD(
        node: NNF,
        probs: t.Dict[Name, float],
        k: t.Optional[Name] = None
) -> GradProb:
    # General ×
    # Neutral +
    # Non-idempotent +
    # = d-DNNF

    def add(a: GradProb, b: GradProb) -> GradProb:
        return a[0] + b[0], a[1] + b[1]

    def mul(a: GradProb, b: GradProb) -> GradProb:
        return a[0] * b[0], a[0] * b[1] + a[1] * b[0]

    def label(var: Var) -> GradProb:
        if var.true:
            if var.name == k:
                return probs[var.name], 1
            else:
                return probs[var.name], 0
        else:
            if var.name == k:
                return 1 - probs[var.name], -1
            else:
                return 1 - probs[var.name], 0

    return eval(node, add, mul, (0.0, 0.0), (1.0, 0.0), label)
