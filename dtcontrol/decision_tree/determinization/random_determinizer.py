import numpy as np

from dtcontrol.dataset.single_output_dataset import SingleOutputDataset
from dtcontrol.decision_tree.determinization.determinizer import Determinizer

class RandomDeterminizer(Determinizer):
    """
    This determinizer determinizes randomly.
    """

    def determinize(self, dataset):
        if self.pre_determinized_labels is not None:
            return self.pre_determinized_labels
        if isinstance(dataset, SingleOutputDataset):
            return self.choose_random_labels(dataset.y)
        else:
            return self.choose_random_labels(dataset.get_tuple_ids())

    @staticmethod
    def choose_random_labels(y):
        return np.apply_along_axis(lambda x: np.random.choice(x[x != -1]), axis=1, arr=y)
