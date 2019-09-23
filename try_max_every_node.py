from sklearn.tree import DecisionTreeClassifier
from sklearn.multioutput import MultiOutputClassifier
from benchmark_suite import BenchmarkSuite
from max_every_node_lc_decision_tree import MaxEveryNodeLCDecisionTree
from max_every_node_decision_tree import MaxEveryNodeDecisionTree
from decision_tree_wrapper import DecisionTreeWrapper
from unique_label_decision_tree import UniqueLabelDecisionTree
from linear_classifier_decision_tree import LinearClassifierDecisionTree
from smarter_splits.OC1Wrapper import OC1Wrapper
from sklearn.linear_model import LogisticRegression
from table_printer import print_table
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score
from dataset import MultiOutputDataset, AnyLabelDataset
from label_format import LabelFormat
from multi_output_decision_tree import MultiOutputDecisionTree
from standard_custom_decision_tree import StandardCustomDecisionTree

ds = AnyLabelDataset('../XYdatasets/cartpole_X.pickle', '../XYdatasets/cartpole_Y.npy')
dt = LinearClassifierDecisionTree(LogisticRegression, solver='lbfgs', penalty='none')
dt.fit(ds.X_train, ds.get_combination_labels())
dt.export_dot(file='tmp/try_max.dot')
