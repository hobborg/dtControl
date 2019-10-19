import numpy as np

from classifiers.cart_custom_dt import CartDT, CartNode
from dataset.single_output_dataset import SingleOutputDataset

class NormSingleOutputDT(CartDT):
    """
    :param comp: The comparison function to be used (either max or min)
    """

    def __init__(self, comp):
        super().__init__()
        self.name = f'{"Max" if comp == max else "Min"}Norm-SingleOutputDT'
        self.comp = comp

    def is_applicable(self, dataset):
        return isinstance(dataset, SingleOutputDataset) and not dataset.is_deterministic

    def fit(self, dataset):
        self.root = CartNode()
        self.root.fit(dataset.X_train, self.determinize(dataset))
        self.set_labels(lambda leaf: leaf.trained_label, dataset.index_to_value)

    def determinize(self, dataset):
        return np.apply_along_axis(lambda x: self.comp(x[x != -1], key=lambda i: dataset.index_to_value[i] ** 2),
                                   axis=1,
                                   arr=dataset.Y_train)
