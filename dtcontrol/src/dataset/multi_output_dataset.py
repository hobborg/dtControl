import numpy as np

from src.dataset.dataset import Dataset
from src.util import make_set

class MultiOutputDataset(Dataset):
    def __init__(self, filename):
        super().__init__(filename)
        self.tuple_ids = None
        self.tuple_id_to_tuple = None
        self.tuple_to_tuple_id = None
        self.unique_labels = None
        self.list_id_to_list = None  # maps ids of lists of tuple ids to the actual lists of tuple ids
        # the data in a tuple (zipped) format where the outermost dimension becomes the innermost dimension
        # i.e. the new dimensions are: num_examples x num_labels x num_outputs
        self.tuples = None

    def compute_accuracy(self, y_pred):
        self.check_loaded()
        num_correct = 0
        for i in range(len(y_pred)):
            pred = y_pred[i]
            if pred is None:
                return None
            correct_tuples = set([tuple(l) for l in self.get_tuples()[i] if l[0] != -1])
            if set.issubset(make_set(pred), correct_tuples):
                num_correct += 1
        return num_correct / len(y_pred)

    """
        [[[ 0, -1, -1],
          [ 0, -1, -1],
          [ 0, -1, -1],
          [ 1,  2,  0]],
    
         [[ 0, -1, -1],
          [ 0, -1, -1],
          [ 0, -1, -1],
          [ 0,  0,  0]]]

        gets mapped to
        
        [[[ 0  0]
          [-1 -1]
          [-1 -1]]
        
         [[ 0  0]
          [-1 -1]
          [-1 -1]]
        
         [[ 0  0]
          [-1 -1]
          [-1 -1]]
        
         [[ 1  0]
          [ 2  0]
          [ 0  0]]]
    """

    def get_tuples(self):
        if self.tuples is None:
            self.tuples = np.stack(self.Y_train, axis=2)
        return self.tuples

    """
    [[[ 0  0]
      [-1 -1]
      [-1 -1]]
        
     [[ 0  0]
      [-1 -1]
      [-1 -1]]
        
     [[ 0  0]
      [-1 -1]
      [-1 -1]]
        
     [[ 1  0]
      [ 2  0]
      [ 0  0]]]
    
     gets mapped to
        
     [[2 -1 -1]
      [2 -1 -1]
      [2 -1 -1]
      [3  4  2]]
    """

    def get_tuple_ids(self):
        if self.tuple_ids is not None:
            return self.tuple_ids

        stacked_y_train = self.get_tuples()

        # default
        tuple_to_index = {tuple(-1 for i in range(stacked_y_train.shape[2])): -1}

        self.tuple_ids = np.full((stacked_y_train.shape[0], stacked_y_train.shape[1]), -1)

        # first axis: datapoints
        # second axis: non-det
        # third axis: control inputs
        i = 0
        for datapoint in stacked_y_train:
            j = 0
            for action in datapoint:
                action_tuple = tuple(action)
                if action_tuple not in tuple_to_index.keys():
                    # indexing from 1
                    tuple_to_index[action_tuple] = len(tuple_to_index) + 1
                self.tuple_ids[i][j] = tuple_to_index[action_tuple]
                j += 1
            i += 1

        self.tuple_to_tuple_id = tuple_to_index
        self.tuple_id_to_tuple = {y: x for (x, y) in tuple_to_index.items()}
        return self.tuple_ids

    def get_tuple_to_tuple_id(self):
        if self.tuple_to_tuple_id is None:
            self.get_unique_labels()
        return self.tuple_to_tuple_id

    def get_unique_labels(self):
        if self.unique_labels is None:
            self.unique_labels, self.list_id_to_list = self.get_unique_labels_from_2d(self.get_tuple_ids())
        return self.unique_labels

    def map_unique_label_back(self, label):
        l = self.list_id_to_list[label]
        return [self.tuple_id_to_tuple[i] for i in l if i != -1]

    def from_mask(self, mask):
        subset = MultiOutputDataset(self.filename)
        subset.copy_from_other_dataset(self)
        subset.X_train = self.X_train[mask]
        subset.Y_train = self.Y_train[:, mask, :]
        if self.tuple_ids:
            subset.tuple_ids = self.tuple_ids[mask]
            subset.tuple_id_to_tuple = self.tuple_id_to_tuple
            subset.tuple_to_tuple_id = self.tuple_to_tuple_id
        if self.unique_labels:
            subset.unique_labels = self.unique_labels[mask]
            subset.list_id_to_list = self.list_id_to_list
        if self.tuples:
            subset.tuples = self.tuples[mask]
