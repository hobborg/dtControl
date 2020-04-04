from abc import ABC, abstractmethod

from dtcontrol.decision_tree.determinization.non_determinizer import NonDeterminizer
from dtcontrol.decision_tree.impurity.impurity_measure import ImpurityMeasure

class DeterministicImpurityMeasure(ABC, ImpurityMeasure):

    def __init__(self, determinizer=None):
        self.determinizer = determinizer
        if self.determinizer is None:
            self.determinizer = NonDeterminizer()
