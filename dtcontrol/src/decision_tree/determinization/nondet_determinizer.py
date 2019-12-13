from src.decision_tree.determinization.determinizer import Determinizer

class NondetDeterminizer(Determinizer):
    """
    This determinizer doesn't actually do any determinization but simply uses the unique label approach.
    """

    def determinize(self, dataset):
        return dataset.get_unique_labels()

    def get_index_label(self, label):
        return self.dataset.map_unique_label_back(label)

    def determinize_once_before_construction(self):
        return True

    def is_only_multioutput(self):
        return False
