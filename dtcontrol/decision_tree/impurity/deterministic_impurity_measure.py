from abc import ABC

from dtcontrol.decision_tree.determinization.non_determinizer import NonDeterminizer
from dtcontrol.decision_tree.impurity.impurity_measure import ImpurityMeasure

class DeterministicImpurityMeasure(ImpurityMeasure, ABC):

    def __init__(self, determinizer=NonDeterminizer()):
        self.determinizer = determinizer
