import unittest

from sklearn.linear_model import LogisticRegression

from src.benchmark_suite import BenchmarkSuite
from src.classifiers.cart_custom_dt import CartDT
from src.classifiers.linear_classifier_dt import LinearClassifierDT
from src.classifiers.max_freq_dt import MaxFreqDT
from src.classifiers.max_freq_linear_classifier_dt import MaxFreqLinearClassifierDT

class IntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.suite = BenchmarkSuite(timeout=60 * 5,
                                    save_folder='test/saved_classifiers',
                                    benchmark_file='test/benchmark',
                                    rerun=True)
        self.suite.add_datasets(['examples'], include=['cartpole', '10rooms', 'vehicle'], )

    def test_fast(self):
        classifiers = [CartDT(),
                       LinearClassifierDT(LogisticRegression, solver='lbfgs', penalty='none'),
                       MaxFreqDT(),
                       MaxFreqLinearClassifierDT(LogisticRegression, solver='lbfgs', penalty='none')]
        self.suite.benchmark(classifiers)

if __name__ == '__main__':
    unittest.main()
