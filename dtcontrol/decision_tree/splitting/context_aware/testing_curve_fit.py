import numpy as np
from scipy.optimize import curve_fit

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
    for index in range(len(result)):
        if not ((result[index] <= 0 and y[index] <= 0) or (result[index] > 0 and y[index] > 0)):
            print(result)
            return np.array(result)
    print(result)
    return np.array(result)


c, cov = curve_fit(func, x, y)


