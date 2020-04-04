from abc import ABC, abstractmethod

from dtcontrol.decision_tree.impurity.impurity_measure import ImpurityMeasure

class NondeterministicImpurityMeasure(ABC, ImpurityMeasure):
    @abstractmethod
    def get_oc1_name(self):
        return None
