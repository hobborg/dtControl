import sympy as sp
from itertools import product

x_0, x_1, x_2, x_3, x_4, x_5, c_0, c_1, c_2, c_3, c_4, c_5 = sp.symbols('x_0 x_1 x_2 x_3 x_4 x_5 c_0 c_1 c_2 c_3 c_4 c_5')

coef_interval = {c_2: sp.Interval(sp.S.NegativeInfinity, sp.S.Infinity),
                 c_0: sp.Interval(sp.S.NegativeInfinity, sp.S.Infinity),
                 c_3: sp.Interval(sp.S.NegativeInfinity, sp.S.Infinity),
                 c_1: sp.FiniteSet(1.0)}

combinations = []
fixed_coefs = {}
for coef in coef_interval:
    if isinstance(coef_interval[coef], sp.FiniteSet):
        fixed_coefs[coef] = list(coef_interval[coef].args)


if fixed_coefs:
    # unzipping
    coef, val = zip(*fixed_coefs.items())
    # calculation all combinations and zipping back together
    combinations = [list(zip(coef, nbr)) for nbr in product(*val)]
print(combinations)
for i in combinations:
    print(i)