import numpy as np
from sklearn.linear_model import LogisticRegression
from tqdm import tqdm
from dtcontrol.bdd import BDD
from dtcontrol.benchmark_suite import BenchmarkSuite
from dtcontrol.decision_tree.decision_tree import DecisionTree
from dtcontrol.decision_tree.impurity.entropy import Entropy
from dtcontrol.decision_tree.splitting.context_aware.richer_domain_splitting_strategy import \
    RicherDomainSplittingStrategy
from dtcontrol.decision_tree.splitting.axis_aligned import AxisAlignedSplittingStrategy
from dtcontrol.decision_tree.splitting.linear_classifier import LinearClassifierSplittingStrategy
from dtcontrol.decision_tree.splitting.context_aware.richer_domain_cli_strategy import \
    RicherDomainCliStrategy
from dtcontrol.pre_processing.norm_pre_processor import NormPreProcessor
from collections import defaultdict

suite = BenchmarkSuite(timeout=3600,
                       save_folder='saved_classifiers',
                       benchmark_file='benchmark',
                       rerun=True)

suite.add_datasets(['examples', 'examples/prism', 'examples/storm', 'examples/cps'], include=['cartpole'])

logreg = LinearClassifierSplittingStrategy(LogisticRegression, solver='lbfgs', penalty='none')
logreg.priority = 1

dt = DecisionTree([logreg], Entropy(), 'logreg')

classifiers = [
    dt,
]
print("Constructing DT...")
suite.benchmark(classifiers)

# now our dt is constructed...
suite.display_html()

print("Starting BDD-DT...")

print("Collecting all predicates...")
# collect all predicates used in dt
predicates = dt.root.collect_predicates()

# extracting old controller from suite
dataset = suite.datasets[0]

print("Applying all collected predicates to all states...")
# apply all predicates to dataset and stores result in pred_dict
pred_dict = dict()
for pred in tqdm(predicates):
    # get masks returns tuple of masks
    pred_dict[pred] = pred.get_masks(dataset)[0]


# casting result to dict with key as state and list of predicate evaluations
state_dict = dict()
for state in tqdm(dataset.x_metadata["state_mapping"]):
    # getting the corresponding line in the dataset which corresponds to the state
    i = dataset.x_metadata["state_mapping"].index(state)

    state_dict[state] = []
    for pred in predicates:
        state_dict[state].append(pred_dict[pred][i])

print("BDD-DT finished.")
example_state = dataset.x_metadata["state_mapping"][0]
print("Example state: " + str(example_state))
print("All predicates applied to example state:")
print(state_dict[example_state])


# Creating a dictionary to store states with the same bool list
states_with_same_encoding = defaultdict(list)

for key, value_list in state_dict.items():
    # Using a tuple of the bool list as the dictionary key
    states_with_same_encoding[tuple(value_list)].append(key)

for encoding in states_with_same_encoding:
    print(str(states_with_same_encoding[encoding]) + " has encoding " + str(encoding))

keys_with_same_bool_list = {k: v for k, v in state_dict.items() if len(v) > 1}
print(len(keys_with_same_bool_list))
