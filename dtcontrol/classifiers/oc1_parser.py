import ast
import re

from dtcontrol.classifiers.cart_custom_dt import CartNode
from dtcontrol.classifiers.oc1_node import OC1Node
from dtcontrol.util import peek_line

class OC1Parser:
    def parse_dt(self, dt_file):
        """
        Parses the OC1 generated DT file
        :return OC1Node object pointing to the root
        """
        with open(dt_file) as infile:
            dim = int(re.findall(r"Dimensions: ([0-9]+)", infile.readline())[0])
            return self.parse_recursive(dim, infile, -1)

    def parse_recursive(self, dim, infile, prev_depth):
        if not self.advance_to_next_hyperplane(infile):  # reached EOF
            node = OC1Node(None, None, prev_depth + 1)
            return node
        line = peek_line(infile)
        assert 'Hyperplane' in line
        path, left, right = self.parse_node(line)
        if prev_depth >= 0 and prev_depth >= len(path):
            node = OC1Node(None, None, prev_depth + 1)
            return node
        infile.readline()
        expr_line = infile.readline()
        coeff, intercept = self.parse_expression(expr_line, dim)
        depth = prev_depth + 1
        node = OC1Node(coeff, intercept, depth)
        if self.is_pure(left) and self.is_pure(right):
            left_node = OC1Node(None, None, depth + 1)
            left_node.trained_label = self.get_leaf_class(left)
            left_node.path = path + 'l'
            right_node = OC1Node(None, None, depth + 1)
            right_node.trained_label = self.get_leaf_class(right)
            right_node.path = path + 'r'
            node.left = left_node
            node.right = right_node
        else:
            if self.is_pure(left):
                left_node = OC1Node(None, None, depth + 1)
                left_node.trained_label = self.get_leaf_class(left)
                node.left = left_node
                left_node.path = path + 'l'
                node.right = self.parse_recursive(dim, infile, depth)
            elif self.is_pure(right):
                right_node = OC1Node(None, None, depth + 1)
                right_node.trained_label = self.get_leaf_class(right)
                node.right = right_node
                right_node.path = path + 'r'
                node.left = self.parse_recursive(dim, infile, depth)
            else:
                node.left = self.parse_recursive(dim, infile, depth)
                node.right = self.parse_recursive(dim, infile, depth)
        return node

    @staticmethod
    def advance_to_next_hyperplane(infile):
        while 'Hyperplane' not in peek_line(infile):
            pos = infile.tell()
            infile.readline()
            if infile.tell() == pos:  # EOF
                return False
        return True

    @staticmethod
    def parse_expression(line, dim):
        # remove the " = 0" part and the split
        summands = line[:-5].split(' + ')

        intercept = float(summands[-1])

        j = 0
        coeffs = []
        for i in range(1, dim + 1):
            if f"x[{i}]" in summands[j]:
                coeffs.append(float(summands[j].split()[0]))
                j = j + 1
            else:
                coeffs.append(0)
        return coeffs, intercept

    @staticmethod
    def is_pure(list_):
        return len(list_) - list_.count(0) == 1

    @staticmethod
    def get_leaf_class(leaf):
        for i in range(len(leaf)):
            if leaf[i] != 0:
                return i + 1

    @staticmethod
    def parse_node(line):
        decision_path, _, _, _, left, _, _, right = line.split()
        return decision_path, ast.literal_eval(left[:-1]), ast.literal_eval(right)
