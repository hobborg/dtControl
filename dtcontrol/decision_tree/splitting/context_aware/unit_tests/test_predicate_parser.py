import unittest
from dtcontrol.decision_tree.splitting.context_aware.weinhuber_approach_splitting_strategy import PredicateParser
from dtcontrol.decision_tree.splitting.context_aware.weinhuber_approach_split import WeinhuberApproachSplit
import os
import sympy

class TestPredicateParser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Creating test input files
        test_input_file1 = open("../input_data/test_file1.txt", "w+")
        test_input_file1.write(
            "x_0+11*x_2-30.5*x_1  <= $i\n11*x_2-30*x_1 >= (0,1) ∪ [12, 15]\n11*x_0-28.86-pi != [0,1)\n11*x_2-28.86-pi < {1,2,3,4,5,6} ∪ {6,7,8}\n11*x_2**x_1-28.86*x_2-pi > {1,2,3,4,5,6} ∪ {6,7,8} ∪ [12, 15]\nx_2 = {1,2} ∪ (12, 15]\npi = {1}")
        test_input_file1.close()

    @classmethod
    def tearDownClass(cls):
        # Deleting test input files
        os.unlink("../input_data/test_file1.txt")



    def test_parse_user_predicate(self):
        # Non existing input file
        self.assertEqual(PredicateParser.parse_user_predicate(input_file_path="None"), None)
        # Check if test input file 1 was parsed correctly
        output = PredicateParser.parse_user_predicate(input_file_path="../input_data/test_file1.txt")
        # Checking right instance
        for obj in output:
            self.assertIsInstance(obj, WeinhuberApproachSplit)
        # Checking right vars
        output_var = [obj.variables for obj in output]
        self.assertEqual(output_var,[['0', '1', '2'], ['1', '2'], ['0'], ['2'], ['1', '2'], ['2']])
        # Checking right predicate type
        output_pred = [obj.predicate for obj in output]
        for obj in output_pred:
            self.assertIsInstance(obj, sympy.Basic)
        # Checking right predicates

        self.assertEqual(output_pred, [x_0 - 30.5*x_1 + 11*x_2,-30*x_1 + 11*x_2,11*x_0 - 28.86 - pi,11*x_2 - 28.86 - pi,-28.86*x_2 + 11*x_2**x_1 - pi,x_2])

#TODO: no interval given
#TODO: predicate uses no variables x_
if __name__ == '__main__':
    unittest.main()
