from src.classifiers.splitting.split import Split
from src.classifiers.splitting.splitting_strategy import SplittingStrategy

class CartSplittingStrategy(SplittingStrategy):
    def find_split(self, x, y, impurity_measure):
        splits = {}
        for feature in range(x.shape[1]):
            values = sorted(set(x[:, feature]))
            for i in range(len(values) - 1):
                threshold = (values[i] + values[i + 1]) / 2
                mask = x[:, feature] <= threshold
                splits[(feature, threshold)] = impurity_measure.calculate_impurity(y, mask)

        feature, threshold = min(splits.keys(), key=splits.get)
        mask = x[:, feature] <= threshold
        return mask, CartSplit(feature, threshold)

class CartSplit(Split):
    def __init__(self, feature, threshold):
        self.feature = feature
        self.threshold = threshold

    def predict(self, features):
        return features[:, self.feature][0] <= self.threshold

    def print_dot(self):
        return self.print_c()

    def print_c(self):
        return f'x[{self.feature}] <= {round(self.threshold, 6)}'

    def print_vhdl(self):
        return f'x{self.feature} <= {round(self.threshold, 6)}'
