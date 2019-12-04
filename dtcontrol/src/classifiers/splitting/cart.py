from sklearn.tree import DecisionTreeClassifier

from src.classifiers.splitting.split import Split
from src.classifiers.splitting.splitting_strategy import SplittingStrategy

class Cart(SplittingStrategy):
    def find_split(self, X_train, y, impurity_measure):
        dt = DecisionTreeClassifier(max_depth=1, criterion='entropy')  # TODO: implement myself and use impurity measure
        dt.fit(X_train, y)
        mask = X_train[:, dt.tree_.feature[0]] <= dt.tree_.threshold[0]
        return mask, CartSplit(dt.tree_)

class CartSplit(Split):
    def __init__(self, tree):
        self.tree = tree

    def predict(self, features):
        return features[:, self.tree.feature[0]][0] <= self.tree.threshold[0]

    def print_dot(self):
        return self.print_c()

    def print_c(self):
        return f'X[{self.tree.feature[0]}] <= {round(self.tree.threshold[0], 6)}'

    def print_vhdl(self):
        return f'x{self.tree.feature[0]} <= {round(self.tree.threshold[0], 6)}'
