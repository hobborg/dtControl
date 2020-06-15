import unittest
from hypothesis import given
import sympy as sp
from dtcontrol.decision_tree.splitting.context_aware.weinhuber_approach_split import WeinhuberApproachSplit
from copy import deepcopy
import numpy as np


class TestSplitCurveFit(unittest.TestCase):
    """
    Test cases for fit() inside WeinhuberApproachSplit Objects (weinhuber_approach_split.py)
    """
    data_x_1 = np.array(
        [[1., 4.6, 1., 3.],
         [1., 4.6, 2., 3.],
         [2., 4., 3., 1.],
         [2., 4., 3., 2.],
         [1., 4., 4., 1.],
         [2., 4., 4., 2.],
         [2., 53., 2., 3.],
         [1., 228., 1., 5.],
         [2., 93., 1., 2.],
         [2., 59., 3., 2.]])
    data_y_1 = np.array([-1, -1, 1, 1, 1, 1, -1, -1, -1, 1])

    data_x_2 = np.array(
        [[2., 4., 3., 1.],
         [2., 4., 3., 2.],
         [1., 4., 4., 1.],
         [2., 4., 4., 2.],
         [2., 59., 3., 2.]])
    data_y_2 = np.array([1, 1, 1, 1, -1])

    data_x_3 = np.array(
        [[1., 4.6, 1., 3.],
         [1., 4.6, 2., 3.],
         [2., 53., 2., 3.],
         [1., 228., 1., 5.],
         [2., 93., 1., 2.]])
    data_y_3 = np.array([1, 1, -1, -1, -1])

    x_0, x_1, x_2, x_3, x_4, x_5, c_0, c_1, c_2, c_3, c_4, c_5 = sp.symbols('x_0 x_1 x_2 x_3 x_4 x_5 c_0 c_1 c_2 c_3 c_4 c_5')

    # Split 1
    column_interval1 = {x_0: sp.Interval(sp.S.NegativeInfinity, sp.S.Infinity), x_1: sp.Interval(sp.S.NegativeInfinity, sp.S.Infinity),
                        x_2: sp.Interval(sp.S.NegativeInfinity, sp.S.Infinity), x_3: sp.Interval(sp.S.NegativeInfinity, sp.S.Infinity)}
    coef_interval1 = {c_4: sp.Interval(sp.S.NegativeInfinity, sp.S.Infinity), c_1: sp.Interval(sp.S.NegativeInfinity, sp.S.Infinity),
                      c_3: sp.Interval(sp.S.NegativeInfinity, sp.S.Infinity), c_0: sp.Interval(sp.S.NegativeInfinity, sp.S.Infinity),
                      c_2: sp.Interval(sp.S.NegativeInfinity, sp.S.Infinity)}
    term1 = c_0 * x_0 + c_1 * x_1 + c_2 * x_2 + c_3 * x_3 + c_4
    relation1 = "<="
    split1 = WeinhuberApproachSplit(column_interval1, coef_interval1, term1, relation1)

    def helper_fit(self, split, x, y):
        copy_split = deepcopy(split)
        copy_split.fit([], x, y)
        return copy_split.coef_assignment

    def test_linear_fit(self):
        c_0, c_1, c_2, c_3, c_4, c_5 = sp.symbols('c_0 c_1 c_2 c_3 c_4 c_5')

        coef_assignment_1 = {c_4: -1.5064260304162935, c_1: 0.0033307416540457155, c_0: 0.1720000986661053, c_2: 0.7146818999152404,
                             c_3: -0.26526052933093897}
        self.assertEqual(self.helper_fit(deepcopy(self.split1), self.data_x_1, self.data_y_1), coef_assignment_1)

        coef_assignment_2 = {c_4: 1.1454545454692278, c_0: -2.1651569426239803e-12, c_1: -0.03636363636362639, c_2: -2.1822543772032077e-12,
                             c_3: -2.1969093211282598e-12}
        self.assertEqual(self.helper_fit(deepcopy(self.split1), self.data_x_2, self.data_y_2), coef_assignment_2)

        coef_assignment_3 = {c_4: 3.5023071852310514, c_1: -0.006591957811487801, c_0: -1.6809492419229106, c_3: -0.26367831245735257,
                             c_2: -2.1596058275008545e-12}
        self.assertEqual(self.helper_fit(deepcopy(self.split1), self.data_x_3, self.data_y_3), coef_assignment_3)

    def test_fit_edge_cases(self):
        split = deepcopy(self.split1)
        # Invalid argument types
        self.assertIsNone(split.fit([], [], []))
        self.assertIsNone(split.fit([],
                                    [[1., 4.6, 1., 3.],
                                     [1., 4.6, 2., 3.],
                                     [2., 4., 3., 1.],
                                     [2., 4., 3., 2.],
                                     [1., 4., 4., 1.],
                                     [2., 4., 4., 2.],
                                     [2., 53., 2., 3.],
                                     [1., 228., 1., 5.],
                                     [2., 93., 1., 2.],
                                     [2., 59., 3., 2.]], np.array([1, 1, -1, -1, -1, -1, -1, -1, -1, -1])))

        self.assertIsNone(split.fit([], np.array(
            [[1., 4.6, 1., 3.],
             [1., 4.6, 2., 3.],
             [2., 4., 3., 1.],
             [2., 4., 3., 2.],
             [1., 4., 4., 1.],
             [2., 4., 4., 2.],
             [2., 53., 2., 3.],
             [1., 228., 1., 5.],
             [2., 93., 1., 2.],
             [2., 59., 3., 2.]]), [1, 1, -1, -1, -1, -1, -1, -1, -1, -1]))

        # Invalid shapes (x rows > y column)
        self.assertIsNone(split.fit([], np.array(
            [[1., 4.6, 1., 3.],
             [1., 4.6, 2., 3.],
             [2., 4., 3., 1.],
             [2., 4., 3., 2.],
             [1., 4., 4., 1.],
             [2., 4., 4., 2.],
             [2., 53., 2., 3.],
             [1., 228., 1., 5.],
             [2., 93., 1., 2.]]), np.array([1, 1, -1, -1, -1, -1, -1, -1, -1, -1])))

        # Invalid shapes (x rows < y column)
        self.assertIsNone(split.fit([], np.array(
            [[1., 4.6, 1., 3.],
             [1., 4.6, 2., 3.],
             [2., 4., 3., 1.],
             [2., 4., 3., 2.],
             [1., 4., 4., 1.],
             [2., 4., 4., 2.],
             [2., 53., 2., 3.],
             [1., 228., 1., 5.],
             [2., 93., 1., 2.],
             [2., 59., 3., 2.]]), np.array([1, 1, -1, -1, -1, -1, -1, -1, -1])))

        # Invalid shapes (x rows > y column)
        self.assertIsNone(split.fit([], np.array(
            [[1., 4.6, 1., 3.],
             [1., 4.6, 2., 3.],
             [1., 4.6, 1., 5.],
             [2., 4., 3., 1.],
             [2., 4., 3., 2.],
             [1., 4., 4., 1.],
             [2., 4., 4., 2.],
             [2., 53., 2., 3.],
             [1., 228., 1., 5.],
             [2., 93., 1., 2.],
             [2., 59., 3., 2.]]), np.array([1, 1, -1, -1, -1, -1, -1, -1, -1, -1])))

        # all coefs already fixed
        c_0, c_1, c_2, c_3, c_4, c_5 = sp.symbols('c_0 c_1 c_2 c_3 c_4 c_5')
        self.assertIsNone(split.fit([(c_1, 1), (c_2, -3), (c_0, -3), (c_3, -3), (c_4, -3)], np.array(
            [[1., 4.6, 1., 3.],
             [1., 4.6, 2., 3.],
             [2., 4., 3., 1.],
             [2., 4., 3., 2.],
             [1., 4., 4., 1.],
             [2., 4., 4., 2.],
             [2., 53., 2., 3.],
             [1., 228., 1., 5.],
             [2., 93., 1., 2.],
             [2., 59., 3., 2.]]), np.array([1, 1, -1, -1, -1, -1, -1, -1, -1, -1])))

        # Too many fixed coefs
        self.assertIsNone(split.fit([(c_1, 1), (c_2, -3), (c_0, -3), (c_3, -3), (c_4, -3), (c_5, 0)], np.array(
            [[1., 4.6, 1., 3.],
             [1., 4.6, 2., 3.],
             [2., 4., 3., 1.],
             [2., 4., 3., 2.],
             [1., 4., 4., 1.],
             [2., 4., 4., 2.],
             [2., 53., 2., 3.],
             [1., 228., 1., 5.],
             [2., 93., 1., 2.],
             [2., 59., 3., 2.]]), np.array([1, 1, -1, -1, -1, -1, -1, -1, -1, -1])))

        # Invalid attribute configuration
        split.coef_interval = None
        self.assertIsNone(split.fit([], np.array(
            [[1., 4.6, 1., 3.],
             [1., 4.6, 2., 3.],
             [2., 4., 3., 1.],
             [2., 4., 3., 2.],
             [1., 4., 4., 1.],
             [2., 4., 4., 2.],
             [2., 53., 2., 3.],
             [1., 228., 1., 5.],
             [2., 93., 1., 2.],
             [2., 59., 3., 2.]]), np.array([1, 1, -1, -1, -1, -1, -1, -1, -1, -1])))


if __name__ == '__main__':
    unittest.main()
