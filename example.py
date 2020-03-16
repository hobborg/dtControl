from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC

from dtcontrol.benchmark_suite import BenchmarkSuite
from dtcontrol.decision_tree.decision_tree import DecisionTree
from dtcontrol.decision_tree.determinization.non_determinizer import NonDeterminizer
from dtcontrol.decision_tree.impurity.entropy import Entropy
from dtcontrol.decision_tree.impurity.gini_index import GiniIndex
from dtcontrol.decision_tree.impurity.twoing_rule import TwoingRule
from dtcontrol.decision_tree.splitting.axis_aligned import AxisAlignedSplittingStrategy
from dtcontrol.decision_tree.splitting.categorical_multi import CategoricalMultiSplittingStrategy
from dtcontrol.decision_tree.splitting.linear_classifier import LinearClassifierSplittingStrategy
from dtcontrol.decision_tree.splitting.oc1 import OC1SplittingStrategy

suite = BenchmarkSuite(timeout=60 * 60 * 3,
                       save_folder='saved_classifiers',
                       benchmark_file='benchmark',
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
                       # "10rooms",
                       # "truck_trailer",
                       # "traffic_1m",
                       # "traffic_10m",
                       # "traffic_30m",
                       # "vehicle",
                       # "aircraft"
                   ]
                   )

aa = AxisAlignedSplittingStrategy()
cat = CategoricalMultiSplittingStrategy()
oc1 = OC1SplittingStrategy(num_restarts=10, num_jumps=5)
logreg = LinearClassifierSplittingStrategy(LogisticRegression, solver='lbfgs', penalty='none')
linsvc = LinearClassifierSplittingStrategy(LinearSVC, max_iter=5000)
classifiers = [
    # DecisionTree(NonDeterminizer(), [aa, cat], Entropy(), 'CategoricalCART')
    # DecisionTree(NonDeterminizer(), [aa], Entropy(), 'CART-ent'),
    # DecisionTree(NonDeterminizer(), [aa], AUROC(), 'CART-auc'),
    # DecisionTree(NonDeterminizer(), [aa, logreg], AUROC(), 'CART-logreg-auc'),
    # DecisionTree(NonDeterminizer(), [aa, linsvc], Entropy(), 'linsvc'),
    # DecisionTree(NonDeterminizer(), [aa, logreg], Entropy(), 'logreg'),
    DecisionTree(NonDeterminizer(), [aa, oc1], Entropy(), 'OC1-ent'),
    DecisionTree(NonDeterminizer(), [aa, oc1], GiniIndex(), 'OC1-gini'),
    DecisionTree(NonDeterminizer(), [aa, oc1], TwoingRule(), 'OC1-twoing'),
    # DecisionTree(MaxFreqDeterminizer(), [aa], Entropy(), 'MaxFreq'),
    # DecisionTree(MaxFreqDeterminizer(), [aa, logreg], Entropy(), 'MaxFreqLC'),
    # DecisionTree(NormDeterminizer(min), [aa], Entropy(), 'MinNorm'),
    # DecisionTree(NormDeterminizer(min), [aa, logreg], Entropy(), 'MinNormLC'),
]
suite.benchmark(classifiers)
suite.display_html()
