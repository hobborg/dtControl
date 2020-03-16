from sklearn.linear_model import LogisticRegression

from dtcontrol.benchmark_suite import BenchmarkSuite
from dtcontrol.decision_tree.decision_tree import DecisionTree
from dtcontrol.decision_tree.determinization.non_determinizer import NonDeterminizer
from dtcontrol.decision_tree.impurity.entropy import Entropy
from dtcontrol.decision_tree.splitting.axis_aligned import AxisAlignedSplittingStrategy
from dtcontrol.decision_tree.splitting.categorical_multi import CategoricalMultiSplittingStrategy
from dtcontrol.decision_tree.splitting.categorical_single import CategoricalSingleSplittingStrategy
from dtcontrol.decision_tree.splitting.linear_classifier import LinearClassifierSplittingStrategy

suite = BenchmarkSuite(timeout=60 * 2,
                       save_folder='prism_saved_classifiers',
                       benchmark_file='prism_benchmark',
                       rerun=False)

suite.add_datasets(['examples/prism'])

aa = AxisAlignedSplittingStrategy()
categorical_multi = CategoricalMultiSplittingStrategy()
categorical_single = CategoricalSingleSplittingStrategy()
logreg = LinearClassifierSplittingStrategy(LogisticRegression, solver='lbfgs', penalty='none')
classifiers = [
    DecisionTree(NonDeterminizer(), [aa, categorical_single], Entropy(), 'single'),
    DecisionTree(NonDeterminizer(), [aa, categorical_multi], Entropy(), 'multi'),
    DecisionTree(NonDeterminizer(), [aa, categorical_single, categorical_multi], Entropy(), 'both'),
    # DecisionTree(NonDeterminizer(), [aa, categorical_multi, logreg], Entropy(), 'multi_logreg')
]
suite.benchmark(classifiers)
suite.display_html()
