import logging
import os
import subprocess
import sys

import numpy as np

import dtcontrol
import src.globals
from src.decision_tree.splitting.split import LinearSplit
from src.decision_tree.splitting.splitting_strategy import SplittingStrategy
from src.util import log_without_newline

class OC1SplittingStrategy(SplittingStrategy):
    """
    OC1 already computes the best axis-aligned split internally, so it is not necessary to have both the CART and OC1
    splitting strategy.
    """

    def __init__(self, num_restarts=30, num_jumps=15):
        self.oc1_path = 'decision_tree/OC1_source/mktree'
        self.output_file = 'oc1_tmp/output'
        self.data_file = 'oc1_tmp/data.csv'
        self.dt_file = 'oc1_tmp/dt'
        self.log_file = 'oc1_tmp/log'
        self.num_restarts = num_restarts
        self.num_jumps = num_jumps
        if not os.path.exists(self.oc1_path):
            self.compile_oc1()
        if not os.path.exists('oc1_tmp'):
            os.mkdir('oc1_tmp')

    def compile_oc1(self):
        for path in dtcontrol.__path__:
            oc1_src = f"{path}/src/decision_tree/OC1_source"
            if os.path.exists(oc1_src):
                if os.path.exists(oc1_src + "/mktree"):
                    self.oc1_path = oc1_src + "/mktree"
                    return
                try:
                    log_without_newline("Compiling OC1... ")
                    subprocess.call("make", cwd=oc1_src)
                    self.oc1_path = oc1_src + "/mktree"
                    logging.info("Compiled OC1")
                except subprocess.CalledProcessError:
                    logging.error("Compiling OC1 failed")
                    sys.exit(-1)

    def find_split(self, x, y, impurity_measure):
        self.save_data_to_file(x, y)
        self.execute_oc1()
        split = self.parse_oc1_dt(x.shape[1])
        mask = np.dot(x, split.coefficients) + split.intercept <= 0
        return mask, split

    def save_data_to_file(self, x, y):
        data = np.c_[x, y]
        num_float_columns = data.shape[1] - 1
        np.savetxt(self.data_file, data, fmt=' '.join(['%f'] * num_float_columns + ['%d']), delimiter='\t')

    def execute_oc1(self):
        command = f'{self.oc1_path} -t {self.data_file} -D {self.dt_file} -p0 -i{self.num_restarts} ' \
                  f'-j{self.num_jumps} -l {self.log_file}'
        with open(self.output_file, 'w+') as out:
            p = subprocess.Popen(command.split(' '), stdout=out)
            src.globals.oc1_pid = p.pid
            p.wait()
            src.globals.oc1_pid = None

    def parse_oc1_dt(self, dim):
        with open(self.dt_file) as infile:
            while not infile.readline().startswith('Root'):
                pass
            hyperplane_str = infile.readline()

        summands = hyperplane_str[:-4].split(' + ')
        intercept = float(summands[-1])
        j = 0
        coefficients = []
        for i in range(1, dim + 1):
            if f"x[{i}]" in summands[j]:
                coefficients.append(float(summands[j].split()[0]))
                j = j + 1
            else:
                coefficients.append(0)
        # TODO MJA: add check if split is actually axis-aligned
        return LinearSplit(np.array(coefficients), intercept)
