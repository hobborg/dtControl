from benchmark_suite import BenchmarkSuite
from classifiers.max_every_node_decision_tree import MaxCartDecisionTree

suite = BenchmarkSuite(timeout=60*60*2, save_folder='saved_classifiers', benchmark_file='benchmark_tmp')
suite.delete_classifier_results('MaxEveryNodeDT')
suite.add_datasets(['../XYdatasets', '../dumps'],
                   include=["traffic_1m"],
                   exclude=[
                            ],
                   multiout=['vehicle', 'aircraft', '10rooms'])
classifiers = [  # CartCustomDecisionTree(),
               #LinearClassifierDecisionTree(LogisticRegression, solver='lbfgs', penalty='none'),
               #LinearClassifierDecisionTree(LinearSVC, max_iter=5000),
    MaxCartDecisionTree(),
               #MaxLCDecisionTree(LogisticRegression, solver='lbfgs', penalty='none'),
               #OC1Wrapper(num_restarts=20, num_jumps=5),
               #MaxEveryNodeMultiDecisionTree()
               ]
#suite.delete_dataset_results('cruise-latest')
suite.benchmark(classifiers)

# TODO Mathias: two trees for det multiinput, check whether dataset is multiinput in is_applicable. Integrate this check into loaders?