from sklearn.linear_model import LogisticRegression

from dtcontrol.benchmark_suite import BenchmarkSuite
from dtcontrol.decision_tree.decision_tree import DecisionTree
from dtcontrol.decision_tree.impurity.entropy import Entropy
from dtcontrol.decision_tree.splitting.context_aware.weinhuber_approach_splitting_strategy import \
    WeinhuberApproachSplittingStrategy
from dtcontrol.decision_tree.splitting.axis_aligned import AxisAlignedSplittingStrategy
from dtcontrol.decision_tree.splitting.linear_classifier import LinearClassifierSplittingStrategy
from dtcontrol.decision_tree.splitting.context_aware.weinhuber_approach_predicate_generator_strategy import \
    WeinhuberApproachPredicateGeneratorStrategy
from dtcontrol.decision_tree.splitting.context_aware.weinhuber_approach_linear_units_classifier import \
    WeinhuberApproachLinearUnitsClassifier

suite = BenchmarkSuite(timeout=999999999,
                       save_folder='saved_classifiers',
                       benchmark_file='benchmark',
                       rerun=True)

suite.add_datasets(['examples', 'examples/prism', 'examples/storm', 'examples/eval'], include=['fruits_dataset'])

# logreg = LinearClassifierSplittingStrategy(LogisticRegression, solver='lbfgs', penalty='none')
# logreg.priority = 1

# weinhuber = WeinhuberApproachSplittingStrategy(debug=False)
# weinhuber.curve_fitting_method = "optimized"
# weinhuber.priority = 1

generator = WeinhuberApproachPredicateGeneratorStrategy(debug=True)
generator.priority = 1

# linear_unit = WeinhuberApproachLinearUnitsClassifier(LogisticRegression, ["meter", "meter", "baum", "haus"], solver='lbfgs', penalty='none')
# linear_unit.priority = 1

aa = AxisAlignedSplittingStrategy()
aa.priority = 1

classifiers = [
    DecisionTree([generator], Entropy(), 'Presentation')
]

suite.benchmark(classifiers)
suite.display_html()
