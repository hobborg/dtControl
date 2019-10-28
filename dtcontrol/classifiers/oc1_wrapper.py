import os
import sys
import subprocess
from collections import defaultdict
from shutil import copyfile

import numpy as np

import dtcontrol.util
from dtcontrol.classifiers.cart_custom_dt import CartNode
from dtcontrol.classifiers.custom_dt import CustomDT
from dtcontrol.classifiers.oc1_node import OC1Node
from dtcontrol.classifiers.oc1_parser import OC1Parser


class OC1Wrapper(CustomDT):
    """
    A wrapper for the OC1 C code.

    Make sure that you have compiled the code ('make mktree' in OC1_source)!
    """

    def __init__(self, num_restarts=40, num_jumps=20):
        super().__init__()
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
        self.current_dataset = None
        self.root: OC1Node = None
        self.oc1_parser = OC1Parser()
        self.oc1_reported_acc = None  # The accuracy reported by OC1. Used for debugging.
        self.num_extended_nodes = 0  # The amount of nodes added after OC1 to ensure full overfitting.

        if not os.path.exists(self.oc1_path):
            self.compile_oc1()

        if not os.path.exists('oc1_tmp'):
            os.mkdir('oc1_tmp')

    def compile_oc1(self):
        for path in dtcontrol.__path__:
            oc1_src = f"{path}/classifiers/OC1_source"
            if os.path.exists(oc1_src):
                if os.path.exists(oc1_src + "/mktree"):
                    self.oc1_path = oc1_src + "/mktree"
                    return
                try:
                    print(f"Compiling OC1...")
                    subprocess.call("make", cwd=oc1_src)
                    self.oc1_path = oc1_src + "/mktree"
                    print("Compiled OC1\n")
                except subprocess.CalledProcessError:
                    print("Compiling OC1 failed")  # todo use logging
                    sys.exit(-1)

    def is_applicable(self, dataset):
        return True

    def get_stats(self) -> dict:
        return {
            'nodes': self.num_nodes,
            'oblique': self.num_oblique,
            'extended': self.num_extended_nodes,
            'bandwidth': int(np.ceil(np.log2((self.num_nodes + 1) / 2)))
        }

    def get_fit_command(self, dataset):
        self.current_dataset = dataset
        self.save_data_to_file(np.c_[dataset.X_train, dataset.get_unique_labels()])
        command = '{} -t {} -D {} -p0 -i{} -j{} -l {}' \
            .format(self.oc1_path, self.data_file, self.dt_file, self.num_restarts, self.num_jumps, self.log_file)
        return command

    def fit_command_called(self):
        self.parse_fit_output()
        self.root: OC1Node = self.oc1_parser.parse_dt(self.dt_file)
        self.train_cart_nodes()
        self.root.set_labels(lambda x: self.current_dataset.map_unique_label_back(x.trained_label),
                             self.current_dataset.index_to_value)
        self.current_dataset = None

    def train_cart_nodes(self):
        node_to_data = defaultdict(list)
        node_to_labels = defaultdict(list)
        nodes_to_extend = []
        for i in range(len(self.current_dataset.X_train)):
            row = self.current_dataset.X_train[i]
            label = self.current_dataset.get_unique_labels()[i]
            parent = None
            node = self.root
            while node.left:
                parent = node
                node = node.left if node.test_condition(row.reshape(1, -1)) else node.right
            node_to_data[node].append(row)
            node_to_labels[node].append(label)
            if node.trained_label != label and node not in [n for n, _ in nodes_to_extend]:
                nodes_to_extend.append((node, parent))

        for node, parent in nodes_to_extend:
            cart_node = CartNode(node.depth)
            if parent.left == node:
                parent.left = cart_node
            else:
                parent.right = cart_node
            cart_node.fit(np.array(node_to_data[node]), np.array(node_to_labels[node]))
            self.num_nodes += cart_node.num_nodes - 1
            self.num_extended_nodes += cart_node.num_nodes - 1

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
                elif line.startswith('acc.'):
                    line = line.split('\t')[0]
                    line = line.split(' = ')[1]
                    self.oc1_reported_acc = float(line)

    def save_data_to_file(self, data):
        num_float_columns = data.shape[1] - 1
        np.savetxt(self.data_file, data, fmt=' '.join(['%f'] * num_float_columns + ['%d']), delimiter='\t')

    def execute_command(self, command):
        with open(self.output_file, 'w+') as out:
            p = subprocess.Popen(command.split(' '), stdout=out)
            p.wait()

    def save(self, filename):
        copyfile(self.dt_file, filename)

    def export_vhdl(self, numInputs, file=None):
        pass
