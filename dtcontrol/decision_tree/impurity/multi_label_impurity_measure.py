from abc import ABC

from dtcontrol.decision_tree.impurity.impurity_measure import ImpurityMeasure

class MultiLabelImpurityMeasure(ImpurityMeasure, ABC):

    def get_oc1_name(self):
        return None
