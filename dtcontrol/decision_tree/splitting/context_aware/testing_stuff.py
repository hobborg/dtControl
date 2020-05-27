import sympy

expr = sympy.sympify("10.974395*x_2-32.230035")
const = expr.func(*[term for term in expr.args if not term.free_symbols])
new_args = []

for i in expr.args:
    if not i.free_symbols:
        new_args.append(99)
    else:
        new_args.append(i)
print(expr.args)
print(new_args)
expr_1 = expr.func(*tuple(new_args))
print(expr_1)


