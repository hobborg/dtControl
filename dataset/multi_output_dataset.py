import numpy as np
from operator import itemgetter
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
    def get_tuple_labels(self, y):
        if self.tuple_labels is not None:
            return self.tuple_labels

        stacked_y_train = np.stack(y, axis=2)

        # default
        tuple_to_index = {(-1, -1): -1}

        self.tuple_labels = np.full((stacked_y_train.shape[0], stacked_y_train.shape[1]), -1)

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

    '''
    A list mapping tuple ids to list (float_id, float_id) tuples
    eg. {-1: (-1, -1), 2: (1, 3), 3: (2, 4)}
    '''
    def map_tuple_label_back(self, label):
        return self.index_to_tuple[label]

    '''
    eg. 
    [[2 0 0]
     [2 0 0]
     [2 0 0]
     [3 4 2]]
    
    unique_labels = [1, 2, 3, 4]
    unique_mapping = {1: [(1, 3), (-1, -1), (-1, -1)], 
                      2: [(1, 3), (-1, -1), (-1, -1)], 
                      3: [(1, 3), (-1, -1), (-1, -1)], 
                      4: [(3, 3), ( 3,  6), ( 1,  3)]}
    '''
    def get_unique_labels(self):
        if self.unique_labels is None:
            self.unique_labels, nondetid_to_list = self._get_unique_labels(self.get_tuple_labels(self.y_train))
            self.unique_mapping = {l: [self.map_tuple_label_back(i) for i in nondetid_to_list[l]] for l in self.unique_labels}
        return self.unique_labels

    def map_unique_label_back(self, label):
        return self.unique_mapping[label]


    '''
    Generate a list of tuples (ctrl_idx, inp_enc, freq)
    where ctrl_idx is the control input index, inp_enc is the control input integer encoding and
    freq is the number of times the respective control input has occurred as the ctrl_idx'th component
    '''

    def _get_ranks(self, y):
        ranks = []
        for ctrl_idx in range(y.shape[0]):
            flattended_control = y[ctrl_idx].flatten()
            flattended_control = flattended_control[flattended_control != -1]
            counter = list(zip(range(len(np.bincount(flattended_control))), np.bincount(flattended_control)))
            idx_input_count = [(ctrl_idx,) + l for l in counter]
            ranks.extend(idx_input_count)
        return sorted(ranks, key=itemgetter(2), reverse=True)

    '''
    Given a y_train such as
    array([[[ 1,  2,  3],
            [ 1,  2,  1],
            [ 1,  2,  2],
            [ 3,  3, -1]],

           [[ 3,  4,  5],
            [ 3,  4,  4],
            [ 2,  6,  1],
            [ 3,  6, -1]]])

    gets determinized to

    array([[[ 1, -1, -1],
            [ 1, -1, -1],
            [ 1, -1, -1],
            [ 3, -1, -1]],

           [[ 3, -1, -1],
            [ 3, -1, -1],
            [ 2, -1, -1],
            [ 3, -1, -1]]])
            
    which is reduced to 
    
    array([[[1],
            [1],
            [1],
            [3]],
    
           [[3],
            [3],
            [2],
            [3]]])
    '''
    def determinize_max_over_all_inputs(self, y_original):
        y = np.copy(y_original)
        determinized = False

        # list of tuples (ctrl_input_idx, input_encoding) which were already considered for keeping
        already_considered = set()

        while not determinized:
            ranks = self._get_ranks(y)

            # find the ctrl_idx and inp_enc which should be used in the next round of pruning
            # i.e. the first one from the ranking list whose input has not been already considered
            ctrl_idx = None
            inp_enc = None
            for (ctr, inp, _) in ranks:
                if inp not in already_considered:
                    already_considered.add(inp)
                    ctrl_idx = ctr
                    inp_enc = inp
                    break

            # Go through y[ctrl_idx] row by row
            # for each row, if it contains input_encoding, then change the remaining into -1
            # make the same -1 changes for rest of the control inputs
            for i in range(y.shape[1]):
                row = y[ctrl_idx, i]
                if inp_enc in row:
                    for j in range(y.shape[2]):
                        if row[j] != inp_enc:
                            y[:, i, j] = -1

            # check if all rows contain only one element
            determinized = True
            for ctrl_idx in range(y.shape[0]):
                for i in range(y.shape[1]):
                    row = y[ctrl_idx, i]
                    valid_row = row[row != -1]
                    determinized = determinized & (valid_row.size == 1)
        valid_y = np.array([np.array([yyy[yyy!=-1] for yyy in yy]) for yy in y])
        return self.get_unique_labels()

    def map_determinized_labels_back(self, labels):
        return self.map_unique_label_back(labels)
