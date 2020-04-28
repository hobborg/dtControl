from sklearn.linear_model import LogisticRegression

from dtcontrol.benchmark_suite import BenchmarkSuite
from dtcontrol.decision_tree.decision_tree import DecisionTree
from dtcontrol.decision_tree.determinization.max_freq_determinizer import MaxFreqDeterminizer
from dtcontrol.decision_tree.impurity.entropy import Entropy
from dtcontrol.decision_tree.impurity.multi_label_entropy import MultiLabelEntropy
from dtcontrol.decision_tree.splitting.axis_aligned import AxisAlignedSplittingStrategy
from dtcontrol.decision_tree.splitting.linear_classifier import LinearClassifierSplittingStrategy

suite = BenchmarkSuite(timeout=60,
                       save_folder='saved_classifiers',
                       benchmark_file='benchmark',
                       rerun=False)

suite.add_datasets(['examples', 'examples/prism', 'examples/storm'], include=['cartpole'])

aa = AxisAlignedSplittingStrategy()
logreg = LinearClassifierSplittingStrategy(LogisticRegression, solver='lbfgs', penalty='none')
classifiers = [
    DecisionTree([aa], Entropy(), 'CART'),
    DecisionTree([aa, logreg], Entropy(), 'LogReg'),
    DecisionTree([aa], Entropy(), 'Early-stopping', early_stopping=True),
    DecisionTree([aa], Entropy(MaxFreqDeterminizer()), 'MaxFreq', early_stopping=True),
    DecisionTree([aa], MultiLabelEntropy(), 'MultiLabelEntropy', early_stopping=True)
]
suite.benchmark(classifiers)
suite.display_html()
