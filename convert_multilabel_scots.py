import numpy as np
import pandas as pd

filename = '../XYdatasets/aircraft'
first_y_index = 3

data = np.genfromtxt(f'{filename}.scots', delimiter=',')
data = data[1:]  # remove column names
assert len(data) == len(np.unique(data[:, :first_y_index], axis=1))  # should be non-deterministic

X = data[:, :first_y_index]
Y = data[:, first_y_index:]
data_frame = pd.DataFrame(np.array(X), columns=[f'x{i+1}' for i in range(first_y_index)])
data_frame.to_pickle(f'{filename}_X.pickle')
np.save(f'{filename}_Y.npy', np.array(Y))
