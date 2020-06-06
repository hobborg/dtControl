import numpy as np
from lmfit import Model
from lmfit import Parameters, minimize
from lmfit.models import VoigtModel


def func(x, c_0, c_1, c_2, c_3, c_4):
    result = []
    x = x.reshape((10, 4))
    for row in range(x.shape[0]):
        term = c_0 * x[row, 0] + c_1 * x[row, 1] + c_2 * x[row, 2] + c_3 * x[row, 3] - c_4
        result.append(term)
    print(result)
    return np.array(result)


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

gmodel = Model(func)
params = Parameters()
params.add_many(('c_0', 1, True, None, None, None, None), ('c_1', 1, True, None, None, None, None),
                ('c_2', 1, True, None, None, None, None), ('c_3', 1, True, None, None, None, None),
                ('c_4', 1, True, None, None, None, None))

result = gmodel.fit(y.flatten(), params, x=x.flatten(), max_nfev=99999)

print(result.fit_report())
