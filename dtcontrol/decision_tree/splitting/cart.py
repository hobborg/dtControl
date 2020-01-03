from dtcontrol.decision_tree.splitting.split import AxisAlignedSplit
from dtcontrol.decision_tree.splitting.splitting_strategy import SplittingStrategy

class CartSplittingStrategy(SplittingStrategy):
    def find_split(self, x, y, impurity_measure):
        splits = {}
        for feature in range(x.shape[1]):
            values = sorted(set(x[:, feature]))
            for i in range(len(values) - 1):
                threshold = (values[i] + values[i + 1]) / 2
                mask = x[:, feature] <= threshold
                splits[(feature, threshold)] = impurity_measure.calculate_impurity(x, y, mask)

        feature, threshold = min(splits.keys(), key=splits.get)
        mask = x[:, feature] <= threshold
        return mask, AxisAlignedSplit(feature, threshold)
