from sympy import *

foo = Interval(0, +oo, left_open=True)

infiumum = foo.inf
supremum = foo.sup

middle = (infiumum + supremum )/ 2
print(middle)


