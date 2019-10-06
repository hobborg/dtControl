from dataset.dataset import Dataset
from dataset.single_output_dataset import SingleOutputDataset
from classifiers.cart_custom_decision_tree import CartCustomDecisionTree, CartCustomNode

class MaxCartDecisionTree(CartCustomDecisionTree):
    def __init__(self,):
        super().__init__()
        self.name = 'MaxEveryNodeDT'

    def is_applicable(self, dataset):
        return isinstance(dataset, SingleOutputDataset)  # TODO: change this and adapt to multi-output?

    def fit(self, dataset):
        self.root = MaxCartNode()
        self.root.fit(dataset.X_train, dataset.Y_train)
        self.set_labels(lambda leaf: leaf.trained_label, dataset.index_to_value)

    def __str__(self):
        return 'MaxEveryNodeDecisionTree'

class MaxCartNode(CartCustomNode):
    def __init__(self, depth=0):
        super().__init__(depth)

    def create_child_node(self):
        return MaxCartNode(self.depth + 1)

    def find_split(self, X, y):
        return super().find_split(X, Dataset._get_max_labels(y))

    def check_done(self, y):
        return super().check_done(Dataset._get_max_labels(y))