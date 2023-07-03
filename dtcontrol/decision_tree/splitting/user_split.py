from dtcontrol.decision_tree.splitting.split import Split
from dtcontrol.decision_tree.determinization.label_powerset_determinizer import LabelPowersetDeterminizer
import numpy as np

class UserSplit(Split):
    def __init__(self, user_split):
        super().__init__()
        self.user_split = user_split
        self.determinizer = LabelPowersetDeterminizer()
    def get_masks(self, dataset):
        y = self.determinizer.determinize(dataset)
        mask = np.zeros(len(y), bool)
        for label in self.user_split:
            # print(f"{label}\n{y}")
            mask |= (y == label)
        return [mask, ~mask]
    def predict(self, features):
        return super().predict(features)
    def predict_multi(self, x, ind):
        return super().predict_multi(x, ind)
    def print_c(self):
        return super().print_c()
    def print_dot(self, variables=None, category_names=None):
        return super().print_dot(variables, category_names)
    def print_vhdl(self):
        return super().print_vhdl()
    def to_json_dict(self, **kwargs):
        return super().to_json_dict(**kwargs)