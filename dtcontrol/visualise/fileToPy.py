# TODO quantisation information
# Will have number of parameters and their bounds and quantisation already present

import sympy as sp
import os

variable_subs = []
lambda_list = []
numVars = 2
numResults = 1

is_dynamics = False
SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
dynamics_data_file = os.path.join(SITE_ROOT, 'test.txt')

with open(dynamics_data_file) as f:
    my_list = f.read().splitlines()
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
                lam_1 = sp.lambdify(tmp.free_symbols, tmp)
                lambda_list.append((foo[0].strip(), lam_1, tmp.free_symbols))

print(variable_subs)
lambda_list = sorted(lambda_list, key=lambda x: int(x[0].split("_")[1]))
print(lambda_list)


def runge_kutta(x, u, tau, x0=0, nint=10):
    # h is 0.01, may be adjusted later, x0 is 0
    # n = int((tau - x0) / h)
    h = tau/nint
    # everywhere fix h as 10
    # tau = 1 for 10 rooms

    # Step height h, step size n
    k0 = [None] * len(x)
    k1 = [None] * len(x)
    k2 = [None] * len(x)
    k3 = [None] * len(x)
    for iter in range(1, nint + 1):
        # "Apply Runge Kutta Formulas to find next value of y and z"
        for i in range(len(x)):
            k0[i] = h * computation(i, x, u, lambda_list)
        for i in range(len(x)):
            k1[i] = h * computation(i, [(x[j] + 0.5 * k0[j]) for j in range(len(x))], u, lambda_list)
        for i in range(len(x)):
            k2[i] = h * computation(i, [(x[j] + 0.5 * k1[j]) for j in range(len(x))], u, lambda_list)
        for i in range(len(x)):
            k3[i] = h * computation(i, [(x[j] + k2[j]) for j in range(len(x))], u, lambda_list)
        for i in range(len(x)):
            x[i] = x[i] + (1.0 / 6.0) * (k0[i] + 2 * k1[i] + 2 * k2[i] + k3[i])

    return x


def computation(index, x, u, ll):
    new_vl = []
    for name in ll[index][2]:
        spilt_of_var = (str(name)).split('_')
        if spilt_of_var[0] == 'x':
            new_vl.append(x[int(spilt_of_var[1])])
        else:
            new_vl.append(u[int(spilt_of_var[1])])
    return float(ll[index][1](*tuple(new_vl)))


print(runge_kutta([3.5, 0], [-3], 0.3))

