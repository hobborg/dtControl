from sympy import *

x = Symbol('x')
foo = Interval(0,1).open(0,1)

sin_sols = ConditionSet(x, Eq(sin(x), 0), Interval(0, 2*pi))
pprint(sin_sols)

print(FiniteSet(1,2,3,4,5,6,7,8,9,"10"))