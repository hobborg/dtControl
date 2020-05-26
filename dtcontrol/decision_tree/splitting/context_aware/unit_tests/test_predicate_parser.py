import unittest
from dtcontrol.decision_tree.splitting.context_aware.weinhuber_approach_splitting_strategy import PredicateParser
from dtcontrol.decision_tree.splitting.context_aware.weinhuber_approach_split import WeinhuberApproachSplit
import os
import sympy
import random


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
                                        |   23 * 123 = {1,2,3}
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

        """
        # Useful / correct predicates
        test_input_file1 = open("../input_data/test_file1.txt", "w+")
        test_input_file1.write(
            "x_0+11*x_2-30.5*x_1  <= (-Inf, Inf)\n11*x_2-30*x_1 >= (0,1) ∪ [12, 15]\n11*x_0-28.86-pi != [0,1)\n11*x_2-28.86-pi < {1,2,3,4,5,6} ∪ {6,7,8}\n11*x_2**x_1-28.86*x_2-pi > {1,2,3,4,5,6} ∪ {6,7,8} ∪ [12, 15]\nx_2 = {1,2} ∪ (12, 15]\npi = {1}")
        test_input_file1.close()

        # No / wrong usage of variables
        test_input_file2 = open("../input_data/test_file2.txt", "w+")
        test_input_file2.write(
            "x1 = [12,123]\nx__!23 * 123 = {1,2,3}\n12*pi >= [1,2]\nx+11*x_2-30.5*x_1  <= (-Inf, Inf)\n11*x_ 2-30*x_1 >= (0,1) ∪ [12, 15]\n11*x _0-28.86-pi != [0,1)\n11*_2-28.86-pi < {1,2,3,4,5,6} ∪ {6,7,8}\n11*x__2**x_1-28.86*xx_2-pi > {1,2,3,4,5,6} ∪ {6,7,8} ∪ [12, 15]\ny_2 = {1,2} ∪ (12, 15]\n12*pi >= {1}\n23 * 123 = {1,2,3}")
        test_input_file2.close()

        # General typos
        test_input_file3 = open("../input_data/test_file3.txt", "w+")
        test_input_file3.write(
            "sqrqasdasdaserrt(2)*x_12 != {123}\nf(x_2) >= [21, 22]\ng(f(sqrt(x_123))) < {1,23}\n sqrt(x_1 = {123}\nsqrrrt(2)*x_12 != {123}\nlöög(10)*x_0 - x_1 < {13}"
        )
        test_input_file3.close()

        # Invalid relations
        test_input_file4 = open("../input_data/test_file4.txt", "w+")
        test_input_file4.write(
            "12*x_1*pi ? {1}\n 2 / x_0 =9 {1,2}\nx_1 [1,9)\nx_12 = x_2137\n1233\nsqrt(123) = \n 2123*x_12 / x_120+132 >9 {1,22,33}\n29/x_9 + 781 <$! [1,9)\n x_2 + x_2 +x_3 / x_0 >=9 {1,2}\nx_1 !ja= [1,9)"
        )
        test_input_file4.close()

        # valid open intervals
        test_input_file5 = open("../input_data/test_file5.txt", "w+")
        test_input_file5.write(
            "x_1 = (-10, 100)\nx_1 = (20.231313, 123)\nx_1 =(123, 200)\nx_1 = (0.000013, 0.0015)\nx_1 =(-Inf, 0.000013)\nx_1 =(-INF, inf)\nx_1 =(90909, Inf)"
        )
        test_input_file5.close()

        # invalid open intervals
        test_input_file6 = open("../input_data/test_file6.txt", "w+")
        test_input_file6.write(
            "x_1 = -10, 100)\nx_1 = (,20.231313, 123)\nx_1 =(12as3,s 200)\nx_1 = s(0.000013, 0.0015d)\nx_1 =(x_1-Inf, 0.000013!)\nx_1 =(-INF, inf#\nx_1 =((99090909, Inf)\nx_1 =(99090909, Inf))\n12*pi*x_1 >= (1,1)\n12*pi*x_1 >= (1,x_0)\n12*pi*x_1 >= (1,)\n12*pi*x_1 >= )\n12*pi*x_1 >= (((1,1)))"
        )
        test_input_file6.close()

        # valid closed intervals
        test_input_file7 = open("../input_data/test_file7.txt", "w+")
        test_input_file7.write(
            "x_1 = [-10, 100]\nx_1 = [20.231313, 123]\nx_1 =[123, 200]\nx_1 = [0.000013, 0.0015]\nx_1 =[-Inf, 0.000013]\nx_1 =[-INF, inf]\nx_1 =[90909, Inf]"
        )
        test_input_file7.close()

        # invalid closed intervals
        test_input_file8 = open("../input_data/test_file8.txt", "w+")
        test_input_file8.write(
            "x_1 = -10, 100]\nx_1 = [,20.231313, 123]\nx_1 =[12as3,s 200]\nx_1 = s[0.000013, 0.0015d]\nx_1 =[x_1-Inf, 0.000013!]\nx_1 =[-INF, inf#\nx_1 =[[99090909, Inf]\nx_1 =[99090909, Inf]]\n12*pi*x_1 >= [,-1]\n12*pi*x_1 >= [1,x_0]\n12*pi*x_1 >= [1,]\n12*pi*x_1 >= ]\n12*pi*x_1 >= [[[1,1]]]"
        )
        test_input_file8.close()

        # valid closed and open intervals
        test_input_file9 = open("../input_data/test_file9.txt", "w+")
        test_input_file9.write(
            "x_1 = (-10, 100]\nx_1 = [20.231313, 123)\nx_1 =(123, 200]\nx_1 = [0.000013, 0.0015)\nx_1 =(-Inf, 0.000013]\nx_1 =[-INF, inf)\nx_1 =(90909, Inf]"
        )
        test_input_file9.close()

        # invalid closed and open intervals
        test_input_file10 = open("../input_data/test_file10.txt", "w+")
        test_input_file10.write(
            "x_1 = (y-10, 100]\nx_1 = (,20.231313, 123]\nx_1 =[12as3,s 200)\nx_1 = s(0.000013, 0.0015d]\nx_1 =(x_1-Inf, 0.000013!]\nx_1 =(-INF, inf&]\nx_1 =[(99090909, Inf]\nx_1 =(99090909, Inf]]\n12*pi*x_1 >= (,-1]\n12*pi*x_1 >= (1,x_0]\n12*pi*x_1 >= (1,]\n12*pi*x_1 >= [)\n12*pi*x_1 >= [[(1,1]])\nx_1 = (1,1]"
        )
        test_input_file10.close()

        # valid finite intervals
        test_input_file11 = open("../input_data/test_file11.txt", "w+")
        test_input_file11.write(
            "x_1 = {1233.123, sqrt(2), 123213}\nx_1 = {log(12), sqrt(2), 123213}\nx_12 = {1,2,3,4,5,6,7,8,9,1,2,3,4,5,6,7,8}"
        )
        test_input_file11.close()

        # invalid finite intervals
        test_input_file12 = open("../input_data/test_file12.txt", "w+")
        test_input_file12.write(
            "x_1 = {1233.123,, x_0*sqrt(2), 123213}\nx_1 = {log12), sqrt(2),!§ 123213}\nx_12 = {1,{2},{3},4,5,6,x_0,8,9,1,2,3,4,5,6,7,8}\nx_12 = {1x_0}\nx_12 = {1,{2},{3},BAUM)\n12*pi*x_1 >= {1,Inf,x_0\n12*pi*x_1 >= 8{12}\n12*pi*x_1 >= {(,-}1\n12*pi*x_1 >= {1 2 3 }"
        )
        test_input_file12.close()

        # Valid union intervals
        test_input_file13 = open("../input_data/test_file13.txt", "w+")
        test_input_file13.write(
            "x_1 = {1233.123, sqrt(2), 123213} or (1,2) or (3,4) u [9,10) u (12,9999] OR (-1,0) Or {-1,-2,-3,-4}\nx_1 = {12313} OR {1313,2323} u {log(12), sqrt(2), 123213}\nx_12 = {1,2,3,4,5,6,7,8,9,1,2,3,4,5,6,7,8} u {1,2,3,4,5}\n12*pi*x_1 >= [1,5] or (-1,2) Or {-10,-11,123.4}"
        )
        test_input_file13.close()

        # invalid union intervals
        test_input_file14 = open("../input_data/test_file14.txt", "w+")
        test_input_file14.write(
            "x_1 = {1233.123,, x_0*sqrt(2), 123213Or } or {123}\nx_1 = [123,1234] or {log12), sqrt(2),!§ 123213}\nx_12 = {1,2} or {1,{2},{3},4,5,6,x_0,8,9,1,2,3,4,5,6,7,8}\nx_12 = (1,9) or {1x_0}\nx_12 = (8,9] or {1,{2},{3},BAUM)\n12*pi*x_1 >= [1 x_0 5] or -1,2) Or [-10,-11),123.4}"
        )
        test_input_file14.close()

    @classmethod
    def tearDownClass(cls):
        # Deleting test input files after usage
        for i in range(14):
            os.unlink(f"../input_data/test_file{i + 1}.txt")

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
        # Invalid relations
        self.assertEqual(PredicateParser.parse_user_predicate(input_file_path="../input_data/test_file4.txt"), None)

    def test_parse_user_interval_open(self):
        # USAGE OF FILE 5
        # Valid open intervals
        output = [obj.interval for obj in
                  PredicateParser.parse_user_predicate(input_file_path="../input_data/test_file5.txt")]
        self.assertEqual(output, [sympy.Interval.open(-10.0000, 100.000),
                                  sympy.Interval.open(20.231313, 123.000),
                                  sympy.Interval.open(123.000, 200.000),
                                  sympy.Interval.open(0.0000130000, 0.00150000),
                                  sympy.Interval.open(sympy.sympify("-oo"), 0.0000130000),
                                  sympy.Interval(sympy.sympify("-oo"), sympy.sympify("oo")),
                                  sympy.Interval.open(90909, sympy.sympify("oo"))])

        # Random input checker
        for i in range(100):
            a = random.randint(-1000000000, 1000000000)
            b = random.randint(-1000000000, 1000000000)
            if a != b:
                interval = PredicateParser.parse_user_interval(f"({min(a, b)},{max(a, b)})")
                interval_sym = sympy.Interval.open(min(a, b), max(a, b))
                self.assertEqual(interval, interval_sym)
                self.assertFalse(interval.contains(a))
                self.assertFalse(interval.contains(b))
                self.assertTrue(interval.contains((a + b) / 2))

        # USAGE OF FILE 6
        # Invalid intervals
        self.assertEqual(PredicateParser.parse_user_predicate(input_file_path="../input_data/test_file6.txt"),
                         None)

    def test_parse_user_interval_close(self):
        # USAGE OF FILE 7
        # Valid closed intervals
        output = [obj.interval for obj in
                  PredicateParser.parse_user_predicate(input_file_path="../input_data/test_file7.txt")]
        self.assertEqual(output, [sympy.Interval(-10.0000, 100.000),
                                  sympy.Interval(20.231313, 123.000),
                                  sympy.Interval(123.000, 200.000),
                                  sympy.Interval(0.0000130000, 0.00150000),
                                  sympy.Interval(sympy.sympify("-oo"), 0.0000130000),
                                  sympy.Interval(sympy.sympify("-oo"), sympy.sympify("oo")),
                                  sympy.Interval(90909, sympy.sympify("oo"))])

        # Random input checker
        for i in range(100):
            a = random.randint(-1000000000, 1000000000)
            b = random.randint(-1000000000, 1000000000)
            if a != b:
                interval = PredicateParser.parse_user_interval(f"[{min(a, b)},{max(a, b)}]")
                interval_sym = sympy.Interval(min(a, b), max(a, b))
                self.assertEqual(interval, interval_sym)
                self.assertTrue(interval.contains(a))
                self.assertTrue(interval.contains(b))
                self.assertTrue(interval.contains((a + b) / 2))

        # USAGE OF FILE 8
        # Invalid closed intervals
        self.assertEqual(PredicateParser.parse_user_predicate(input_file_path="../input_data/test_file8.txt"),
                         None)

    def test_parse_user_interval_open_and_close(self):
        # USAGE OF FILE 9
        # Valid intervals
        output = [obj.interval for obj in
                  PredicateParser.parse_user_predicate(input_file_path="../input_data/test_file9.txt")]
        self.assertEqual(output, [sympy.Interval.Lopen(-10.0000, 100.000),
                                  sympy.Interval.Ropen(20.231313, 123.000),
                                  sympy.Interval.Lopen(123.000, 200.000),
                                  sympy.Interval.Ropen(0.0000130000, 0.00150000),
                                  sympy.Interval(sympy.sympify("-oo"), 0.0000130000),
                                  sympy.Interval(sympy.sympify("-oo"), sympy.sympify("oo")),
                                  sympy.Interval.open(90909, sympy.sympify("oo"))])

        # USAGE OF FILE 10
        # Invalid intervals
        # KNOWN BUG (or Feature??) -> (0, inf#) would evaluate to (0,inf) but '#' seems to be the only special character where that works
        self.assertEqual(PredicateParser.parse_user_predicate(input_file_path="../input_data/test_file10.txt"),
                         None)

    def test_parse_user_interval_finite(self):
        # USAGE OF FILE 11
        # Valid finite intervals
        output = [obj.interval for obj in
                  PredicateParser.parse_user_predicate(input_file_path="../input_data/test_file11.txt")]
        self.assertEqual(output, [sympy.FiniteSet(sympy.sympify("sqrt(2)").evalf(), 1233.123, 123213.0),
                                  sympy.FiniteSet(sympy.sympify("sqrt(2)").evalf(), sympy.sympify("log(12)").evalf(),
                                                  123213.0),
                                  sympy.FiniteSet(1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0)])

        # USAGE OF FILE 12
        # Invalid intervals
        self.assertEqual(PredicateParser.parse_user_predicate(input_file_path="../input_data/test_file12.txt"),
                         None)

    def test_parse_user_interval_union(self):
        # USAGE OF FILE 13
        # Valid union intervals
        output = [obj.interval for obj in
                  PredicateParser.parse_user_predicate(input_file_path="../input_data/test_file13.txt")]
        self.assertEqual(output, [sympy.Union(sympy.FiniteSet(-4, -3, -2, 123213), sympy.Interval.Ropen(-1, 0),
                                        sympy.Interval.open(1, 2),
                                        sympy.Interval.open(3, 4),
                                        sympy.Interval.Ropen(9, 10),
                                        sympy.Interval.Lopen(12, 9999)),
                                  sympy.FiniteSet(sympy.sympify("sqrt(2)").evalf(), sympy.sympify("log(12)").evalf(), 1313, 2323, 12313.0, 123213.0),
                                  sympy.FiniteSet(1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0),
                                  sympy.Union(sympy.FiniteSet(-11.0, -10.0, 123.4), sympy.Interval.Lopen(-1.00000000000000, 5.00000000000000))])

        # USAGE OF FILE 14
        # Invalid union intervals
        output = [obj.interval for obj in
                  PredicateParser.parse_user_predicate(input_file_path="../input_data/test_file14.txt")]
        self.assertEqual(output,[sympy.FiniteSet(123.0), sympy.Interval.Lopen(8, 9)])


if __name__ == '__main__':
    unittest.main()

# TODO: add to the other tests values like sqrt(2), log(2) , sqrt(12381239+12313) + log(1239) etc ...
