import ast
import os
import re
import subprocess
from shutil import copyfile

import numpy as np

import util
from classifiers.custom_dt import Node
from dataset.single_output_dataset import SingleOutputDataset


class OC1Wrapper:
    """
    A wrapper for the OC1 C code.

    Make sure that you have compiled the code ('make mktree' in OC1_source)!
    """

    def __init__(self, num_restarts=40, num_jumps=20):
        self.name = 'OC1'
        self.oc1_path = 'classifiers/OC1_source/mktree'
        self.output_file = 'oc1_tmp/oc1_output'
        self.data_file = 'oc1_tmp/oc1_data.csv'
        self.dt_file = 'oc1_tmp/oc1_dt'
        self.log_file = 'oc1_tmp/oc1.log'
        self.num_restarts = num_restarts
        self.num_jumps = num_jumps
        self.num_nodes = None
        self.num_oblique = None
        self.root: OC1Node = None

        if not os.path.exists('oc1_tmp'):
            os.mkdir('oc1_tmp')

    def is_applicable(self, dataset):
        return True

    def get_stats(self) -> dict:
        return {
            'nodes': self.num_nodes,
            'oblique': self.num_oblique,
            'bandwidth': int(np.ceil(np.log2((self.num_nodes + 1) / 2)))
        }

    def get_fit_command(self, dataset):  # TODO: segfault after number of oblique - dont compute accuracy
        self.map_unique_label_back = dataset.map_unique_label_back
        self.index_to_value = dataset.index_to_value
        self.save_data_to_file(np.c_[dataset.X_train, dataset.get_unique_labels()], last_column_is_label=True)
        command = './{} -t {} -D {} -p0 -i{} -j{} -l {}' \
            .format(self.oc1_path, self.data_file, self.dt_file, self.num_restarts, self.num_jumps, self.log_file)
        return command

    def fit_command_called(self):
        self.parse_fit_output()
        self.root: OC1Node = self.parse_dt()
        self.root.set_labels(lambda x: self.map_unique_label_back(x.trained_label), self.index_to_value)

    def fit(self, dataset):
        command = self.get_fit_command(dataset)
        self.execute_command(command)
        self.fit_command_called()

    def parse_fit_output(self):
        with open(self.output_file, 'r') as f:
            for line in f:
                if line.startswith('Number of nodes'):
                    self.num_nodes = int(line.split(': ')[1])
                elif line.startswith('Number of oblique'):
                    self.num_oblique = int(line.split(': ')[1])

    def parse_dt(self):
        """
        Parses the OC1 generated DT file
        :return OC1Node object pointing to the root
        """
        f = open(self.dt_file)
        dim = int(re.findall(r"Dimensions: ([0-9]+)", f.readline())[0])
        for line in f:
            if "Hyperplane" in line:
                path, left, right = self.parse_node(line)
                expr_line = f.readline()
                coeff, intercept = self.parse_expression(expr_line, dim)
                if "Root" in path:
                    if self.is_leaf(left) and self.is_leaf(right):
                        root = OC1Node(None, None, depth=0)
                        assert self.get_leaf_class(left) == self.get_leaf_class(right)
                        root.trained_label = self.get_leaf_class(left)
                    else:
                        root = OC1Node(coeff, intercept, depth=0)
                        if self.is_leaf(left):
                            root.left = OC1Node(None, None, depth=1)
                            root.left.trained_label = self.get_leaf_class(left)
                        if self.is_leaf(right):
                            root.right = OC1Node(None, None, depth=1)
                            root.right.trained_label = self.get_leaf_class(right)
                    continue

                current_node = root
                depth = 0
                for direction in path:
                    depth += 1
                    if direction == "l":
                        if not current_node.left:
                            current_node.left = OC1Node(coeff, intercept, depth=depth)
                        current_node = current_node.left
                    elif direction == "r":
                        if not current_node.right:
                            current_node.right = OC1Node(coeff, intercept, depth=depth)
                        current_node = current_node.right

                if self.is_leaf(left):
                    current_node.left = OC1Node(None, None, depth=depth)
                    current_node.left.trained_label = self.get_leaf_class(left)
                if self.is_leaf(right):
                    current_node.right = OC1Node(None, None, depth=depth)
                    current_node.right.trained_label = self.get_leaf_class(right)

        return root

    def predict(self, dataset):
        self.save_data_to_file(dataset.X_train)
        command = './{} -T {} -u -D {} -l {}'.format(self.oc1_path, self.data_file, self.dt_file, self.log_file)
        self.execute_command(command)
        output = self.parse_predict_output()
        result = [dataset.map_unique_label_back(x) for x in output]
        return result

    def parse_predict_output(self):
        data = np.loadtxt('{}.classified'.format(self.data_file), delimiter='\t')
        return data[:, -1]

    def save_data_to_file(self, data, last_column_is_label=False):
        num_int_columns = 1 if last_column_is_label else 0
        num_float_columns = data.shape[1] - num_int_columns
        np.savetxt(self.data_file, data, fmt=' '.join(['%f'] * num_float_columns + ['%d'] * num_int_columns),
                   delimiter='\t')

    def execute_command(self, command):
        with open(self.output_file, 'w+') as out:
            p = subprocess.Popen(command.split(' '), stdout=out)
            p.wait()

    def save(self, filename):
        copyfile(self.dt_file, filename)

    def export_dot(self, file=None):
        dot = self.root.export_dot()
        if file:
            with open(file, 'w+') as outfile:
                outfile.write(dot)
        else:
            return dot

    def export_c(self, file=None):
        pass

    def export_vhdl(self, file=None):
        pass

    @staticmethod
    def parse_expression(line, dim):
        # remove the " = 0" part and the split
        summands = line[:-5].split(' + ')

        intercept = round(float(summands[-1]), 6)

        j = 0
        coeffs = []
        for i in range(1, dim + 1):
            if f"x[{i}]" in summands[j]:
                coeffs.append(round(float(summands[j].split()[0]), 6))
                j = j + 1
            else:
                coeffs.append(0)
        return coeffs, intercept

    @staticmethod
    def is_leaf(list_):
        return len(list_) - list_.count(0) == 1

    @staticmethod
    def get_leaf_class(leaf):
        for i in range(len(leaf)):
            if leaf[i] != 0:
                return (i + 1)

    @staticmethod
    def parse_node(line):
        decision_path, _, _, _, left, _, _, right = line.split()
        return decision_path, ast.literal_eval(left[:-1]), ast.literal_eval(right)


class OC1Node(Node):
    def __init__(self, coeff, intercept, depth=0):
        super().__init__(depth)
        self.dt = None
        self.coeff = coeff
        self.intercept = intercept

    def test_condition(self, x):
        """
        :param x: [row of X_train]; shape (1, num_features)
        :return true if go left
        """
        pass

    def create_child_node(self):
        pass

    def find_split(self, X, y):
        pass

    def get_dot_label(self):
        if self.actual_label is not None:
            return str(util.objround(self.actual_label, 6))  # TODO get precision from flag?
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
        pass
