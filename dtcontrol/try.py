from sklearn.linear_model import LogisticRegression

from dtcontrol.benchmark_suite import BenchmarkSuite
from dtcontrol.classifiers.linear_classifier_dt import LinearClassifierDT
from dtcontrol.classifiers.oc1_wrapper import OC1Wrapper
from dtcontrol.classifiers.cart_custom_dt import CartDT
from dtcontrol.classifiers.max_freq_dt import MaxFreqDT
from dtcontrol.classifiers.bdd import BDD

suite = BenchmarkSuite(timeout=60 * 60 * 2, save_folder='saved_classifiers', benchmark_file='benchmark_tmp', rerun=True)
suite.add_datasets(['examples'],
                   include=["cartpole",
                            # "tworooms-noneuler-latest",
                            # "helicopter",
                            # "cruise-latest",
                            # "dcdc",
                            # "10rooms",
                            # "truck_trailer",
                            # "traffic_1m",
                            # "traffic_10m",
                            # "traffic_30m",
                            # "vehicle",
                            # "aircraft"
                            ],
                   exclude=[
                       'aircraft', 'traffic_30m', 'truck_trailer'
                   ]
                   )
classifiers = [
    CartDT(),
    # LinearClassifierDT(LogisticRegression, solver='lbfgs', penalty='none'),
    # LinearClassifierDecisionTree(LinearSVC, max_iter=5000),
    # MaxFreqDT(),
    # MaxLCDecisionTree(LogisticRegression, solver='lbfgs', penalty='none'),
    # OC1Wrapper(num_restarts=1, num_jumps=1),
    # BDD()
    # MaxEveryNodeMultiDecisionTree()
]
suite.benchmark(classifiers)
