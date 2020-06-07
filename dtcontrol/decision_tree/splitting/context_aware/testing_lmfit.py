import numpy as np
from lmfit import Model
from lmfit import Parameters
from inspect import Parameter, signature, Signature

from dtcontrol.decision_tree.splitting.context_aware.weinhuber_approach_split import WeinhuberApproachSplit


def adapter(coefs_arg):
    def func(*args):
        result = []

        x = args[0]
        c_0 = args[1]
        c_1 = args[2]
        c_2 = args[3]
        c_3 = args[4]
        c_4 = args[5]

        x = x.reshape((10, 4))
        for row in range(x.shape[0]):
            term = c_0 * x[row, 0] + c_1 * x[row, 1] + c_2 * x[row, 2] + c_3 * x[row, 3] - c_4
            result.append(term)
        return np.array(result)

    params = [Parameter('x', Parameter.POSITIONAL_OR_KEYWORD)]
    params.extend([Parameter(coef, Parameter.POSITIONAL_OR_KEYWORD) for coef in coefs_arg])
    func.__signature__ = signature(func).replace(parameters=params)
    return func


x = np.array([[1., 4.6, 1., 3.],
              [1., 4.6, 2., 3.],
              [2., 4., 3., 1.],
              [2., 4., 3., 2.],
              [1., 4., 4., 1.],
              [2., 4., 4., 2.],
              [2., 53., 2., 3.],
              [1., 228., 1., 5.],
              [2., 93., 1., 2.],
              [2., 59., 3., 2.]])

y = np.array([-1, -1, 1, 1, 1, 1, -1, -1, -1, -1])

gg = adapter(['c_0', 'c_1', 'c_2', 'c_3', 'c_4'])


gmodel = Model(gg)
params = Parameters()
params.add_many(('c_0', 1, True, None, None, None, None), ('c_1', 1, True, None, None, None, None),
                ('c_2', 1, True, None, None, None, None), ('c_3', 1, True, None, None, None, None),
                ('c_4', 1, True, None, None, None, None))

result = gmodel.fit(y.flatten(), params, x=x.flatten())

print(signature(gg))
