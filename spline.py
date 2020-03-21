import matplotlib
from matplotlib import pyplot as plt
import numpy as np
from numpy.random import rand

matplotlib.use('TkAgg')

x = range(1, 6)
num_plots = 9
_, axes = plt.subplots(num_plots, 2, sharey='row')

def plot(y, i):
    scaled = [1 + np.e * np.log(2) * p * np.log2(p) for p in y]
    axes[i, 0].bar(x, y)
    axes[i, 1].bar(x, scaled)


for i in range(5):
    y = np.array([rand(), rand(), rand(), rand(), rand()])
    plot(y, i)

plot(np.array([.1, .1, .9, .1, .1]), 5)
plot(np.array([.01, .01, .99, .01, .01]), 6)
plot(np.array([1, 1, 1, 1, 1]), 7)
plot(np.array([.2, .2, .2, .2, .2]), 8)
plt.show()
