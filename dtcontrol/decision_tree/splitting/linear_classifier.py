import numpy as np

from dtcontrol.decision_tree.splitting.linear_split import LinearSplit
from dtcontrol.decision_tree.splitting.splitting_strategy import SplittingStrategy

class LinearClassifierSplittingStrategy(SplittingStrategy):
    def __init__(self, classifier_class, keep_categorical=False, **kwargs):  # TODO MJA: implement one hot encoding
        self.classifier_class = classifier_class
        self.keep_categorical = keep_categorical
        self.kwargs = kwargs

    def find_split(self, dataset, y, impurity_measure):
        x_numeric = dataset.get_numeric_x()
        if len(x_numeric) == 0:
            return None

        label_to_impurity = {}
        label_to_classifier = {}
        for label in np.unique(y):
            new_y = np.copy(y)
            label_mask = (new_y == label)
            new_y[label_mask] = 1
            new_y[~label_mask] = -1
            classifier = self.classifier_class(**self.kwargs)
            classifier.fit(x_numeric, new_y)
            label_to_classifier[label] = classifier
            features = LinearSplit.map_numeric_coefficients_back(classifier.coef_[0], dataset)
            impurity = impurity_measure.calculate_impurity(dataset, y, LinearClassifierSplit(classifier, features))
            label_to_impurity[label] = impurity

        label = min(label_to_impurity.items(), key=lambda x: x[1])[0]
        classifier = label_to_classifier[label]
        return LinearClassifierSplit(classifier)

class LinearClassifierSplit(LinearSplit):
    def __init__(self, classifier, features):
        super().__init__(features, classifier.intercept_[0])
        self.classifier = classifier

    def get_masks(self, dataset):
        mask = self.classifier.predict(dataset.get_numeric_x()) == -1
        return [mask, ~mask]

    def predict(self, features):
        return 0 if self.classifier.predict(features)[0] == -1 else 1
