from dtcontrol.decision_tree.determinization.determinizer import Determinizer

class NonDeterminizer(Determinizer):
    """
    This determinizer doesn't actually do any determinization but simply uses the label powerset approach.
    """

    def determinize(self, dataset):
        if self.pre_determinized_labels is None:
            self.pre_determinized_labels = dataset.get_unique_labels()
        return self.pre_determinized_labels
