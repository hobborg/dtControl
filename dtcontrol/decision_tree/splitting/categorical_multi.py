from dtcontrol.decision_tree.splitting.split import Split
from dtcontrol.decision_tree.splitting.splitting_strategy import SplittingStrategy

class CategoricalMultiSplittingStrategy(SplittingStrategy):
    def __init__(self, value_grouping=False):
        self.value_grouping = value_grouping

    def find_split(self, dataset, y, impurity_measure):
        x_categorical = dataset.get_categorical_x()
        splits = {}
        for feature in range(x_categorical.shape[1]):
            real_feature = dataset.map_categorical_feature_back(feature)
            split = CategoricalMultiSplit(real_feature)
            impurity = impurity_measure.calculate_impurity(dataset, y, split)
            splits[split] = impurity

            if self.value_grouping:
                values = sorted(set(x_categorical[:, feature]))
                for i in range(len(values)):
                    for j in range(i, len(values)):
                        pass  # merge, compute new impurity and iterate until we don't find any improvement

        if not splits:
            return None
        return min(splits.keys(), key=splits.get)

class CategoricalMultiSplit(Split):
    def __init__(self, feature, value_groups=None):
        self.feature = feature
        self.value_groups = value_groups
        if not self.value_groups:
            self.value_groups = []

    def predict(self, features):
        v = features[:, self.feature][0]
        for i in range(len(self.value_groups)):
            if v in self.value_groups[i]:
                return i
        assert False

    def get_masks(self, dataset):
        if not self.value_groups:
            self.value_groups = [[v] for v in sorted(set(dataset.x[:, self.feature]))]
        return [sum(dataset.x[:, self.feature] == group[i] for i in range(len(group))) for group in self.value_groups]

    def print_dot(self, variables=None, category_names=None):
        if variables:
            return variables[self.feature]
        return f'x[{self.feature}]'

    def print_c(self):
        return f'x[{self.feature}]'

    def print_vhdl(self):
        return f'x{self.feature}]'
