import logging

import numpy as np
from dtcontrol.dataset.dataset_loader import DatasetLoader
from tqdm import tqdm


class ScotsDatasetLoader(DatasetLoader):
    def _load_dataset(self, filename):
        precision = 10

        f = open(filename)
        print(f"Reading from {filename}")

        for i in range(5):
            f.readline()

        line = f.readline()
        state_dim = int(line)

        for i in range(2):
            f.readline()

        state_eta = []
        for i in range(state_dim):
            line = f.readline()
            state_eta.append(round(float(line), precision))

        for i in range(3):
            f.readline()

        state_lb = []
        for i in range(state_dim):
            line = f.readline()
            state_lb.append(round(float(line), precision))

        for i in range(3):
            f.readline()

        state_ub = []
        for i in range(state_dim):
            line = f.readline()
            state_ub.append(round(float(line), precision))

        n_state_grid = []
        for i in range(state_dim):
            n_state_grid.append(int(round((state_ub[i] - state_lb[i]) / state_eta[i], precision)) + 1)

        for i in range(4):
            f.readline()

        input_dim = int(f.readline())

        for i in range(2):
            f.readline()

        input_eta = []
        for i in range(input_dim):
            line = f.readline()
            input_eta.append(round(float(line), precision))

        for i in range(3):
            f.readline()

        input_lb = []
        for i in range(input_dim):
            line = f.readline()
            input_lb.append(round(float(line), precision))

        for i in range(3):
            f.readline()

        input_ub = []
        for i in range(input_dim):
            line = f.readline()
            input_ub.append(float(line))

        n_input_grid = []
        for i in range(input_dim):
            n_input_grid.append(int(round((input_ub[i] - input_lb[i]) / input_eta[i], precision) + 1))

        for i in range(4):
            f.readline()

        dim_str = f.readline().split(":")[1]
        rows, max_non_det = list(map(int, dim_str.split()))

        # Controller starts now
        controller_start = 32 + 3 * (state_dim + input_dim)

        x_NN = [1]
        for i in range(1, state_dim):
            x_NN.append(x_NN[i - 1] * n_state_grid[i - 1])

        u_NN = [1]
        for i in range(1, input_dim):
            u_NN.append(u_NN[i - 1] * n_input_grid[i - 1])

        # Get the number of lines describing the controller
        controller_lines = sum(1 for line in f) - 1

        x_train = np.empty((controller_lines, state_dim), dtype=np.float32)
        y_train = np.full((input_dim, controller_lines, max_non_det), -1, dtype=np.int32)

        f.seek(0)

        float_to_unique_label = dict()

        for i in range(controller_start):
            f.readline()

        logging.info("Extracting states and control inputs from SCOTS dump")
        for i, line in enumerate(tqdm(f, total=controller_lines)):
            if i == controller_lines:
                break
            idxu = np.fromstring(line, dtype=np.int32, sep=' ')
            idx = idxu[0]

            k = state_dim - 1
            x = np.zeros(state_dim)
            while k > 0:
                num = int(idx / x_NN[k])  # j
                idx = idx % x_NN[k]  # i
                x[k] = state_lb[k] + num * state_eta[k]
                k = k - 1
            num = idx
            x[0] = state_lb[0] + num * state_eta[0]

            x_train[i] = x

            # creating input variables
            u_idx = np.empty(input_dim, dtype=np.int16)
            for j in range(1, idxu.shape[0]):
                idu = idxu[j]
                kk = input_dim - 1
                u = np.empty(input_dim, dtype=np.float32)
                while kk > 0:
                    u_idx[kk] = int(idu / u_NN[kk])
                    idu = idu % u_NN[kk]
                    u[kk] = input_lb[kk] + u_idx[kk] * input_eta[kk]
                    if u[kk] not in float_to_unique_label.keys():
                        float_to_unique_label[u[kk]] = len(float_to_unique_label) + 1
                    y_train[kk][i][j - 1] = float_to_unique_label[u[kk]]
                    kk = kk - 1
                u_idx[0] = idu
                u[0] = input_lb[0] + u_idx[0] * input_eta[0]
                if u[0] not in float_to_unique_label.keys():
                    float_to_unique_label[u[0]] = len(float_to_unique_label) + 1
                y_train[0][i][j - 1] = float_to_unique_label[u[0]]

        # inverse map
        unique_label_to_float = {y: x for (x, y) in float_to_unique_label.items()}

        # if only single control input, do not wrap it in another array
        if y_train.shape[0] == 1:
            y_train = y_train[0]

        print("Constructed training set with %s datapoints" % x_train.shape[0])

        # construct metadata
        x_metadata = dict()
        x_metadata["variables"] = [f"x_{i}" for i in range(len(state_lb))]
        x_metadata["min"] = state_lb
        x_metadata["max"] = state_ub
        x_metadata["step_size"] = state_eta

        y_metadata = dict()
        y_metadata["variables"] = [f"u_{i}" for i in range(len(input_lb))]
        y_metadata["min"] = input_lb
        y_metadata["max"] = input_ub
        y_metadata["step_size"] = input_eta

        return (x_train, x_metadata, y_train, y_metadata, unique_label_to_float)
