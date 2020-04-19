import sys

from sklearn.linear_model import LogisticRegression

from dtcontrol.benchmark_suite import BenchmarkSuite
from dtcontrol.decision_tree.decision_tree import DecisionTree
from dtcontrol.decision_tree.determinization.label_powerset_determinizer import LabelPowersetDeterminizer
from dtcontrol.decision_tree.impurity.entropy import Entropy
from dtcontrol.decision_tree.splitting.axis_aligned import AxisAlignedSplittingStrategy
from dtcontrol.decision_tree.splitting.categorical_multi import CategoricalMultiSplittingStrategy
from dtcontrol.decision_tree.splitting.categorical_single import CategoricalSingleSplittingStrategy
from dtcontrol.decision_tree.splitting.linear_classifier import LinearClassifierSplittingStrategy
from dtcontrol.decision_tree.splitting.oc1 import OC1SplittingStrategy

suite = BenchmarkSuite(timeout=60 * 2,
                       save_folder='prism_saved_classifiers',
                       benchmark_file='prism_benchmark',
                       rerun=False)

suite.add_datasets(['../examples/prism'])

aa = AxisAlignedSplittingStrategy()
categorical_multi = CategoricalMultiSplittingStrategy()
tol0 = CategoricalMultiSplittingStrategy(value_grouping=True, tolerance=0)
tol_small = CategoricalMultiSplittingStrategy(value_grouping=True)
tol_medium = CategoricalMultiSplittingStrategy(value_grouping=True, tolerance=.2)
tol_inf = CategoricalMultiSplittingStrategy(value_grouping=True, tolerance=sys.maxsize)
categorical_single = CategoricalSingleSplittingStrategy()
logreg = LinearClassifierSplittingStrategy(LogisticRegression, solver='lbfgs', penalty='none')
oc1 = OC1SplittingStrategy()

classifiers = [
    DecisionTree(LabelPowersetDeterminizer(), [aa, categorical_multi, logreg], Entropy(), 'logreg'),
    DecisionTree(LabelPowersetDeterminizer(), [aa, categorical_multi, oc1], Entropy(), 'oc1'),
    # DecisionTree(NonDeterminizer(), [aa, categorical_single], Entropy(), 'single'),
    DecisionTree(LabelPowersetDeterminizer(), [aa, categorical_multi], Entropy(), 'multi'),
    # DecisionTree(NonDeterminizer(), [aa, tol0], Entropy(), 'tol 0'),
    # DecisionTree(NonDeterminizer(), [aa, tol_small], Entropy(), 'tol 1e-5'),
    # DecisionTree(NonDeterminizer(), [aa, tol_medium], Entropy(), 'tol .2'),
    # DecisionTree(NonDeterminizer(), [aa, tol_inf], Entropy(), 'tol inf'),
    # DecisionTree(NonDeterminizer(), [aa, categorical_single, categorical_multi], Entropy(), 'both'),
    # DecisionTree(NonDeterminizer(), [aa, categorical_multi, logreg], Entropy(), 'multi_logreg')
]
suite.benchmark(classifiers)
suite.display_html()
