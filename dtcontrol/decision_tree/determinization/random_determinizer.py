import numpy as np

from dtcontrol.decision_tree.determinization.determinizer import Determinizer

class RandomDeterminizer(Determinizer):
    """
    This determinizer determinizes randomly.
    """

    def __init__(self, pre_determinize=True):
        super().__init__()
        self.pre_determinize = pre_determinize

    def determinize(self, dataset):
        if self.is_pre():
            assert self.pre_determinized_labels is not None
            return self.pre_determinized_labels
        return self.choose_random_labels(dataset.get_single_labels())

    @staticmethod
    def choose_random_labels(y):
        return np.apply_along_axis(lambda x: np.random.choice(x[x != -1]), axis=1, arr=y)

    def is_pre(self):
        return self.pre_determinize
