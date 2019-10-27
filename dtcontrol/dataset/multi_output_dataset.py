import numpy as np
from operator import itemgetter
from dtcontrol.dataset.dataset import Dataset
from dtcontrol.util import make_set


class MultiOutputDataset(Dataset):
    def __init__(self, filename):
        super().__init__(filename)
        self.tuple_ids = None
        self.tuple_id_to_tuple = None
        self.tuple_to_tuple_id = None
        self.unique_labels = None
        self.list_id_to_list = None
        self.zipped = None

    def compute_accuracy(self, y_pred):
        self.check_loaded()
        num_correct = 0
        for i in range(len(y_pred)):
            pred = y_pred[i]
            if pred is None:
                return None
            correct_tuples = set([tuple(l) for l in self.get_zipped()[i] if l[0] != -1])
            if set.issubset(make_set(pred), correct_tuples):
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

    def get_zipped(self):
        if self.zipped is None:
            self.zipped = np.stack(self.Y_train, axis=2)
        return self.zipped

    def get_tuple_ids(self):
        if self.tuple_ids is not None:
            return self.tuple_ids

        stacked_y_train = self.get_zipped()

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
                j = j + 1
            i = i + 1

        self.tuple_to_tuple_id = tuple_to_index
        self.tuple_id_to_tuple = {y: x for (x, y) in tuple_to_index.items()}
        return self.tuple_ids

    '''
    A list mapping tuple ids to list (float_id, float_id) tuples
    eg. {-1: (-1, -1), 2: (1, 3), 3: (2, 4)}
    '''

    def map_tuple_id_back(self, label):
        return self.tuple_id_to_tuple[label]

    def get_unique_labels(self):
        if self.unique_labels is None:
            self.unique_labels, self.list_id_to_list = self._get_unique_labels(self.get_tuple_ids())
        return self.unique_labels

    def map_unique_label_back(self, label):
        l = self.list_id_to_list[label]
        return [self.tuple_id_to_tuple[i] for i in l if i != -1]

    '''
    Generate a list of tuples (ctrl_idx, inp_enc, freq)
    where ctrl_idx is the control input index, inp_enc is the control input integer encoding and
    freq is the number of times the respective control input has occurred as the ctrl_idx'th component
    '''

    @staticmethod
    def _get_ranks(y):
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

    @staticmethod
    def determinize_max_over_all_inputs(y_original, tuple_to_tuple_id):
        y = np.copy(y_original)
        determinized = False

        # list of tuples (ctrl_input_idx, input_encoding) which were already considered for keeping
        already_considered = set()

        while not determinized:
            ranks = MultiOutputDataset._get_ranks(y)

            # find the ctrl_idx and inp_enc which should be used in the next round of pruning
            # i.e. the first one from the ranking list whose input has not been already considered
            ctrl_idx = None
            inp_enc = None
            for (ctr, inp, _) in ranks:
                if (ctr, inp) not in already_considered:
                    already_considered.add((ctr, inp))
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
        valid_y = np.array([np.array([yyy[yyy != -1] for yyy in yy]) for yy in y])
        zipped = np.stack(valid_y, axis=2)
        # [[[1,3], [1,3], [1,2], [3,3]]] -> [1,1,2,3] (tuple ids)
        return np.apply_along_axis(lambda x: tuple_to_tuple_id[tuple(x)], axis=2, arr=zipped).flatten()
