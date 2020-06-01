import inspect
import sympy as sp
import numpy as np
from inspect import Parameter, signature, Signature

from scipy.optimize import curve_fit

for i in range(4):
    print(i)

term = sp.sympify("c0*x_0 + c1*x_1 + c2*x_2 + c3*x_3 + c4")

x = np.array(
    [[1., 4.6, 1., 3.],
     [1., 4.6, 2., 3.],
     [2., 4., 3., 1.],
     [2., 4., 3., 2.],
     [1., 4., 4., 1.],
     [2., 4., 4., 2.],
     [2., 53., 2., 3.],
     [1., 228., 1., 5.],
     [2., 93., 1., 2.],
     [2., 59., 3., 2.]])
y_1 = np.array([1, 1, -1, -1, -1, -1, -1, -1, -1, -1])


def fun_input_helper(x, c0, c1, c2, c3, c4):
    out = []
    for features in range(x.shape[0]):
        subs_list = [("c0", c0), ("c1", c1), ("c2", c2), ("c3", c3), ("c4", c4)]
        for i in range(len(x[features, :])):
            subs_list.append(("x_" + str(i), x[features, i]))

        result = float(term.subs(subs_list).evalf())
        out.append(result)

    return np.array(out)


c1, c2, c3, c4 = sp.symbols('c1 c2 c3 c4')
coef_interval = {c1: {6, 32, 34433}, c2: {1, 2, 3}, c3: {5, 10, 32, 40}, c4: {1, 2, 3}}


def get_adapter():
    # https://stackoverflow.com/questions/27670661/python-exact-number-of-arguments-defined-by-variable
    # dataset input
    params = [Parameter("x", Parameter.POSITIONAL_ONLY)]
    # variable coefs
    params.extend([Parameter(str(coef), Parameter.POSITIONAL_ONLY) for coef in coef_interval])

    def input_adapter(x, *args):
        out = []
        for features in range(x.shape[0]):
            subs_list = []
            for arg_index in range(len(args)):
                subs_list.append(("c" + str(arg_index), args[arg_index]))
            for i in range(len(x[features, :])):
                subs_list.append(("x_" + str(i), x[features, i]))

            result = float(term.subs(subs_list).evalf())
            out.append(result)
        return np.array(out)

    input_adapter.__signature__ = signature(input_adapter).replace(parameters=params)
    return input_adapter


def input_adapter(x, *args):
    out = []
    for features in range(x.shape[0]):
        subs_list = []
        for arg_index in range(len(args)):
            subs_list.append(("c" + str(arg_index), args[arg_index]))
        for i in range(len(x[features, :])):
            subs_list.append(("x_" + str(i), x[features, i]))

        result = float(term.subs(subs_list).evalf())
        out.append(result)
    return np.array(out)


g = [1, 1, 1, 1,1]
c, cov = curve_fit(input_adapter, x, y_1, g)
print(c)
