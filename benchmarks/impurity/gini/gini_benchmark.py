from sklearn.linear_model import LogisticRegression

from dtcontrol.benchmark_suite import BenchmarkSuite
from dtcontrol.decision_tree.decision_tree import DecisionTree
from dtcontrol.decision_tree.determinization.max_freq_determinizer import MaxFreqDeterminizer
from dtcontrol.decision_tree.determinization.non_determinizer import NonDeterminizer
from dtcontrol.decision_tree.impurity.entropy import Entropy
from dtcontrol.decision_tree.impurity.gini_index import GiniIndex
from dtcontrol.decision_tree.splitting.axis_aligned import AxisAlignedSplittingStrategy
from dtcontrol.decision_tree.splitting.linear_classifier import LinearClassifierSplittingStrategy
from dtcontrol.decision_tree.splitting.oc1 import OC1SplittingStrategy

suite = BenchmarkSuite(timeout=60 * 3,
                       benchmark_file='gini',
                       rerun=False)

suite.add_datasets(['../../../examples'],
                   include=[
                       "cartpole",
                       "tworooms-noneuler-latest",
                       # "helicopter",
                       "cruise-latest",
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
oc1 = OC1SplittingStrategy(num_restarts=10, num_jumps=5)
classifiers = [
    DecisionTree(NonDeterminizer(), [aa], Entropy(), 'CART-ent'),
    DecisionTree(NonDeterminizer(), [aa], GiniIndex(), 'CART-gini'),
    DecisionTree(NonDeterminizer(), [aa, logreg], Entropy(), 'logreg-ent'),
    DecisionTree(NonDeterminizer(), [aa, logreg], GiniIndex(), 'logreg-gini'),
    DecisionTree(MaxFreqDeterminizer(), [aa], Entropy(), 'MaxFreq-ent'),
    DecisionTree(MaxFreqDeterminizer(), [aa], GiniIndex(), 'MaxFreq-gini'),
]
suite.benchmark(classifiers)
suite.display_html()
