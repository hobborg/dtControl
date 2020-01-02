import numpy as np

from src.decision_tree.splitting.split import LinearSplit
from src.decision_tree.splitting.splitting_strategy import SplittingStrategy

class LinearClassifierSplittingStrategy(SplittingStrategy):
    def __init__(self, classifier_class, **kwargs):
        self.classifier_class = classifier_class
        self.kwargs = kwargs

    def find_split(self, x, y, impurity_measure):
        label_to_impurity = {}
        label_to_classifier = {}
        for label in np.unique(y):
            new_y = np.copy(y)
            label_mask = (new_y == label)
            new_y[label_mask] = 1
            new_y[~label_mask] = -1
            classifier = self.classifier_class(**self.kwargs)
            classifier.fit(x, new_y)
            label_to_classifier[label] = classifier
            pred = classifier.predict(x)
            impurity = impurity_measure.calculate_impurity(x, y, (pred == -1))
            label_to_impurity[label] = impurity

        label = min(label_to_impurity.items(), key=lambda x: x[1])[0]
        classifier = label_to_classifier[label]
        mask = (classifier.predict(x) == -1)
        return mask, LinearClassifierSplit(classifier)

class LinearClassifierSplit(LinearSplit):
    def __init__(self, classifier):
        super().__init__(classifier.coef_[0], classifier.intercept_[0])
        self.classifier = classifier

    def predict(self, features):
        return self.classifier.predict(features)[0] == -1
