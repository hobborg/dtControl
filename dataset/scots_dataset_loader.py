import numpy as np

from dataset.dataset_loader import DatasetLoader

"""
@author: pushpakjagpushpaktap
"""
class ScotsDatasetLoader(DatasetLoader):
    def _load_dataset(self, filename):
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
            state_eta = state_eta + [float(line)]

        for i in range(3):
            f.readline()

        state_lb = []
        for i in range(state_dim):
            line = f.readline()
            state_lb = state_lb + [float(line)]

        for i in range(3):
            f.readline()

        state_ub = []
        for i in range(state_dim):
            line = f.readline()
            state_ub = state_ub + [float(line)]

        n_state_grid = []
        for i in range(state_dim):
            n_state_grid = n_state_grid + [int(round((state_ub[i] - state_lb[i]) / state_eta[i], 6)) + 1]

        for i in range(4):
            f.readline()

        line = f.readline()
        input_dim = int(line)

        for i in range(2):
            f.readline()

        input_eta = []
        for i in range(input_dim):
            line = f.readline()
            input_eta = input_eta + [float(line)]

        for i in range(3):
            f.readline()

        input_lb = []
        for i in range(input_dim):
            line = f.readline()
            input_lb = input_lb + [float(line)]

        for i in range(3):
            f.readline()

        input_ub = []
        for i in range(input_dim):
            line = f.readline()
            input_ub = input_ub + [float(line)]

        n_input_grid = []
        for i in range(input_dim):
            n_input_grid = n_input_grid + [int(round((input_ub[i] - input_lb[i]) / input_eta[i], 6) + 1)]

        for i in range(4):
            f.readline()

        dim_str = f.readline().split(":")[1]
        rows, max_non_det = list(map(int, dim_str.split()))

        # Controller starts now
        controller_start = 32 + 3 * (state_dim + input_dim)

        x_NN = [1]
        for i in range(1, state_dim):
            x_NN = x_NN + [x_NN[i - 1] * n_state_grid[i - 1]]

        u_NN = [1]
        for i in range(1, input_dim):
            u_NN = u_NN + [u_NN[i - 1] * n_input_grid[i - 1]]

        # creating input variables
        t = 0
        for t in range(state_dim):
            t += 1
            globals()["x" + str(t)] = []

        t1 = 0
        for t1 in range(input_dim):
            t1 += 1
            globals()["y" + str(t1)] = []

        # Get the number of lines describing the controller
        controller_lines = sum(1 for line in f) - 1

        x_train = np.empty((controller_lines, state_dim), dtype=np.float32)
        y_train = np.full((input_dim, controller_lines, max_non_det), -1, dtype=np.int16)

        f.seek(0)

        float_to_unique_label = dict()

        for i in range(controller_start):
            f.readline()

        for i in range(0, controller_lines):
            line = f.readline()
            idxu = np.matrix(line)
            idx = idxu[0, 0]
            k = state_dim - 1
            x = np.zeros(state_dim)
            while k > 0:
                num = int(idx / x_NN[k])  # j
                idx = idx % x_NN[k]  # i
                x[k] = state_lb[k] + num * state_eta[k]
                k = k - 1
            num = idx
            x[0] = state_lb[0] + num * state_eta[0]

            x_train[i - controller_start] = x
            # creating input variables
            u_idx = np.empty((1, input_dim), dtype=np.int32)
            t2 = 0
            for t2 in range(input_dim):
                t2 += 1
                globals()["yy" + str(t2)] = [[]]
            tt = 0
            for tt in range(input_dim):
                tt += 1
                globals()["u" + str(tt)] = [[]]
            for j in range(1, idxu.size):
                idu = idxu[0, j]
                kk = input_dim - 1
                u = np.zeros(input_dim)
                while kk > 0:
                    u_idx[0, kk] = int(idu / u_NN[kk])
                    idu = idu % u_NN[kk]
                    u[kk] = input_lb[kk] + u_idx[0, kk] * input_eta[kk]
                    if u[kk] not in float_to_unique_label.keys():
                        float_to_unique_label[u[kk]] = len(float_to_unique_label) + 1
                    y_train[kk][i - controller_start][j - 1] = float_to_unique_label[u[kk]]
                    kk = kk - 1
                u_idx[0, 0] = idu
                u[0] = input_lb[0] + u_idx[0, 0] * input_eta[0]
                if u[0] not in float_to_unique_label.keys():
                    float_to_unique_label[u[0]] = len(float_to_unique_label) + 1
                y_train[0][i - controller_start][j - 1] = float_to_unique_label[u[0]]

        # inverse map
        unique_label_to_float = {y: x for (x, y) in float_to_unique_label.items()}

        # if only single control input, do not wrap it in another array
        if y_train.shape[0] == 1:
            y_train = y_train[0]
        
        return (x_train, [], y_train, unique_label_to_float)