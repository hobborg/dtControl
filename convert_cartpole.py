import numpy as np
import pandas as pd

filename = '../XYdatasets/cartpole'

data = np.genfromtxt(f'{filename}.scots', delimiter=',')
data = data[1:]  # remove column names
# nondeterministic = len(data) - len(np.unique(data[:,:first_y_index], axis=1)) > 0  # only true for cartpole up to now

labels = np.unique(data[:,2])
label_mapping = dict()
for i in range(len(labels)):
    label_mapping[labels[i]] = i

same_points_indices = [0]
i = 0
while i < len(data):
    j = i
    while j < len(data) - 1 and (data[j,:2] == data[j+1,:2]).all():
        j += 1
    same_points_indices.append(j + 1)
    i = j + 1

new_data = []
new_labels = []
for i in range(len(same_points_indices) - 1):
    new_data.append(data[same_points_indices[i],:2])
    label_indices = [label_mapping[l] for l in data[same_points_indices[i]:same_points_indices[i+1],2]]
    label = np.array([0] * len(labels))
    label[label_indices] = 1
    new_labels.append(label)

data_frame = pd.DataFrame(np.array(new_data), columns=['x1','x2'])
data_frame.to_pickle(f'{filename}_X.pickle')

np.save(f'{filename}_Y.npy', np.array(new_labels))