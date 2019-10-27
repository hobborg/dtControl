from dtcontrol.classifiers.cart_custom_dt import CartDT, CartNode
from dtcontrol.dataset.dataset import Dataset
from dtcontrol.dataset.single_output_dataset import SingleOutputDataset

class MaxFreqDT(CartDT):
    def __init__(self, ):
        super().__init__()
        self.name = 'MaxFreqDT'

    def is_applicable(self, dataset):
        return not dataset.is_deterministic

    def fit(self, dataset):
        self.root = MaxFreqNode()
        if isinstance(dataset, SingleOutputDataset):
            self.root.fit(dataset.X_train, dataset.Y_train)
            self.set_labels(lambda leaf: leaf.trained_label, dataset.index_to_value)
        else:
            self.root.fit(dataset.X_train, dataset.get_tuple_ids())
            self.set_labels(lambda leaf: dataset.map_tuple_id_back(leaf.trained_label), dataset.index_to_value)

class MaxFreqNode(CartNode):
    def __init__(self, depth=0):
        super().__init__(depth)

    def create_child_node(self):
        return MaxFreqNode(self.depth + 1)

    def find_split(self, X, y):
        return super().find_split(X, Dataset._get_max_labels(y))

    def check_done(self, X, y):
        return super().check_done(X, Dataset._get_max_labels(y))
