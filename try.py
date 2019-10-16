from benchmark_suite import BenchmarkSuite
from classifiers.cart_custom_decision_tree import CartCustomDecisionTree
from classifiers.max_every_node_decision_tree import MaxCartDecisionTree

suite = BenchmarkSuite(timeout=60*60*2, save_folder='saved_classifiers', benchmark_file='benchmark_tmp')
suite.add_datasets(['../XYdatasets', '../dumps'],
                   include=["traffic_1m"],
                   exclude=[
                   ]
                   )
classifiers = [
    CartCustomDecisionTree(),
    # LinearClassifierDecisionTree(LogisticRegression, solver='lbfgs', penalty='none'),
    # LinearClassifierDecisionTree(LinearSVC, max_iter=5000),
    MaxCartDecisionTree(),
    # MaxLCDecisionTree(LogisticRegression, solver='lbfgs', penalty='none'),
    # OC1Wrapper(num_restarts=20, num_jumps=5),
    # MaxEveryNodeMultiDecisionTree()
]
suite.delete_dataset_results('cruise-latest')
suite.benchmark(classifiers)
