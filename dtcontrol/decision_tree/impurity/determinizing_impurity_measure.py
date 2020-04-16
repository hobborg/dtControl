from abc import ABC

from dtcontrol.decision_tree.determinization.label_powerset_determinizer import LabelPowersetDeterminizer
from dtcontrol.decision_tree.impurity.impurity_measure import ImpurityMeasure

class DeterminizingImpurityMeasure(ImpurityMeasure, ABC):

    def __init__(self, determinizer=LabelPowersetDeterminizer()):
        self.determinizer = determinizer
