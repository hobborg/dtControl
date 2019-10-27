import numpy as np

from dtcontrol.classifiers.cart_custom_dt import CartDT, CartNode
from dtcontrol.dataset.single_output_dataset import SingleOutputDataset

class RandomDT(CartDT):

    def __init__(self):
        super().__init__()
        self.name = 'RandomDT'

    def is_applicable(self, dataset):
        return not dataset.is_deterministic

    def fit(self, dataset):
        self.root = CartNode()
        if isinstance(dataset, SingleOutputDataset):
            self.root.fit(dataset.X_train, self.determinize(dataset.Y_train))
            self.set_labels(lambda leaf: leaf.trained_label, dataset.index_to_value)
        else:
            self.root.fit(dataset.X_train, self.determinize(dataset.get_tuple_ids()))
            self.set_labels(lambda leaf: dataset.map_tuple_id_back(leaf.trained_label), dataset.index_to_value)

    def determinize(self, y):
        return np.apply_along_axis(lambda x: np.random.choice(x[x != -1]), axis=1, arr=y)
