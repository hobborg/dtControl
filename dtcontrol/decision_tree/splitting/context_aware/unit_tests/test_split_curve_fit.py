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

    @classmethod
    def setUpClass(cls):
        """
        Creating all the split objects to perform these tests on.
        Split 1:
            column_interval: {x_0: Interval(-oo, oo), x_1: Interval(-oo, oo), x_2: Interval(-oo, oo), x_3: Interval(-oo, oo)}
            coef_interval: {c_4: Interval(-oo, oo), c_1: Interval(-oo, oo), c_3: Interval(-oo, oo), c_0: Interval(-oo, oo), c_2: Interval(-oo, oo)}
            term: c_0*x_0 + c_1*x_1 + c_2*x_2 + c_3*x_3 + c_4
            relation: <=

        Split 2:

        Split 3:

        Split 4:

        Split 5:

        Split 6:

        Split 7:

        Split 8:

        Split 9:

        """
        x_0, x_1, x_2, x_3, x_4, x_5, c_0, c_1, c_2, c_3, c_4, c_5 = sp.symbols('x_0 x_1 x_2 x_3 x_4 x_5 c_0 c_1 c_2 c_3 c_4 c_5')
        column_interval1 = {x_0: sp.Interval(sp.S.NegativeInfinity, sp.S.Infinity), x_1: sp.Interval(sp.S.NegativeInfinity, sp.S.Infinity),
                            x_2: sp.Interval(sp.S.NegativeInfinity, sp.S.Infinity), x_3: sp.Interval(sp.S.NegativeInfinity, sp.S.Infinity)}
        coef_interval1 = {c_4: sp.Interval(sp.S.NegativeInfinity, sp.S.Infinity), c_1: sp.Interval(sp.S.NegativeInfinity, sp.S.Infinity),
                          c_3: sp.Interval(sp.S.NegativeInfinity, sp.S.Infinity), c_0: sp.Interval(sp.S.NegativeInfinity, sp.S.Infinity),
                          c_2: sp.Interval(sp.S.NegativeInfinity, sp.S.Infinity)}
        term1 = c_0 * x_0 + c_1 * x_1 + c_2 * x_2 + c_3 * x_3 + c_4
        relation1 = "<="
        cls.Split1 = WeinhuberApproachSplit(column_interval1, coef_interval1, term1, relation1)

    def test_fit_edge_cases(self):
        split = deepcopy(self.Split1)
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
