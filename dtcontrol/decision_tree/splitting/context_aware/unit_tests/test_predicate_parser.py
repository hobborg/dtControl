import unittest
from dtcontrol.decision_tree.splitting.context_aware.weinhuber_approach_splitting_strategy import PredicateParser
from dtcontrol.decision_tree.splitting.context_aware.weinhuber_approach_split import WeinhuberApproachSplit
import os

class TestPredicateParser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Creating test input files
        test_input_file1 = open("../test_input_file_1.txt", "w+")
        test_input_file1.write(
            "11*x_2-30.5  <= $i\n11*x_2-30 <= (0,1) ∪ [12, 15]\n11*x_2-28.86-pi <= [0,1)\n11*x_2-28.86-pi > {1,2,3,4,5,6} ∪ {6,7,8}\n11*x_2-28.86-pi > {1,2,3,4,5,6} ∪ {6,7,8} ∪ [12, 15]")
        test_input_file1.close()

    @classmethod
    def tearDownClass(cls):
        # Deleting test input files

        os.unlink("../test_input_file_1.txt")

    def test_parse_user_predicate(self):
        # Non existing input file
        self.assertEqual(PredicateParser.parse_user_predicate(input_file_path="None"), None)
        # Check if test input file 1 was parsed correctly
        output = PredicateParser.parse_user_predicate(input_file_path="dtcontrol/decision_tree/splitting/context_aware/unit_tests/test_input_file_1.txt")
        print(output)
        # for obj in output:
        #     self.assertIsInstance(obj, WeinhuberApproachSplit)
        #
        # output_var = [obj.variables for obj in output]
        # self.assertEqual(output_var,['2','2','2','2','2'] )



if __name__ == '__main__':
    unittest.main()
