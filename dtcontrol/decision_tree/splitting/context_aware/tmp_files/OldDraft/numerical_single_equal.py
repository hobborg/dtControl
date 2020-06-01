from dtcontrol.decision_tree.splitting.split import Split
from dtcontrol.decision_tree.splitting.splitting_strategy import SplittingStrategy


class CategoricalSingleEqualSplittingStrategy(SplittingStrategy):
    def find_split(self, dataset, impurity_measure):
        """
        :param dataset: the subset of data at the current split
        :param y: the determinized labels
        :param impurity_measure: the impurity measure to determine the quality of a potential split
        :returns: a split object
        """
        x_numeric = dataset.get_numeric_x()         # .get_numeric_x: converts all values inside dataset to type float
        splits = {}                                 # dict containing all splits. key names = Split Object e.g. x1 <= 160.5  values = impurity_measure

        # interates over 0...m  (m: columns)
        for feature in range(x_numeric.shape[1]):
            # all possible values of a feature sorted
            values = sorted(set(x_numeric[:, feature]))
            for i in range(len(values) - 1):
                real_feature = dataset.map_numeric_feature_back(feature)
                split = CategoricalSingleEqualSplit(real_feature,values[i])
                # Key:Splitobject   Value:Impurity of the split
                splits[split] = impurity_measure.calculate_impurity(dataset,split)
        if not splits:
            return None
        return min(splits.keys(), key=splits.get)

        # The min function goes over all keys, k, in the dictionary and takes the one that has minimum value after applying splits.get method.
        # The get() method returns the value specified for key, k, in the dictionary.



class CategoricalSingleEqualSplit(Split):
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

    def print_dot(self, variables=None, category_names=None):
        if variables:
            var = variables[self.feature]
        else:
            var = f'x[{self.feature}]'
        if category_names and self.feature in category_names:
            val = category_names[self.feature][self.value]
        else:
            val = self.value
        return f'{var} == {val}'

    def print_c(self):
        return f'x[{self.feature}] == {self.value}'

    def print_vhdl(self):
        return f'x{self.feature}] == {self.value}'
