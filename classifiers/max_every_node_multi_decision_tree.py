from dataset.multi_output_dataset import MultiOutputDataset
from classifiers.cart_custom_decision_tree import CartCustomDecisionTree, CartCustomNode


class MaxEveryNodeMultiDecisionTree(CartCustomDecisionTree):
    def __init__(self,):
        super().__init__()
        self.name = 'MaxEveryNodeMultiDT'

    def is_applicable(self, dataset):
        return isinstance(dataset, MultiOutputDataset)

    def fit(self, dataset):
        self.root = MaxMultiNode()
        self.root.fit(dataset.X_train, dataset.Y_train)
        self.set_labels(lambda leaf: leaf.trained_label, dataset.index_to_value)

    def __str__(self):
        return 'MaxEveryNodeMultiDecisionTree'


class MaxMultiNode(CartCustomNode):
    def __init__(self, depth=0):
        super().__init__(depth)

    def create_child_node(self):
        return MaxMultiNode(self.depth + 1)

    def find_split(self, X, y):
        return super().find_split(X, self.get_tuple_label(self._determinize_max_over_all_inputs(y)))

    def check_done(self, y):
        return super().check_done(MultiOutputDataset.get_max_labels(y))