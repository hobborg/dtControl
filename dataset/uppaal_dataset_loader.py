import re

from dataset.dataset_loader import DatasetLoader

class UppaalDatasetLoader(DatasetLoader):
    def _load_dataset(self, filename):
        pass

    # TODO: integrate the following method into the _load_dataset method

    """
        Reads {file} and procudes either a Single-OutputDataset
        (X_train, Y_train, mapping_dict, X_vars, action_dict) where 
        X_train is a numpy array of state valuations for each state in the controller
        Y_train a list of lists of action indices
        value_index_mapping maps action values (floats) to action indices - here, always {}
        X_vars contains the names of the columns in X_train
        action_dict is the mapping from action index to action name

        :param file: A file exported using UPPAAL's --print-strategies CLI switch
        """

    @staticmethod
    def from_uppaal(file):
        f = open(file)
        print("Reading from %s" % file)

        lines = f.readlines()

        # Extract categorical_features
        categorical_features = re.findall('(\w+)\.\w+', lines[1])

        # Extract numeric features
        numeric_features = re.findall('(\w+)=\-?[0-9]+', lines[7])

        # Extract actions
        action_set = set()
        for line in lines:
            if line.startswith('When'):
                action_set.add(line[line.index(' take transition ') + 17:].rstrip())
        action_set.add('wait')
        actions = dict(zip(list(action_set), range(0, len(action_set))))

        row_num_vals = []
        row_actions = []

        current_actions = []
        ignore_current = False
        total_rows = 0
        total_state_actions = 0
        for line in lines[7:]:
            if line.startswith("State"):
                numeric_vals = re.findall('\w+=([^\ ]+)', line)
            elif ignore_current:
                continue
            elif line.startswith("When"):
                collect_actions = True
                action_str = line[line.index(' take transition ') + 17:].rstrip()
                current_actions.append(actions[action_str])
            elif line.startswith("While"):
                # We implicityly assume that transitions starting with 'While' are mapped to wait.
                current_actions.append(actions['wait'])
            elif line.strip() == "":
                # if not ignore_current:
                row_num_vals.append(numeric_vals)
                row_actions.append(current_actions)
                total_rows += 1
                total_state_actions += len(current_actions)
                current_actions = []
            else:
                raise Exception("ERROR: Unhandled line in input")
                break

        print(f"Done reading {total_rows} states with \na total of {total_state_actions} state-action pairs.")

        # Project onto measurable variables, the strategy should not depend on the gua variables coming from euler
        projection_variables = list(filter(lambda x: 'gua' not in x, numeric_features))
        num_df = pd.DataFrame(row_num_vals, columns=numeric_features, dtype='float32')
        num_df = num_df[projection_variables]

        X_train = np.asarray(num_df)
        Y_train = row_actions

        print("\nConstructed training set with %s datapoints" % X_train.shape[0])

        index_to_action_name = [{y: x} for (x, y) in actions.items()]

        return (X_train, Y_train, {}, projection_variables, index_to_action_name)
