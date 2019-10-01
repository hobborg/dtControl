import pandas as pd
import numpy as np
import os
from sklearn.metrics import accuracy_score
from label_format import LabelFormat
from abc import ABC, abstractmethod

class Dataset(ABC):
    def __init__(self, X_file, Y_file):
        self.name = self.get_dataset_name(X_file)
        self.X_file = X_file
        self.Y_file = Y_file
        self.X_train = None
        self.Y_train = None
        self.combination_label_mapping = {}
        self.label_format_to_labels = None

    def load_if_necessary(self):
        if self.X_train is None:
            self.X_train = np.array(pd.read_pickle(self.X_file))
            self.Y_train = np.load(self.Y_file)

    def check_loaded(self):
        if self.X_train is None:
            raise RuntimeError('Dataset is not loaded.')

    @staticmethod
    def get_dataset_name(file):
        return os.path.basename(file).replace('_X.pickle', '')

    """
    Reads {file} and procudes either a Single-OutputDataset
    (X_train, Y_train, mapping_dict, X_vars, action_dict) where 
    X_train is a numpy array of state valuations for each state in the controller
    Y_train a list of lists of action indices
    value_index_mapping maps action values (floats) to action indices - here, always {}
    X_vars contains the names of the columns in X_train
    action_dict is the mapping from action index to action name
    """
    @staticmethod
    def from_uppaal(file):
        # A file exported using UPPAAL's --print-strategies CLI switch

        f = open(file)
        print("Reading from %s" % file)   

        lines = f.readlines()

        # Extract categorical_features
        categorical_features = re.findall('(\w+)\.\w+', lines[1])

        # Extract numeric features
        numeric_features = re.findall('(\w+)=\-?[0-9]+', lines[7])

        # Extract actions
        action_set = set()
        for line in lines:
            if line.startswith('When'):
                action_set.add(line[line.index(' take transition ')+17:].rstrip())
        action_set.add('wait')
        actions = dict(zip(list(action_set), range(0, len(action_set))))

        row_num_vals = []
        row_actions = []

        current_actions = []
        ignore_current = False
        total_rows = 0
        total_state_actions = 0
        for line in lines[7:]:
            if line.startswith("State"):
                numeric_vals = re.findall('\w+=([^\ ]+)', line)
            elif ignore_current:
                continue
            elif line.startswith("When"):
                collect_actions = True
                action_str = line[line.index(' take transition ')+17:].rstrip()
                current_actions.append(actions[action_str])
            elif line.startswith("While"):
                # We implicityly assume that transitions starting with 'While' are mapped to wait.
                current_actions.append(actions['wait'])
            elif line.strip() == "":
                # if not ignore_current:
                row_num_vals.append(numeric_vals)
                row_actions.append(current_actions)
                total_rows += 1
                total_state_actions += len(current_actions)
                current_actions = []
            else:
                raise Exception("ERROR: Unhandled line in input")
                break

        print(f"Done reading {total_rows} states with \na total of {total_state_actions} state-action pairs.")

        # Project onto measurable variables, the strategy should not depend on the gua variables coming from euler
        projection_variables = list(filter(lambda x: 'gua' not in x, numeric_features))
        num_df = pd.DataFrame(row_num_vals, columns=numeric_features, dtype='float32')
        num_df = num_df[projection_variables]

        X_train = np.asarray(num_df)
        Y_train = row_actions

        print("\nConstructed training set with %s datapoints" % X_train.shape[0])

        index_to_action_name = [{y:x} for (x, y) in actions.items()]

        return (X_train, Y_train, {}, projection_variables, index_to_action_name)


    """
    Reads {file} and procudes either a Single- or Multi-Output Dataset
    (X_train, Y_train, mapping_dict, X_vars, Y_dict) where 
    X_train is a numpy array of state valuations for each state in the controller
    Y_train a list of lists (list of actions for each state) if single-output, else 
              list of list of tuples (list of actions tuples for each state) if multi-output
    value_index_mapping contains an entry for each contron input;
                        an entry is a map from values (floats) to indices (grid indices)
    X_vars contains the names of the columns in X_train
    actions is a list of control input names
    """
    def from_scots(file):
        pass

    @abstractmethod
    def is_applicable(self, label_format):
        pass

    def get_labels_for_format(self, label_format):
        self.check_loaded()
        if not self.is_applicable(label_format):
            raise ValueError(f'Dataset is not applicable to {label_format}.')
        return self.label_format_to_labels[label_format]()

    def get_combination_labels(self):
        self.check_loaded()
        l = []
        next_unused_int = 1  # OC1 expects labels starting with 1
        label_to_int = {}
        for i in range(len(self.Y_train)):
            label = ','.join([str(i) for i in self.Y_train[i]])
            if label not in label_to_int:
                label_to_int[label] = next_unused_int
                self.combination_label_mapping[next_unused_int] = self.Y_train[i]
                next_unused_int += 1
            new_label = label_to_int[label]
            l.append(new_label)
        return np.array(l)

    @abstractmethod
    def compute_accuracy(self, Y_pred, label_format):
        pass

class AnyLabelDataset(Dataset):
    def __init__(self, X_file, Y_file):
        super().__init__(X_file, Y_file)
        self.label_format_to_labels = {
            LabelFormat.VECTOR: lambda: self.Y_train,
            LabelFormat.COMBINATIONS: lambda: self.get_combination_labels(),  # lambda to delay computation
            LabelFormat.MAX: lambda: self.get_max_labels(self.Y_train),
            LabelFormat.MAX_EVERY_NODE: lambda: self.Y_train
        }

    def is_applicable(self, label_format):
        return label_format is not LabelFormat.MULTI

    @staticmethod
    def get_max_labels(y):
        label_counts = np.count_nonzero(y, axis=0)
        new_labels = []
        for i in range(len(y)):
            labels = y[i]
            max_label = max([i for i in range(len(labels)) if labels[i] == 1], key=lambda l: label_counts[l])
            new_labels.append(max_label)
        return np.array(new_labels)

    def compute_accuracy(self, Y_pred, label_format):
        self.check_loaded()
        if len(Y_pred[Y_pred == None]) != 0:
            return None
        num_correct = 0
        for i in range(len(Y_pred)):
            if label_format == LabelFormat.VECTOR:
                pred = Y_pred[i]
            elif label_format == LabelFormat.COMBINATIONS:
                pred = self.combination_label_mapping[Y_pred[i]]
            else:
                pred = self.create_one_hot_vector(Y_pred[i], self.Y_train.shape[1])

            predicted_indices = set(np.nonzero(pred)[0])
            correct_indices = set(np.nonzero(self.Y_train[i])[0])
            if set.issubset(predicted_indices, correct_indices):
                num_correct += 1
        return num_correct / len(Y_pred)

    @staticmethod
    def create_one_hot_vector(index, length):
        return np.array([int(tmp == index) for tmp in range(length)])

class MultiOutputDataset(Dataset):
    def __init__(self, X_file, Y_file):
        super().__init__(X_file, Y_file)
        self.multi_label_mapping = {}
        self.label_format_to_labels = {
            LabelFormat.COMBINATIONS: lambda: self.get_combination_labels(),
            LabelFormat.MULTI: lambda: self.get_multi_labels()
        }

    def get_multi_labels(self):
        """
        :return: a numpy array of the labels in integer format
        """
        self.check_loaded()
        l = []
        next_unused_int = 1  # OC1 expects labels starting with 1
        label_to_int = {}
        for i in range(len(self.Y_train)):
            inner = []
            for j in range(self.Y_train.shape[1]):
                label = self.Y_train[i, j]
                if label not in label_to_int:
                    label_to_int[label] = next_unused_int
                    self.multi_label_mapping[next_unused_int] = label
                    next_unused_int += 1
                new_label = label_to_int[label]
                inner.append(new_label)
            l.append(inner)
        return np.array(l)

    def is_applicable(self, label_format):
        return label_format in [LabelFormat.MULTI, LabelFormat.COMBINATIONS]

    def compute_accuracy(self, Y_pred, label_format):
        self.check_loaded()
        if len(Y_pred[Y_pred == None]) != 0:
            return None
        labels = self.get_labels_for_format(label_format)
        if label_format == LabelFormat.COMBINATIONS:
            return accuracy_score(labels, Y_pred)
        return sum(int(np.all(Y_pred[i] == labels[i])) for i in range(len(labels))) / len(labels)
