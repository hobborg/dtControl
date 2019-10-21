from benchmark_suite import BenchmarkSuite
from classifiers.oc1_wrapper import OC1Wrapper
from classifiers.cart_custom_dt import CartDT
from classifiers.max_freq_dt import MaxFreqDT

suite = BenchmarkSuite(timeout=60*60*2, save_folder='saved_classifiers', benchmark_file='benchmark_tmp')
suite.add_datasets(['../XYdatasets', '../dumps'],
                   include=["cartpole"],
                   exclude=[
                   ]
                   )
classifiers = [
    # CartDT(),
    # LinearClassifierDecisionTree(LogisticRegression, solver='lbfgs', penalty='none'),
    # LinearClassifierDecisionTree(LinearSVC, max_iter=5000),
    # MaxFreqDT(),
    # MaxLCDecisionTree(LogisticRegression, solver='lbfgs', penalty='none'),
    OC1Wrapper(num_restarts=20, num_jumps=5),
    # MaxEveryNodeMultiDecisionTree()
]
suite.benchmark(classifiers)
