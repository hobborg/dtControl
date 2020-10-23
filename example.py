from sklearn.linear_model import LogisticRegression

from dtcontrol.benchmark_suite import BenchmarkSuite
from dtcontrol.decision_tree.decision_tree import DecisionTree
from dtcontrol.decision_tree.impurity.entropy import Entropy
from dtcontrol.decision_tree.splitting.context_aware.richer_domain_splitting_strategy import \
    RicherDomainSplittingStrategy
from dtcontrol.decision_tree.splitting.axis_aligned import AxisAlignedSplittingStrategy
from dtcontrol.decision_tree.splitting.linear_classifier import LinearClassifierSplittingStrategy
from dtcontrol.decision_tree.splitting.context_aware.richer_domain_cli_strategy import \
    RicherDomainCliStrategy

suite = BenchmarkSuite(timeout=3600,
                       save_folder='saved_classifiers',
                       benchmark_file='benchmark',
                       rerun=True)

suite.add_datasets(['examples', 'examples/prism', 'examples/storm', 'examples/eval'], include=['cartpole'])

logreg = LinearClassifierSplittingStrategy(LogisticRegression, solver='lbfgs', penalty='none')
logreg.priority = 1

richer = RicherDomainSplittingStrategy(debug=False)
richer.priority = 1

cli = RicherDomainCliStrategy(debug=True)
cli.priority = 1

aa = AxisAlignedSplittingStrategy()
aa.priority = 1

classifiers = [
    # Interactive
    # DecisionTree([cli], Entropy(), 'interactive'),
    DecisionTree([aa, logreg], Entropy(), 'aa-logreg')
]

suite.benchmark(classifiers)
suite.display_html()
