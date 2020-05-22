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

weinhuber = WeinhuberApproachSplittingStrategy(predicate_structure_difference=5, predicate_dt_range=5,
                                               fallback_strategy=[AxisAlignedSplittingStrategy()])

"""
aa Priority = 1
lin Priority = 0.5
...
DecisionTree([aa, lin])


"""

# splitting
aa = AxisAlignedSplittingStrategy()
# oc1 = OC1SplittingStrategy()
cat = CategoricalSingleSplittingStrategy()

classifiers = [
    DecisionTree([weinhuber], Entropy(), 'Testing')
    # DecisionTree([smart_equal], Entropy(), 'Categorical Single Equal'),
    # DecisionTree([smart_exp], Entropy(), 'Experimental'),
    # DecisionTree([smart_lin], Entropy(), 'Type: Linear Classifier'),
    # DecisionTree([smart_UIS], Entropy(), 'User Input Predicat '),
    # DecisionTree([user_predicat], Entropy(), 'User Predicat Splitting')
    # DecisionTree([lin, aa], Entropy(), 'Old Version'),
    # DecisionTree([aa], Entropy(), 'Old Version'),
    # DecisionTree([lin], Entropy(), 'Old Version'),
    # DecisionTree([oc1], Entropy(), 'OC1'),
    # DecisionTree([cat], Entropy(), 'BUGGY: Categorical Single Splitting'),
    # DecisionTree([aa], Entropy(), 'CART'),
    # DecisionTree([aa, logreg], Entropy(), 'LogReg'),
    # DecisionTree([aa], Entropy(), 'Early-stopping', early_stopping=True),
    # DecisionTree([aa], Entropy(MaxFreqDeterminizer()), 'MaxFreq', early_stopping=True),
    # DecisionTree([aa], MultiLabelEntropy(), 'MultiLabelEntropy', early_stopping=True)
]
suite.benchmark(classifiers)
suite.display_html()
