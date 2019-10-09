from sklearn.tree import DecisionTreeClassifier

from classifiers.custom_decision_tree import CustomDecisionTree, Node

class CartCustomDecisionTree(CustomDecisionTree):
    def __init__(self):
        super().__init__()
        self.name = 'CART'

    def is_applicable(self, dataset):
        return True

    def fit(self, dataset):
        self.root = CartCustomNode()
        self.root.fit(dataset.X_train, dataset.get_unique_labels())
        self.set_labels(lambda leaf: dataset.map_unique_label_back(leaf.trained_label), dataset.index_to_value)

    def __str__(self):
        return 'CART'

class CartCustomNode(Node):
    def __init__(self, depth=0):
        super().__init__(depth)
        self.dt = None

    def test_condition(self, x):
        tree = self.dt.tree_
        return x[:, tree.feature[0]][0] <= tree.threshold[0]

    def create_child_node(self):
        return CartCustomNode(self.depth + 1)

    def find_split(self, X, y):
        self.dt = DecisionTreeClassifier(max_depth=1, criterion='entropy')
        self.dt.fit(X, y)
        mask = X[:, self.dt.tree_.feature[0]] <= self.dt.tree_.threshold[0]
        return mask

    def get_dot_label(self):
        if self.actual_label:
            return self.actual_label
        tree = self.dt.tree_
        return f'X[{tree.feature[0]}] <= {round(tree.threshold[0], 4)}'

    def get_c_label(self):
        if self.actual_label:
            return f'return {self.actual_label};'
        tree = self.dt.tree_
        return f'X[{tree.feature[0]}] <= {round(tree.threshold[0], 4)}'

    def print_dot_red(self):
        return False
