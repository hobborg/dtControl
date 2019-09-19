import numpy as np
import pandas as pd

filename = '../XYdatasets/vehicle'

data = np.genfromtxt(f'{filename}.scots', delimiter=',')
data = data[1:]  # remove column names
assert len(data) == len(np.unique(data[:, :3], axis=1))  # vehicle should be non-deterministic

X = data[:, :3]
Y = data[:, 3:]
data_frame = pd.DataFrame(np.array(X), columns=['x1', 'x2', 'x3'])
data_frame.to_pickle(f'{filename}_X.pickle')
np.save(f'{filename}_Y.npy', np.array(Y))
