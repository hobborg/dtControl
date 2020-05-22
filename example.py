from sklearn.linear_model import LogisticRegression

from dtcontrol.benchmark_suite import BenchmarkSuite
from dtcontrol.decision_tree.decision_tree import DecisionTree
from dtcontrol.decision_tree.impurity.entropy import Entropy

# context_aware
from dtcontrol.decision_tree.splitting.context_aware.OldDraft.numerical_single_equal import \
    CategoricalSingleEqualSplittingStrategy
from dtcontrol.decision_tree.splitting.context_aware.OldDraft.experimental_split import ExperimentalSplittingStrategy
from dtcontrol.decision_tree.splitting.context_aware.OldDraft.linear_type_classifier import \
    LinearClassifierSplittingStrategy
from dtcontrol.decision_tree.splitting.context_aware.OldDraft.linear_type_classifier_user_input import \
    LinearClassifierSplittingStrategy as UIS
from dtcontrol.decision_tree.splitting.context_aware.OldDraft.user_predicat_split import UserPredicatSplittingStrategy

from dtcontrol.decision_tree.splitting.context_aware.weinhuber_approach_splitting_strategy import \
    WeinhuberApproachSplittingStrategy

# splitting
from dtcontrol.decision_tree.splitting.axis_aligned import AxisAlignedSplittingStrategy
# from dtcontrol.decision_tree.splitting.oc1 import OC1SplittingStrategy
from dtcontrol.decision_tree.splitting.categorical_single import CategoricalSingleSplittingStrategy

suite = BenchmarkSuite(timeout=999,
                       save_folder='saved_classifiers',
                       benchmark_file='benchmark',
                       rerun=True)

suite.add_datasets(['examples', 'examples/prism', 'examples/storm'], include=['fruits_dataset'])

# context_aware
smart_equal = CategoricalSingleEqualSplittingStrategy()
smart_exp = ExperimentalSplittingStrategy()
smart_lin = LinearClassifierSplittingStrategy(LogisticRegression, solver='lbfgs', penalty='none')
smart_UIS = UIS(LogisticRegression, solver='lbfgs', penalty='none')
user_predicat = UserPredicatSplittingStrategy()

weinhuber = WeinhuberApproachSplittingStrategy(predicate_structure_difference=5, predicate_dt_range=5)
weinhuber.priority = 1
aa = AxisAlignedSplittingStrategy()
aa.priority = 1

classifiers = [
    DecisionTree([weinhuber, aa], Entropy(), 'Testing')
]
suite.benchmark(classifiers)
suite.display_html()
