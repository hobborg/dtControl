import numpy as np
from scipy.optimize import curve_fit
from scipy.optimize import OptimizeWarning
import warnings


x = np.array([[1., 4.6, 1., 3.],
              [1., 4.6, 2., 3.],
              [2., 53., 2., 3.],
              [1., 228., 1., 5.],
              [2., 93., 1., 2.]])
y = np.array([-1, -1, -1, -1, 1])


# Calc Function
def func(x, c_0, c_1, c_2, c_3, c_4):
    result = []
    for row in range(x.shape[0]):
        term = c_0 * x[row, 0] + c_1 * x[row, 1] + c_2 * x[row, 2] + c_3 * x[row, 3] - c_4
        result.append(term)

    print(result)
    for index in range(len(result)):
        if not ((result[index] <= 0 and y[index] <= 0) or (result[index] > 0 and y[index] > 0)):
            return np.array(result)
    return np.array(result)

# Run 1: Determining more suitable y
with warnings.catch_warnings():
    warnings.filterwarnings("ignore")
    try:
        calculated_coefs, cov = curve_fit(func, x, y)
    except Exception:
        pass

print(calculated_coefs)


