from abc import ABC, abstractmethod

class Determinizer(ABC):
    def __init__(self):
        self.dataset = None

    def set_dataset(self, dataset):
        self.dataset = dataset

    @abstractmethod
    def determinize(self, dataset):
        """
        :param dataset: the dataset to be determinized
        :return: the determinized labels
        """
        pass

    @abstractmethod
    def get_index_label(self, label):
        """
        :param label: the determinized label
        :returns: the index (int) label, which can either be a single label, a single tuple, a list of labels,
                  or a list of tuples
        """
        pass

    def get_actual_label(self, label):
        """
        :param label: the determinized label
        :returns: the actual (float) label, which can either be a single label, a single tuple, a list of labels,
                  or a list of tuples
        """
        index_label = self.get_index_label(label)
        if isinstance(index_label, tuple):  # single tuple
            return tuple([self.dataset.index_to_value[i] for i in index_label if i != -1])
        elif isinstance(index_label, list):
            if isinstance(index_label[0], tuple):  # list of tuples
                return [tuple(map(lambda x: self.dataset.index_to_value[x], tup)) for tup in index_label]
            else:  # list of labels
                return [self.dataset.index_to_value[i] for i in index_label if i != -1]
        else:  # single label
            return self.dataset.index_to_value[index_label]

    @abstractmethod
    def is_only_multioutput(self):
        pass
