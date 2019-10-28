import dtcontrol.util
from sklearn.tree import DecisionTreeClassifier
from dtcontrol.classifiers.custom_dt import CustomDT, Node

class CartDT(CustomDT):
    def __init__(self):
        super().__init__()
        self.name = 'CART'

    def is_applicable(self, dataset):
        return True

    def fit(self, dataset):
        self.root = CartNode()
        self.root.fit(dataset.X_train, dataset.get_unique_labels())
        self.set_labels(lambda leaf: dataset.map_unique_label_back(leaf.trained_label), dataset.index_to_value)

class CartNode(Node):
    def __init__(self, depth=0):
        super().__init__(depth)
        self.dt = None

    def test_condition(self, x):
        tree = self.dt.tree_
        return x[:, tree.feature[0]][0] <= tree.threshold[0]

    def create_child_node(self):
        return CartNode(self.depth + 1)

    def find_split(self, X, y):
        self.dt = DecisionTreeClassifier(max_depth=1, criterion='entropy')
        self.dt.fit(X, y)
        mask = X[:, self.dt.tree_.feature[0]] <= self.dt.tree_.threshold[0]
        return mask

    def get_dot_label(self):
        if self.actual_label is not None:
            rounded = dtcontrol.util.objround(self.actual_label, 6)  # TODO get precision from flag?
            return dtcontrol.util.split_into_lines(rounded)
        tree = self.dt.tree_
        return f'X[{tree.feature[0]}] <= {round(tree.threshold[0], 6)}'  # TODO get precision from flag?

    def print_dot_red(self):
        return False
        
    def is_axis_aligned(self):
        return True
