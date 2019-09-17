def compute_accuracy(self, classifier):
    Y_pred = classifier.predict(self.X_train)
    if len(Y_pred[Y_pred == None]) != 0:
        return None
    if not self.any_label:
        return accuracy_score(self.Y_train, Y_pred)

    num_correct = 0
    for i in range(len(Y_pred)):
        pred = self.unique_label_mapping[Y_pred[i]] if classifier.needs_unique_labels else Y_pred[i]
        predicted_indices = set(np.nonzero(pred)[0])
        correct_indices = set(np.nonzero(self.Y_train[i])[0])
        if set.issubset(predicted_indices, correct_indices):
            num_correct += 1
    return num_correct / len(Y_pred)

# TODO