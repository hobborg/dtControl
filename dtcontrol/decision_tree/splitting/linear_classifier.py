import numpy as np

from dtcontrol.decision_tree.determinization.non_determinizer import NonDeterminizer
from dtcontrol.decision_tree.splitting.linear_split import LinearSplit
from dtcontrol.decision_tree.splitting.splitting_strategy import SplittingStrategy

class LinearClassifierSplittingStrategy(SplittingStrategy):
    def __init__(self, classifier_class, determinizer=NonDeterminizer(), **kwargs):
        self.determinizer = determinizer
        self.classifier_class = classifier_class
        self.kwargs = kwargs

    def find_split(self, dataset, impurity_measure):
        x_numeric = dataset.get_numeric_x()
        if x_numeric.shape[1] == 0:
            return None

        y = self.determinizer.determinize(dataset)
        splits = {}
        for label in np.unique(y):
            new_y = np.copy(y)
            label_mask = (new_y == label)
            new_y[label_mask] = 1
            new_y[~label_mask] = -1
            classifier = self.classifier_class(**self.kwargs)
            classifier.fit(x_numeric, new_y)
            real_features = LinearSplit.map_numeric_coefficients_back(classifier.coef_[0], dataset)
            split = LinearClassifierSplit(classifier, real_features, dataset.numeric_columns)
            splits[split] = impurity_measure.calculate_impurity(dataset, y, split)

        return min(splits.keys(), key=splits.get)

class LinearClassifierSplit(LinearSplit):
    def __init__(self, classifier, real_coefficients, numeric_columns):
        super().__init__(classifier.coef_[0], classifier.intercept_[0], real_coefficients, numeric_columns)
        self.classifier = classifier
        self.numeric_columns = numeric_columns

    def get_masks(self, dataset):
        mask = self.classifier.predict(dataset.get_numeric_x()) == -1
        return [mask, ~mask]

    def predict(self, features):
        return 0 if self.classifier.predict(features[:, self.numeric_columns])[0] == -1 else 1
