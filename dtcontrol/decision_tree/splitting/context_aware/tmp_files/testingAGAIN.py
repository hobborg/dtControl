import sympy as sp


fooo1 = sp.Interval(sp.S.NegativeInfinity, sp.S.Infinity)

foo2 = sp.Interval(sp.S.NegativeInfinity, sp.S.Infinity)


print(fooo1 == foo2)