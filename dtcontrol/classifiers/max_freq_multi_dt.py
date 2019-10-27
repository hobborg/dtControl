from dtcontrol.dataset.multi_output_dataset import MultiOutputDataset
from dtcontrol.classifiers.cart_custom_dt import CartDT, CartNode


class MaxFreqMultiDT(CartDT):
    def __init__(self,):
        super().__init__()
        self.name = 'MaxFreqMultiDT'

    def is_applicable(self, dataset):
        return isinstance(dataset, MultiOutputDataset) and not dataset.is_deterministic

    def fit(self, dataset):
        if dataset.tuple_to_tuple_id is None:
            dataset.get_tuple_ids()
        self.root = MaxFreqMultiNode(dataset.tuple_to_tuple_id)
        self.root.fit(dataset.X_train, dataset.Y_train)
        self.set_labels(lambda leaf: dataset.map_tuple_id_back(leaf.trained_label), dataset.index_to_value)


class MaxFreqMultiNode(CartNode):
    def __init__(self, tuple_to_tuple_id, depth=0):
        super().__init__(depth)
        self.tuple_to_tuple_id = tuple_to_tuple_id

    def create_child_node(self):
        return MaxFreqMultiNode(self.tuple_to_tuple_id, self.depth + 1)

    def find_split(self, X, y):
        return super().find_split(X, MultiOutputDataset.determinize_max_over_all_inputs(y, self.tuple_to_tuple_id))

    def check_done(self, X, y):
        return super().check_done(X, MultiOutputDataset.determinize_max_over_all_inputs(y, self.tuple_to_tuple_id))
