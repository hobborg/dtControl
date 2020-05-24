import sympy

left_formula = sympy.sympify("sqrrrt(225)*x_12+x_3")


subs_list = [(var,1) for var in left_formula.free_symbols]
dummy = left_formula.subs(subs_list).evalf(6)
print(dummy)
