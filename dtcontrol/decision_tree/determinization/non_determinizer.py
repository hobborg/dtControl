from dtcontrol.decision_tree.determinization.determinizer import Determinizer

class NonDeterminizer(Determinizer):
    """
    This determinizer doesn't actually do any determinization but simply uses the label powerset approach.
    """

    def determinize(self, dataset):
        return dataset.get_unique_labels()

    def is_pre(self):
        return True
