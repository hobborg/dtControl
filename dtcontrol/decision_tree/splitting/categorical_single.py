from dtcontrol.decision_tree.splitting.split import Split
from dtcontrol.decision_tree.splitting.splitting_strategy import SplittingStrategy

class CategoricalSingleSplittingStrategy(SplittingStrategy):
    def find_split(self, dataset, y, impurity_measure):
        x_categorical = dataset.get_categorical_x()
        splits = {}
        for feature in range(x_categorical.shape[1]):
            real_feature = dataset.map_categorical_feature_back(feature)
            for value in set(x_categorical[:, feature]):
                split = CategoricalSingleSplit(real_feature, value)
                splits[split] = impurity_measure.calculate_impurity(dataset, y, split)

        if not splits:
            return None
        return min(splits.keys(), key=splits.get)

class CategoricalSingleSplit(Split):
    """
    A split of the form feature == value.
    """

    def __init__(self, feature, value):
        self.feature = feature
        self.value = value

    def predict(self, features):
        v = features[:, self.feature][0]
        return 0 if v == self.value else 1

    def get_masks(self, dataset):
        mask = dataset.x[:, self.feature] == self.value
        return [mask, ~mask]

    def print_dot(self, variables=None):
        if variables:
            return f'{variables[self.feature]} == {self.value}'
        return self.print_c()

    def print_c(self):
        return f'x[{self.feature}] == {self.value}'

    def print_vhdl(self):
        return f'x{self.feature}] == {self.value}'
