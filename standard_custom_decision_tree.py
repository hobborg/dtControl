from sklearn.tree import DecisionTreeClassifier
from custom_decision_tree import CustomDecisionTree, Node

class StandardCustomDecisionTree(CustomDecisionTree):
    def __init__(self):
        super().__init__()
        self.name = 'StandardCustomDT'

    def create_root_node(self):
        return StandardCustomNode()

    def __str__(self):
        return 'StandardCustomDecisionTree'

class StandardCustomNode(Node):
    def __init__(self, depth=0):
        super().__init__(depth)
        self.dt = None

    def test_condition(self, x):
        tree = self.dt.tree_
        return x[:, tree.feature[0]][0] <= tree.threshold[0]

    def create_child_node(self):
        return StandardCustomNode(self.depth + 1)

    def find_split(self, X, y):
        self.dt = DecisionTreeClassifier(max_depth=1, criterion='entropy')
        self.dt.fit(X, y)
        mask = X[:, self.dt.tree_.feature[0]] <= self.dt.tree_.threshold[0]
        return mask

    def get_dot_label(self):
        if self.label:
            return f'Leaf({self.label})'
        tree = self.dt.tree_
        return f'X[{tree.feature[0]}] <= {round(tree.threshold[0], 4)}'

    def get_c_label(self):
        if self.label:
            return f'return {self.label};'
        tree = self.dt.tree_
        return f'X[{tree.feature[0]}] <= {round(tree.threshold[0], 4)}'

    def print_dot_red(self):
        return False
