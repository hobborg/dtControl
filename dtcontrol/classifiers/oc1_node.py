import dtcontrol.util
from dtcontrol.classifiers.custom_dt import Node
import numpy as np

class OC1Node(Node):
    def __init__(self, coeff, intercept, depth=0):
        super().__init__(depth)
        self.coeff = coeff
        self.intercept = intercept
        self.classifier = None

    def test_condition(self, x):
        """
        :param x: [row of X_train]; shape (1, num_features)
        :return true if go left
        """
        return np.dot(x.flatten(), np.array(self.coeff)) + self.intercept <= 0

    def create_child_node(self):
        pass

    def find_split(self, X, y):
        pass

    def get_dot_label(self):
        if self.actual_label is not None:
            rounded = dtcontrol.util.objround(self.actual_label, 6)  # TODO get precision from flag?
            return dtcontrol.util.split_into_lines(rounded)
        else:
            line = []
            for i in range(len(self.coeff)):
                line.append(f"{round(self.coeff[i], 6)}*X[{i}]")  # TODO get precision from flag?
            line.append(f"{round(self.intercept, 6)}")  # TODO get precision from flag?
            hyperplane = "\n+".join(line) + " <= 0"
            return hyperplane.replace('+-', '-')

    def print_dot_red(self):
        pass

    def is_axis_aligned(self):
        return False
