import numpy as np

from src.classifiers.splitting.split import Split
from src.classifiers.splitting.splitting_strategy import SplittingStrategy

class LinearClassifierSplittingStrategy(SplittingStrategy):
    def __init__(self, classifier_class, **kwargs):
        self.classifier_class = classifier_class
        self.kwargs = kwargs

    def find_split(self, X_train, y, impurity_measure):
        label_to_impurity = {}
        label_to_classifier = {}
        for label in np.unique(y):
            new_y = np.copy(y)
            label_mask = (new_y == label)
            new_y[label_mask] = 1
            new_y[~label_mask] = -1
            classifier = self.classifier_class(**self.kwargs)
            classifier.fit(X_train, new_y)
            label_to_classifier[label] = classifier
            pred = classifier.predict(X_train)
            impurity = impurity_measure.calculate_impurity(y, (pred == -1))
            label_to_impurity[label] = impurity

        label = min(label_to_impurity.items(), key=lambda x: x[1])[0]
        classifier = label_to_classifier[label]
        mask = (classifier.predict(X_train) == -1)
        return mask, LinearClassifierSplit(classifier)

class LinearClassifierSplit(Split):
    def __init__(self, classifier):
        self.classifier = classifier

    def predict(self, features):
        return self.classifier.predict(features)[0] == -1

    def print_dot(self):
        return self.get_hyperplane_str(rounded=True, newlines=True)

    def print_c(self):
        return self.get_hyperplane_str()

    def print_vhdl(self):
        hyperplane = self.get_hyperplane_str()
        hyperplane.replace('X[', 'x')
        hyperplane.replace(']', '')
        return hyperplane

    def get_hyperplane_str(self, rounded=False, newlines=False):
        coef = self.classifier.coef_[0]
        intercept = self.classifier.intercept_[0]
        line = []
        for i in range(len(coef)):
            line.append(f"{round(coef[i], 6) if rounded else coef[i]}*X[{i}]")
        line.append(f"{round(intercept, 6) if rounded else intercept}")
        joiner = "\n+" if newlines else "+"
        hyperplane = joiner.join(line) + " <= 0"
        return hyperplane.replace('+-', '-')
