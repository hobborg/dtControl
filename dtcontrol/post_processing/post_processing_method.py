from abc import ABC, abstractmethod

from dtcontrol.benchmark_suite_classifier import BenchmarkSuiteClassifier

class PostProcessingMethod(BenchmarkSuiteClassifier, ABC):
    def __init__(self, classifier, name):
        super().__init__(name)
        self.classifier = classifier

    @abstractmethod
    def run(self):
        """
        Runs the post-processing method and transforms the decision tree.
        """
        pass

    def is_applicable(self, dataset):
        return self.classifier.is_applicable(dataset)

    def fit(self, dataset):
        self.classifier.fit(dataset)
        self.run()

    def predict(self, dataset, actual_values=True):
        return self.classifier.predict(dataset, actual_values)

    def get_stats(self):
        return self.classifier.get_stats()

    def save(self, file):
        self.classifier.save(file)

    def print_dot(self, x_metadata, y_metadata):
        return self.classifier.print_dot(x_metadata, y_metadata)

    def print_c(self):
        return self.classifier.print_c()
