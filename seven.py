from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC

from benchmark_suite import BenchmarkSuite
from classifiers.linear_classifier_dt import LinearClassifierDT
from classifiers.max_freq_linear_classifier_dt import MaxFreqLinearClassifierDT
from classifiers.norm_dt import NormDT
from classifiers.norm_linear_classifier_dt import NormLinearClassifierDT
from classifiers.oc1_wrapper import OC1Wrapper
from classifiers.cart_custom_dt import CartDT
from classifiers.max_freq_dt import MaxFreqDT
from classifiers.bdd import BDD
import sys

def run(benchmark_file):
    suite = BenchmarkSuite(timeout=60 * 60 * 3, save_folder=f'saved_classifiers_{benchmark_file}', benchmark_file=benchmark_file,
                           is_artifact=True)
    suite.add_datasets(['../XYdatasets', '../dumps'],
                       include=['10rooms', 'helicopter', 'traffic_30m', 'vehicle', 'aircraft'],
                       exclude=[
                       ]
                       )
    classifiers = [
        # CartDT(),
        # LinearClassifierDT(LogisticRegression, solver='lbfgs', penalty='none'),
        # LinearClassifierDT(LinearSVC, max_iter=5000),
        # MaxFreqDT(),
        # MaxLCDecisionTree(LogisticRegression, solver='lbfgs', penalty='none'),
        # OC1Wrapper(num_restarts=20, num_jumps=5),
        # BDD()
        # MaxEveryNodeMultiDecisionTree()
        # MaxFreqLinearClassifierDT(LogisticRegression, solver='lbfgs', penalty='none')
        NormLinearClassifierDT(min, LogisticRegression, solver='lbfgs', penalty='none')
    ]
    suite.benchmark(classifiers)


if __name__ == '__main__':
    benchmark_file = sys.argv[1]
    run(benchmark_file)
