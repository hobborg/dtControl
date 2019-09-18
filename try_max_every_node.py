from sklearn.linear_model import LogisticRegression
import numpy as np
import pandas as pd
from max_every_node_decision_tree import MaxEveryNodeDecisionTree

def compute_accuracy(Y_pred, Y_train):
    if len(Y_pred[Y_pred == None]) != 0:
        return None

    num_correct = 0
    for i in range(len(Y_pred)):
        predicted_indices = {Y_pred[i]}
        correct_indices = set(np.nonzero(Y_train[i])[0])
        if set.issubset(predicted_indices, correct_indices):
            num_correct += 1
    return num_correct / len(Y_pred)

X_train = np.array(pd.read_pickle('../XYdatasets/cruise-latest_X.pickle'))
Y_train = np.load('../XYdatasets/cruise-latest_Y.npy')

classifier = MaxEveryNodeDecisionTree(LogisticRegression, solver='lbfgs', penalty='none')
classifier.fit(X_train, Y_train)
classifier.export_dot(file='tree.dot')

print('Total number of nodes: {}'.format(classifier.root.num_nodes))
print('{}/{} nodes used not AA'.format(classifier.root.num_not_axis_aligned, classifier.root.num_nodes))
print('Accuracy: {}'.format(compute_accuracy(classifier.predict(X_train), Y_train)))