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
from dtcontrol.decision_tree.splitting.polynomial import PolynomialClassifierSplittingStrategy
from dtcontrol.decision_tree.splitting.neural_net import NeuralNetSplittingStrategy
from dtcontrol.decision_tree.impurity.min_label_entropy import MinLabelEntropy
from dtcontrol.decision_tree.determinization.max_freq_determinizer import MaxFreqDeterminizer
from dtcontrol.decision_tree.determinization.label_powerset_determinizer import LabelPowersetDeterminizer
from dtcontrol.decision_tree.splitting.user_split import UserSplit
import numpy as np

suite = BenchmarkSuite(timeout=3600,
                       save_folder='saved_classifiers',
                       benchmark_file='benchmark_test',
                       rerun=True)

suite.add_datasets(['examples', 'examples/prism', 'examples/storm', 'examples/cps'], include=['cruise_250'])
[dataset.load_if_necessary() for dataset in suite.datasets]
print(f"{[dataset.get_name() for dataset in suite.datasets]}")
ds = suite.datasets[0]

logreg = LinearClassifierSplittingStrategy(LogisticRegression, solver='lbfgs', penalty='none')
logreg.priority = 1

user_input = []
y = LabelPowersetDeterminizer().determinize(ds)
labels, counts = np.unique(y, return_counts=True)
print(f"Labels: {suite.datasets[0].get_unique_labels_from_2d(suite.datasets[0].y)[1]}")
print(f"Labels: {({label : ds.index_label_to_actual(ds.map_unique_label_back(label)) for label in labels})}")
print(f"Labels: {labels} with counts {counts} respectively")
while (int(input("splits?"))):
    user_input.append(list(map(int, input("Choose label indices for mask:").split())))
# user_input = (labels[[0,2]])

input(f"user_split: {user_input}")

u = UserSplit(user_split=user_input[0])
input(f"{u.get_masks(ds)}")

poly = PolynomialClassifierSplittingStrategy(user_splits=user_input)
poly.priority = 0.1

# richer = RicherDomainSplittingStrategy(debug=False)
# richer.priority = 1

# cli = RicherDomainCliStrategy(debug=True)
# cli.priority = 1

aa = AxisAlignedSplittingStrategy()
aa.priority = 0.5

nn = NeuralNetSplittingStrategy(user_splits=user_input)
nn.priority = 1


classifiers = [
    # Interactive
    # DecisionTree([cli], Entropy(), 'interactive'),
    # DecisionTree([nn, poly, aa], MinLabelEntropy(), 'nn-test-accuracy'),
    DecisionTree([nn, poly, aa], MinLabelEntropy(), 'neural-minlabel-user')
]
suite.benchmark(classifiers)
suite.display_html()