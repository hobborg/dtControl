from linear_classifier_decision_tree import LinearClassifierDecisionTree
from sklearn.linear_model import LogisticRegression
from dataset import AnyLabelDataset

ds = AnyLabelDataset('../XYdatasets/cartpole_X.pickle', '../XYdatasets/cartpole_Y.npy')
dt = LinearClassifierDecisionTree(LogisticRegression, solver='lbfgs', penalty='none')
dt.fit(ds.X_train, ds.get_combination_labels())
dt.export_dot(file='tmp/try_max.dot')
