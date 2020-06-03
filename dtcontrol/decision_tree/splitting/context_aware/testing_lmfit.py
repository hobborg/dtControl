import numpy as np
from lmfit import Model

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

# Calc Function
def func(x, c_0, c_1, c_2, c_3, c_4):
    result = []
    for row in range(x.shape[0]):
        term = c_0 * x[row, 0] + c_1 * x[row, 1] + c_2 * x[row, 2] + c_3 * x[row, 3] - c_4
        result.append(term)
    return np.array(result).flatten()

model = Model(func)
params = model.make_params(c_0=1, c_1=1, c_2=1, c_3=1, c_4=1)
result = model.fit(params,y,x=x )
print(result.fit_report())
