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
    print(result)
    return np.array(result)


c, cov = curve_fit(func, x, y, [6.076065,-1.827636,6.537475,-7.036291,0.158684])
print(c)
#
# import numpy as np
# from scipy.optimize import curve_fit
#
# def func(X, a, b, c):
#
#     w,x,y,z = X
#
#     return np.log(a) + b*np.log(x) + c*np.log(y)
#
# # some artificially noisy data to fit
# x = np.linspace(0.1,1.1,101)
# y = np.linspace(1.,2., 101)
# a, b, c = 10., 4., 6.
# z = func((x,y), a, b, c) * 1 + np.random.random(101) / 100
#
# # initial guesses for a,b,c:
# p0 = 8., 2., 7.
# print(curve_fit(func, (x,y), z, p0))