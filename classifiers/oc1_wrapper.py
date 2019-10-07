import numpy as np
import subprocess
import os
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

        if not os.path.exists('oc1_tmp'):
            os.mkdir('oc1_tmp')

    def is_applicable(self, dataset):
        return isinstance(dataset, SingleOutputDataset)

    def get_stats(self):
        return {
            'num_nodes': self.num_nodes,
            'num_oblique': self.num_oblique
        }

    def get_fit_command(self, dataset):
        self.save_data_to_file(np.c_[dataset.X_train, dataset.get_unique_labels()], last_column_is_label=True)
        command = './{} -t {} -D {} -p0 -i{} -j{} -l {}' \
            .format(self.oc1_path, self.data_file, self.dt_file, self.num_restarts, self.num_jumps, self.log_file)
        return command

    def fit_command_called(self):
        self.parse_fit_output()

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

    def predict(self, dataset):
        self.save_data_to_file(dataset.X_train)
        command = './{} -T {} -u -D {} -l {}'.format(self.oc1_path, self.data_file, self.dt_file, self.log_file)
        self.execute_command(command)
        output = self.parse_predict_output()
        output = np.reshape(output, (-1, 1))
        return np.apply_along_axis(lambda x: dataset.map_unique_label_back(x[0]), axis=1,
                                   arr=output)  # TODO: represent tree in python

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
