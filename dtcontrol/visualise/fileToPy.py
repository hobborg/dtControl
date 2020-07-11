# TODO quantisation information
# Will have number of parameters and their bounds and quantisation already present

import sympy as sp

with open('test.txt') as f:
    my_list = f.read().splitlines()

is_dynamics = False
variable_subs = []
lambda_list = []

for i in my_list:
    i = i.strip()
    if i == 'Dynamics:':
        is_dynamics = True
    elif i == 'Parameters:':
        is_dynamics = False
    else:
        if i != '':
            if not is_dynamics:
                foo = i.split("=")
                variable_subs.append((foo[0].strip(), float(foo[1])))
            else:
                foo = i.split("=")
                tmp = sp.sympify(foo[1].strip())
                tmp = tmp.subs(variable_subs)
                lambda_list.append((foo[0].strip(), tmp))

print(variable_subs)
print(lambda_list)

# args = sorted(lam_1.free_symbols, key=lambda x: int(str(x).split("_")[1]))
# lam_2 = sp.lambdify(args, lam_1)
# print(lam_2)
# print(lam_1)
# print(lam_2(1, 1))
#
# print(lam_1.free_symbols)
