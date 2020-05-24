import unittest
from dtcontrol.decision_tree.splitting.context_aware.weinhuber_approach_splitting_strategy import PredicateParser
from dtcontrol.decision_tree.splitting.context_aware.weinhuber_approach_split import WeinhuberApproachSplit
import os
import sympy


class TestPredicateParser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        """

        FILE NAME                       |   BEHAVIOR
        --------------------------------|----------------------------------------
        test_file1.txt                  |   useful /correct predicates
        --------------------------------|----------------------------------------
        test_file2.txt                  |   predicates which do not use dataset
                                        |   -> No /wrong usage of variables
                                        |   e.g.
                                        |   12*pi >= {1}
                                        |   x__!23 * 123 = {1,2,3}
        --------------------------------|----------------------------------------
        test_file3.txt                  |   predicates with general typos or use of unknown functions
                                        |   e.g.
                                        |   sqrrrt(2)*x_12 != {123}
                                        |   löög(10)*x_0 - x_1 < {13}
        --------------------------------|----------------------------------------
        test_file4.txt                  |   only invalid relations
                                        |   e.g.
                                        |   12*x_1*pi ? {1}
                                        |   2 / x_0 =9 {1,2}
                                        |   x_1 [1,9)
        --------------------------------|----------------------------------------
        test_file5.txt                  |   only valid open intervals
                                        |   e.g.
                                        |   12*pi*x_1 >=(-Inf, Inf)
                                        |   12*pi*x_1 >= (1,6)
        --------------------------------|----------------------------------------
        test_file6.txt                  |   only invalid open intervals
                                        |   e.g.
                                        |   12*pi*x_1 >= (1,1)
                                        |   12*pi*x_1 >= (1,x_0)
                                        |   12*pi*x_1 >= (1,)
                                        |   12*pi*x_1 >= )
                                        |   12*pi*x_1 >= (((1,1)))
        --------------------------------|----------------------------------------
        test_file7.txt                  |   only valid closed intervals
                                        |   e.g.
                                        |   12*pi*x_1 >= [-Inf, Inf]
                                        |   12*pi*x_1 >= [2,6]
        --------------------------------|----------------------------------------
        test_file8.txt                  |   only invalid closed intervals
                                        |   e.g.
                                        |   12*pi*x_1 >= [,-1]
                                        |   12*pi*x_1 >= [1,x_0]
                                        |   12*pi*x_1 >= [1,]
                                        |   12*pi*x_1 >= ]
                                        |   12*pi*x_1 >= [[[1,1]]]
        --------------------------------|----------------------------------------
        test_file9.txt                  |   only valid open and closed intervals
                                        |   e.g.
                                        |   12*pi*x_1 >= (-1,1]
                                        |   12*pi*x_1 >= [-1,1)
        --------------------------------|----------------------------------------
        test_file10.txt                 |   only invalid open and closed intervals
                                        |   e.g.
                                        |   12*pi*x_1 >= (,-1]
                                        |   12*pi*x_1 >= (1,x_0]
                                        |   12*pi*x_1 >= (1,]
                                        |   12*pi*x_1 >= [)
                                        |   12*pi*x_1 >= [[(1,1]])
        --------------------------------|----------------------------------------
        test_file11.txt                 |   only valid finite intervals
                                        |   e.g.
                                        |   12*pi*x_1 >= {1,2,3}
        --------------------------------|----------------------------------------
        test_file12.txt                 |   only invalid finite intervals
                                        |   e.g.
                                        |   12*pi*x_1 >= {1,Inf,x_0
                                        |   12*pi*x_1 >= 8{12}
                                        |   12*pi*x_1 >= {(,-}1
                                        |   12*pi*x_1 >= {1 2 3 }
        --------------------------------|----------------------------------------
        test_file13.txt                 |   only valid union intervals
                                        |   e.g.
                                        |   12*pi*x_1 >= [1,5] or (-1,2) Or {-10,-11,123.4}
        --------------------------------|----------------------------------------
        test_file14.txt                 |   only invalid union intervals
                                        |   e.g.
                                        |   12*pi*x_1 >= [1 x_0 5] or -1,2) Or [-10,-11),123.4}
        --------------------------------|----------------------------------------
        test_file15.txt                 |   random collection of invalid intervals
        --------------------------------|----------------------------------------
        test_file16.txt                 |   random collection of valid intervals
        --------------------------------|----------------------------------------

        """

        test_input_file1 = open("../input_data/test_file1.txt", "w+")
        test_input_file1.write(
            "x_0+11*x_2-30.5*x_1  <= (-Inf, Inf)\n11*x_2-30*x_1 >= (0,1) ∪ [12, 15]\n11*x_0-28.86-pi != [0,1)\n11*x_2-28.86-pi < {1,2,3,4,5,6} ∪ {6,7,8}\n11*x_2**x_1-28.86*x_2-pi > {1,2,3,4,5,6} ∪ {6,7,8} ∪ [12, 15]\nx_2 = {1,2} ∪ (12, 15]\npi = {1}")
        test_input_file1.close()

        test_input_file2 = open("../input_data/test_file2.txt", "w+")
        test_input_file2.write(
            "x1 = [12,123]\nx__!23 * 123 = {1,2,3}\n12*pi >= [1,2]\nx+11*x_2-30.5*x_1  <= (-Inf, Inf)\n11*x_ 2-30*x_1 >= (0,1) ∪ [12, 15]\n11*x _0-28.86-pi != [0,1)\n11*_2-28.86-pi < {1,2,3,4,5,6} ∪ {6,7,8}\n11*x__2**x_1-28.86*xx_2-pi > {1,2,3,4,5,6} ∪ {6,7,8} ∪ [12, 15]\ny_2 = {1,2} ∪ (12, 15]")
        test_input_file2.close()

        test_input_file3 = open("../input_data/test_file3.txt", "w+")
        test_input_file3.write(
            "sqrqasdasdaserrt(2)*x_12 != {123}\nf(x_2) >= [21, 22]\ng(f(sqrt(x_123))) < {1,23}\n sqrt(x_1 = {123}"
        )
        test_input_file3.close()

        test_input_file4 = open("../input_data/test_file4.txt", "w+")
        test_input_file4.write(
            "12*x_1*pi ? {1}\n 2 / x_0 =9 {1,2}\nx_1 [1,9)\nx_12 = x_2137\n1233\nsqrt(123) = \n 2123*x_12 / x_120+132 >9 {1,22,33}\n29/x_9 + 781 <$! [1,9)\n x_2 + x_2 +x_3 / x_0 >=9 {1,2}\nx_1 !ja= [1,9)"
        )
        test_input_file4.close()

        test_input_file5 = open("../input_data/test_file5.txt", "w+")
        test_input_file5.write(
            ""
        )
        test_input_file5.close()

    @classmethod
    def tearDownClass(cls):
        # Deleting test input files
        os.unlink("../input_data/test_file1.txt")
        os.unlink("../input_data/test_file2.txt")
        os.unlink("../input_data/test_file3.txt")
        os.unlink("../input_data/test_file4.txt")
        os.unlink("../input_data/test_file5.txt")

    def test_parse_user_predicate_useful_predicates(self):
        # USAGE OF FILE 1

        # Non existing input file
        self.assertEqual(PredicateParser.parse_user_predicate(input_file_path="None"), None)

        # Check if test input file 1 was parsed correctly
        output = PredicateParser.parse_user_predicate(input_file_path="../input_data/test_file1.txt")

        # Checking right instance
        for obj in output:
            self.assertIsInstance(obj, WeinhuberApproachSplit)

        # Checking right vars
        output_var = [obj.variables for obj in output]
        self.assertEqual(output_var, [[0, 1, 2], [1, 2], [0], [2], [1, 2], [2]])

        # Checking right instance
        output_pred = [obj.predicate for obj in output]
        for obj in output_pred:
            self.assertIsInstance(obj, sympy.Basic)

        # Checking if predicates got parsed correctly
        self.assertEqual(output_pred, sympy.sympify(
            ["x_0 - 30.5*x_1 + 11*x_2", "-30*x_1 + 11*x_2", "11*x_0 - 28.86 - pi", "11*x_2 - 28.86 - pi",
             "-28.86*x_2 + 11*x_2**x_1 - pi", "x_2"]))

        # Checking if relation got parsed correctly
        output_relation = [obj.relation for obj in output]
        self.assertEqual(output_relation, ['<=', '>=', '!=', '<', '>', '='])

        # Checking if interval got parsed correctly
        output_interval = [obj.interval for obj in output]
        self.assertEqual(output_interval, [sympy.Interval(sympy.sympify("-oo"), sympy.sympify("oo")),
                                           sympy.Union(sympy.Interval.open(0, 1), sympy.Interval(12, 15)),
                                           sympy.Interval.Ropen(0, 1), sympy.FiniteSet(1, 2, 3, 4, 5, 6, 7, 8),
                                           sympy.Union(sympy.FiniteSet(1, 2, 3, 4, 5, 6, 7, 8), sympy.Interval(12, 15)),
                                           sympy.Union(sympy.FiniteSet(1, 2), sympy.Interval.Lopen(12, 15))])

    def test_parse_user_predicate_wrong_variables(self):
        # USAGE OF FILE 2
        # Wrong variables only dataset
        self.assertEqual(PredicateParser.parse_user_predicate(input_file_path="../input_data/test_file2.txt"), None)

    def test_parse_user_predicate_unknown_functions(self):
        # USAGE OF FILE 3
        # Typos only dataset
        self.assertEqual(PredicateParser.parse_user_predicate(input_file_path="../input_data/test_file3.txt"), None)

    def test_parse_user_predicate_invalid_relations(self):
        # USAGE OF FILE 4
        foo = PredicateParser.parse_user_predicate(input_file_path="../input_data/test_file4.txt")
        self.assertEqual(PredicateParser.parse_user_predicate(input_file_path="../input_data/test_file4.txt"), None)

    def test_parse_user_interval_open(self):
        # USAGE OF FILE 5
        # Valid intervals

        # USAGE OF FILE 6
        # Invalid intervals
        pass

    def test_parse_user_interval_close(self):
        # USAGE OF FILE 7
        # Valid intervals

        # USAGE OF FILE 8
        # Invalid intervals
        pass

    def test_parse_user_interval_open_and_close(self):
        # USAGE OF FILE 9
        # Valid intervals

        # USAGE OF FILE 10
        # Invalid intervals
        pass

    def test_parse_user_interval_finite(self):
        # USAGE OF FILE 11
        # Valid intervals

        # USAGE OF FILE 12
        # Invalid intervals
        pass

    def test_parse_user_interval_union(self):
        # USAGE OF FILE 13
        # Valid intervals

        # USAGE OF FILE 14
        # Invalid intervals
        pass

    def test_parse_user_interval_random_invalid(self):
        # USAGE OF FILE 15
        pass

    def test_parse_user_interval_random_valid(self):
        # USAGE OF FILE 16
        pass


if __name__ == '__main__':
    unittest.main()


# TODO: 12*pi*x_1 >= (1,1] allowed or not?