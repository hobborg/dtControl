import numpy as np

from dataset.dataset import Dataset


class MultiOutputDataset(Dataset):
    def __init__(self, filename):
        super().__init__(filename)
        self.tuple_labels = None
        self.index_to_tuple = None
        self.unique_labels = None
        self.unique_mapping = None

    def compute_accuracy(self, y_pred):  # TODO: double-check that this works
        self.check_loaded()
        if len(y_pred[y_pred is None]) != 0:
            return None
        tuple_labels = self.get_tuple_labels()
        num_correct = 0
        for i in range(len(y_pred)):
            pred = y_pred[i]
            if set.issubset(set(pred), set(tuple_labels[i])):
                num_correct += 1
        return num_correct / len(y_pred)

    '''
        array([[[ 0, -1, -1],
            [ 0, -1, -1],
            [ 0, -1, -1],
            [ 1,  2,  0]],
    
           [[ 0, -1, -1],
            [ 0, -1, -1],
            [ 0, -1, -1],
            [ 0,  0,  0]]])

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
    
        gets mapped to
        
        [[2 0 0]
         [2 0 0]
         [2 0 0]
         [3 4 2]]
    '''
    def get_tuple_labels(self):
        if self.tuple_labels is not None:
            return self.tuple_labels

        stacked_y_train = np.stack(self.Y_train, axis=2)

        # default
        tuple_to_index = {(-1, -1): 0}

        self.tuple_labels = np.full((stacked_y_train.shape[0], stacked_y_train.shape[1]), 0)

        # first axis: datapoints
        # second axis: non-det
        # third axis: control inputs
        i = 0
        for datapoint in stacked_y_train:
            j = 0
            for action in datapoint:
                sorted_action_tuple = tuple(sorted(action))
                if sorted_action_tuple not in tuple_to_index.keys():
                    # indexing from 1
                    tuple_to_index[sorted_action_tuple] = len(tuple_to_index) + 1
                self.tuple_labels[i][j] = tuple_to_index[sorted_action_tuple]
                j = j + 1
            i = i + 1

        self.index_to_tuple = {y: x for (x, y) in tuple_to_index.items()}
        return self.tuple_labels

    def map_tuple_label_back(self, label):
        pass

    '''
    eg. 
    [[2 0 0]
     [2 0 0]
     [2 0 0]
     [3 4 2]]
    
    unique_labels = [1, 2, 3]
    unique_mapping = {1: [1 2 3 -1 -1], 2: [1 -1 -1 -1], 3: [1 2 0 0 0]}
    '''
    def get_unique_labels(self):
        if self.unique_labels is None:
            self.unique_labels, self.unique_mapping = self._get_unique_labels(self.get_tuple_labels())
        return self.unique_labels

    def map_unique_label_back(self, label):
        return self.unique_mapping[label]
