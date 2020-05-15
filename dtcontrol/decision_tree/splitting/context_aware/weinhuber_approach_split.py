from dtcontrol.decision_tree.splitting.context_aware.context_aware_split import ContextAwareSplit
import numpy as np
import sympy as sp

class WeinhuberApproachSplit(ContextAwareSplit):

    def predict(self, features):
        subs_list = []

        # Iterating over every possible value and creating a substitution list
        for i in range(len(features[0, :])):
            subs_list.append(("x_" + str(i), features[0, i]))
        result = self.predicate.subs(subs_list)
        result = result.evalf()
        print(result)

        # Checking the result
        if self.relation == "<=":
            check = sp.sympify(result, "<=" ,self.result)
        elif self.relation == ">=":
            check = sp.sympify(result, ">=" ,self.result)
        elif self.relation == "!=":
            check = sp.sympify(result, "!=" ,self.result)
        elif self.relation == ">":
            check = sp.sympify(result, ">" ,self.result)
        elif self.relation == "<":
            check = sp.sympify(result, "<" ,self.result)
        else:
            check = sp.sympify(result, "==" ,self.result)

        if check:
            return 0
        else:
            return 1

    def get_masks(self, dataset):
        data = dataset.get_numeric_x()
        mask = []

        # Using the predict function and iterating over row
        for i in range(np.shape(dataset.get_numeric_x())[0]):
            tmp1 = self.predict(np.array([data[i, :]]))
            if tmp1 == 0:
                mask.append(True)
            else:
                mask.append(False)
        mask = np.array(mask)
        return [mask, ~mask]

    def print_dot(self, variables=None, category_names=None):
        return sp.pretty(self.predicate) + "\\n " + self.relation + " " + sp.pretty(self.result)

    def print_c(self):
        return self.print_dot()

    def print_vhdl(self):
        return self.print_dot()

