import unittest
from dtcontrol.decision_tree.splitting.context_aware.weinhuber_approach_splitting_strategy import PredicateParser
from dtcontrol.decision_tree.splitting.context_aware.weinhuber_approach_split import WeinhuberApproachSplit
import os
import sympy


class TestPredicateParser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Creating test input files (general)
        test_input_file1 = open("../input_data/test_file1.txt", "w+")
        test_input_file1.write(
            "x_0+11*x_2-30.5*x_1  <= $i\n11*x_2-30*x_1 >= (0,1) ∪ [12, 15]\n11*x_0-28.86-pi != [0,1)\n11*x_2-28.86-pi < {1,2,3,4,5,6} ∪ {6,7,8}\n11*x_2**x_1-28.86*x_2-pi > {1,2,3,4,5,6} ∪ {6,7,8} ∪ [12, 15]\nx_2 = {1,2} ∪ (12, 15]\npi = {1}")
        test_input_file1.close()

        # Creating test input files (wrong variables only)
        test_input_file2 = open("../input_data/test_file2.txt", "w+")
        test_input_file2.write(
            "x+11*x_2-30.5*x_1  <= $i\n11*x_ 2-30*x_1 >= (0,1) ∪ [12, 15]\n11*x _0-28.86-pi != [0,1)\n11*_2-28.86-pi < {1,2,3,4,5,6} ∪ {6,7,8}\n11*x__2**x_1-28.86*xx_2-pi > {1,2,3,4,5,6} ∪ {6,7,8} ∪ [12, 15]\ny_2 = {1,2} ∪ (12, 15]")
        test_input_file2.close()

        # test_input_file2 = open("../input_data/test_file2.txt", "w+")
        # test_input_file2.write(
        #    "<= $i\nBaum*x_1 >= (0,1) ∪ [12, 15]\n11*dx0-dds28.a86-!pi != [0,1)\n11*x_2-28.86-pi < {1,2,3,4,5,6} ∪ {6,7,8}\n11*x_2**x_1-28.86*x_2-pi > {1,2,3,4,5,6} ∪ {6,7,8} ∪ [12, 15]\nx_2 = {1,2} ∪ (12, 15]\npi = {1}x_0+11*x_2-30.5*x_1  <= $i\n11*x_2-30*x_1 >= (0,1) ∪ [12, 15]\n11*x_0-28.86-pi != [-10,-12)\n11*x_2-28.86-pi < ∪ {6,7,8}\n11*x_2**x_1-28.86*x_2-pi > \nx_2 = {1,2}15]\npi*x_!%$ {1}\npi*x_! = \n[12,213]\npi*x_1 = [2231;23]\npi*x_3 = {2:3<= $i\nBaum*x_1 >=asd (0,1) ∪ [12, 15\n11222*dx0-dds28.a86-!pi != s0,1)\n11*x_2df-28.d86-pi <# {1,fsa2,3,4,5,6}  {13as6,7,8}\n11*x_2-30*x_1 >= (0,1) ∪ [12, 15] 113*sqrt(2)*pi*x_3 >= (-10,1.213)")
        # test_input_file2.close()

    @classmethod
    def tearDownClass(cls):
        # Deleting test input files
        os.unlink("../input_data/test_file1.txt")
        os.unlink("../input_data/test_file2.txt")

    def test_parse_user_predicate_file1(self):

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

    def test_parse_user_predicate_file2(self):
        # Wrong variables only dataset
        self.assertEqual(PredicateParser.parse_user_predicate(input_file_path="../input_data/test_file2.txt"), None)


if __name__ == '__main__':
    unittest.main()
