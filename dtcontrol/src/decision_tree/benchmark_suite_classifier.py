from abc import ABC, abstractmethod

class BenchmarkSuiteClassifier(ABC):
    @abstractmethod
    def get_name(self):
        pass

    @abstractmethod
    def is_applicable(self, dataset):
        pass

    @abstractmethod
    def fit(self, dataset):
        """
        Trains the classifier on the given dataset and keeps the resulting decision tree in memory.
        """
        pass

    @abstractmethod
    def predict(self, dataset, actual_values=True):
        """
        Classifies a dataset.
        :param dataset: the dataset to classify
        :param actual_values: if True, the actual float values are predicted. if False, the index labels are predicted.
        :return: a list of the predicted labels.
        """
        pass

    @abstractmethod
    def get_stats(self):
        """
        Returns a dictionary of statistics to be saved and displayed (e.g. the number of nodes in the tree).
        """
        pass

    @abstractmethod
    def save(self, file):
        """
        Saves the classifier to a file (for debugging purposes).
        """
        pass

    @abstractmethod
    def print_dot(self):
        """
        Prints the classifier in the dot (graphviz) format.
        """
        pass

    @abstractmethod
    def print_c(self):
        """
        Prints the classifier as nested if-else statements in the C syntax.
        """
        pass
