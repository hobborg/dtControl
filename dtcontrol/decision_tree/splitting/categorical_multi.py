from dtcontrol.decision_tree.splitting.split import Split
from dtcontrol.decision_tree.splitting.splitting_strategy import SplittingStrategy

class CategoricalMultiSplittingStrategy(SplittingStrategy):
    def find_split(self, dataset, y, impurity_measure):
        x_categorical = dataset.get_categorical_x()
        splits = {}
        for feature in range(x_categorical.shape[1]):
            real_feature = dataset.map_categorical_feature_back(feature)
            split = CategoricalMultiSplit(real_feature)
            splits[split] = impurity_measure.calculate_impurity(dataset, y, split)

        if not splits:
            return None
        return min(splits.keys(), key=splits.get)

class CategoricalMultiSplit(Split):
    def __init__(self, feature):
        self.feature = feature
        self.values = []  # the values corresponding to the children

    def predict(self, features):
        v = features[:, self.feature][0]
        return self.values.index(v)

    def get_masks(self, dataset):
        self.values = sorted(set(dataset.x[:, self.feature]))
        return [dataset.x[:, self.feature] == v for v in self.values]

    def print_dot(self, variables=None, category_names=None):
        if variables:
            return variables[self.feature]
        return f'x[{self.feature}]'

    def print_c(self):
        return f'x[{self.feature}]'

    def print_vhdl(self):
        return f'x{self.feature}]'
