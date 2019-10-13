import re

import numpy as np
import pandas as pd

from dataset.dataset_loader import DatasetLoader


class UppaalDatasetLoader(DatasetLoader):
    '''
    Assumption is that all controllable states are named *.Choose
    '''
    def _load_dataset(self, filename):
        f = open(filename)
        print("Reading from %s" % filename)

        lines = f.readlines()

        # Extract categorical_features
        categorical_features = re.findall('(\w+)\.\w+', lines[1])

        # Extract numeric features
        numeric_features = re.findall('(\w+)=\-?[0-9]+', lines[7])

        # Extract actions and controllable components
        action_set = set()
        controllable_states = set()
        for line in lines:
            if line.startswith('State: '):
                ctrl = re.findall(r'(\w+\.Choose)', line)
                if ctrl:
                    controllable_states.update(ctrl)
            if line.startswith('When'):
                action_set.add(line[line.index(' take transition ')+17:].rstrip())
        actions = dict(zip(list(action_set), range(1, len(action_set)+1)))
        controllable_states = list(controllable_states)

        # Figure out the assignments in each action and extract
        # the assigned value. The assigned variable is extracted
        # too, but not used anywhere as of now.
        index_to_value = dict()
        for (action, index) in actions.items():
            _, var, val = re.findall(r"((\w+) \:\= (-?[0-9]+))", action)[0]
            index_to_value[index] = val

        row_num_vals = []
        row_actions = []

        ignore_current = False
        current_actions = []
        total_rows = 0
        total_state_actions = 0
        for line in lines[7:]:
            if line.startswith("State:"):
                # find if the state is controllable, and if so, then make that position 1 in categorical vals
                controllable = False
                cat_vals = [0 for i in range(len(controllable_states))]
                for i in range(len(controllable_states)):
                    if controllable_states[i] in line:
                        cat_vals[i] = 1
                        controllable = True
                if not controllable:
                    ignore_current = True
                    continue
                else:
                    ignore_current = False
                    numeric_vals = re.findall('\w+=([^\ ]+)', line)
            elif ignore_current:
                continue
            elif line.startswith("When"):
                action_str = line[line.index(' take transition ')+17:].rstrip()
                current_actions.append(actions[action_str])
            elif line.startswith("While"):
                # We implicityly assume that transitions starting with 'While' are mapped to wait.
                ignore_current = True
            elif line.strip() == "":
                if not ignore_current:
                    row_num_vals.append(cat_vals + numeric_vals)
                    row_actions.append(current_actions)
                    total_rows += 1
                    total_state_actions += len(current_actions)
                ignore_current = False
                current_actions = []
            else:
                raise Exception("ERROR: Unhandled line in input")
                break

        print(f"Done reading {total_rows} states with \na total of {total_state_actions} state-action pairs.")

        # Project onto measurable variables, the strategy should not depend on the gua variables coming from euler
        projection_variables = controllable_states + list(filter(lambda x: 'gua' not in x, numeric_features))
        num_df = pd.DataFrame(row_num_vals, columns=controllable_states + numeric_features, dtype='float32')
        num_df = num_df[projection_variables]

        grouped = num_df.groupby(projection_variables)
        X = np.empty((len(grouped), len(projection_variables)))
        Y = np.full((len(grouped), max([len(y) for y in row_actions])), -1)

        i = 0
        for (group, indices) in grouped.indices.items():
            if len(indices) > 1:
                X[i] = group
                conservative_actions = set(actions.values()).copy()
                for idx in indices:
                    conservative_actions &= set(row_actions[idx])
                assert len(conservative_actions) > 0, "Stategy for picking safe action doesn't work. Deeper analysis needed."
                Y[i][0:len(conservative_actions)] = list(sorted(conservative_actions))
            else:
                X[i] = group
                Y[i][0:len(row_actions[indices[0]])] = sorted(row_actions[indices[0]])
            i = i+1
            
        print("\nConstructed training set with %s datapoints" % X.shape[0])

        return (X, projection_variables, Y, index_to_value)