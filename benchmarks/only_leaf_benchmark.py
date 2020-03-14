from sklearn.linear_model import LogisticRegression

from dtcontrol.benchmark_suite import BenchmarkSuite
from dtcontrol.decision_tree.decision_tree import DecisionTree
from dtcontrol.decision_tree.determinization.non_determinizer import NonDeterminizer
from dtcontrol.decision_tree.impurity.entropy import Entropy
from dtcontrol.decision_tree.splitting.axis_aligned import AxisAlignedSplittingStrategy
from dtcontrol.decision_tree.splitting.linear_classifier import LinearClassifierSplittingStrategy
from dtcontrol.decision_tree.splitting.linear_classifier_only_leaf import LinearClassifierOnlyLeafSplittingStrategy

suite = BenchmarkSuite(timeout=60,
                       save_folder='leaves_saved_classifiers',
                       benchmark_file='leaves_benchmark',
                       rerun=False)

suite.add_datasets(['examples', 'examples/prism'],
                   include=[
                       # "firewire_abst",
                       # "wlan0",
                       # "mer10"
                       "cartpole",
                       "tworooms-noneuler-latest",
                       # "helicopter",
                       # "cruise-latest",
                       # "dcdc",
                       "10rooms",
                       # "truck_trailer",
                       # "traffic_1m",
                       # "traffic_10m",
                       # "traffic_30m",
                       # "vehicle",
                       # "aircraft"
                   ]
                   )

aa = AxisAlignedSplittingStrategy()
logreg = LinearClassifierSplittingStrategy(LogisticRegression, solver='lbfgs', penalty='none')
only_leaf = LinearClassifierOnlyLeafSplittingStrategy(LogisticRegression, solver='lbfgs', penalty='none')
classifiers = [
    DecisionTree(NonDeterminizer(), [aa], Entropy(), 'CART'),
    DecisionTree(NonDeterminizer(), [aa, logreg], Entropy(), 'logreg'),
    DecisionTree(NonDeterminizer(), [aa, only_leaf], Entropy(), 'only_leaf'),
]
suite.benchmark(classifiers)
suite.display_html()
