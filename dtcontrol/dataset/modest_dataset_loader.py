import logging
import numpy as np
import pandas as pd

from dtcontrol.dataset.dataset_loader import DatasetLoader


class ModestDatasetLoader(DatasetLoader):
    def _load_dataset(self, filename):
        """
        Read a plaintext scheduler dump from the Modest Toolset.
        https://dtcontrol.readthedocs.io/en/latest/devman.html#supporting-new-file-formats
        """

        logging.info(f"Reading from {filename}")
        with (open(filename, 'r') as f):
            # Error checking and logging
            brand = "Schedulers"
            header = f.readline()
            if header.find(brand) < 0:
                raise SyntaxError(filename + " is not a scheduler trace from the Modest Toolset")
            elif header[header.find(brand) + len(brand):] != '\n':
                raise NotImplementedError(filename + " contains the trace of more than one scheduler (unsupported)")
            header = f.readline()
            if header.find("variables") < 0:
                raise SyntaxError(filename + " is not a scheduler trace from the Modest Toolset")

            # Map variables' types declared in the file header
            vars_cat = {}
            is_num = []  # type of variables in order of occurrence
            fpos = f.tell()
            while header.find("Property") < 0:
                f.seek(fpos)
                vname = f.readline().split(': ')[1].strip()
                vtype = f.readline().split(': ')[1].strip()
                f.readline()  # discard storage size data
                if vtype.find("location") >= 0 or vtype.find("bool") >= 0:
                    cat_names = f.readline().split(': ')[1].strip()
                    vars_cat[vname] = [name.strip() for name in cat_names[1:-1].split(",")]
                    is_num.append(tuple([False, vname]))  # variable is not numeric
                else:
                    is_num.append(tuple([True, vname]))  # variable is numeric
                # look ahead
                fpos = f.tell()
                header = f.readline()

            # We should start reading the scheduler trace for a property now
            ppty = header.split(":")[1].strip()
            if len(ppty) == 0:
                raise SyntaxError(filename + " is not a scheduler trace from the Modest Toolset")
            logging.info(f"Processing scheduler trace for the {ppty} property")

            # Generate the matrices of states and actions
            x = []  # values  of variables in each state
            idx = 1  # from dataset.py: "OC1 expects labels starting with 1"
            idx_2_action = {}
            action_2_idx = {}
            action_indices_list = []
            for line in f:
                if line.find("Property") >= 0:
                    ppty = line.split(":")[1].strip()
                    logging.warning(f"(unsupported) Found a second property \"{ppty}\", skipping rest of trace")
                    break
                # Record the value of the variables of this state
                state = line[line.find("(") + 1: line.find(")")].strip()
                assert (state.find(" = ") >= 0)
                vals = [ass.split(" = ")[1] for ass in state.split(", ")]
                # dtControl expects all values to be numeric:
                vals = [int(vals[i]) if is_num[i][0]  # numeric variables are easy
                        else vars_cat[is_num[i][1]].index(vals[i])  # categorical variable: record index of value
                        for i in range(len(vals))]  # [tinyurl.com/dh7p97rd]
                x.append(tuple(int(v) for v in vals))

                # For the action out of this state...
                action = f.readline()
                assert (action.find("Choice:") >= 0)
                action = action.split("Choice:")[1].strip()
                # ... record its index
                if action not in action_2_idx:
                    action_2_idx[action] = idx
                    idx_2_action[idx] = action
                    idx += 1
                action_indices_list.append([action_2_idx[action]])

        assert (len(x) > 0)
        assert (len(x) == len(action_indices_list))

        # Format state variables as expected by dtControl
        all_vars = [v[1] for v in is_num]
        df = pd.DataFrame(x, columns=all_vars)
        x = np.array(x)
        x_metadata = {
            "variables": all_vars,
            "min_inner": list(df.agg("min")),
            "min_outer": list(df.agg("min")),  # OMG *so* inefficient
            "max_inner": list(df.agg("max")),
            "max_outer": list(df.agg("max")),
            "categorical": [],  # handled by dataset_loader.py via accompanying _config.json file
            "step_size": [1 for _ in x[0]],
        }

        # Format actions as expected by dtControl
        y = np.full((len(action_indices_list), 1), -1, dtype=np.int16)
        for i, idx in enumerate(action_indices_list):
            y[i] = np.array(idx)  # idx of action out of state at i-th position
        idx_2_actual = {i: i - 1 for i in idx_2_action.keys()}

        y_metadata = {
            "categorical": [0],  # we always have exactly one output, and it is categorical
            "category_names": {0: [v.strip() for v in sorted(action_2_idx.keys(), key=action_2_idx.get)]},
            "min": [min(idx_2_actual.values())],
            "max": [max(idx_2_actual.values())],
        }
        y_metadata["step_size"] = [int((y_metadata["max"][0] - y_metadata["min"][0]) / max(1, len(idx_2_actual) - 1))]

        logging.debug(x_metadata)
        logging.debug(y_metadata)

        return x, x_metadata, y, y_metadata, idx_2_actual
