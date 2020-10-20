import json
import logging
from os.path import splitext, exists

import numpy as np

from dtcontrol.dataset.dataset_loader import DatasetLoader


class StormDatasetLoader(DatasetLoader):
    '''
    Loads a STORM scheudler generated using the switches:
    --buildstateval --buildchoiceorig  --exportscheduler filename.storm.json
    from Pmin/max=? and R[exp]min/max=? properties
    '''
    def _load_dataset(self, filename):
        logging.info(f"Reading from {filename}")

        file = open(filename)
        json_file = json.loads(file.read())

        x_variables = None
        x_list = []
        y_list = []

        # Stores mapping from action index to action string
        index_to_choice = dict()
        choice_to_index = dict()
        long_action = dict()
        new_action_index = 0
        new_long_action = 0

        for entry in json_file:
            # Add choices
            y_current = []
            for non_deterministic_choice in entry["c"]:
                if "origin" not in non_deterministic_choice:
                    '''
                    a) There is no commandset/edgeset enabled. In this case Storm adds a self-loop to the deadlock 
                       state in order to get a valid MDP.
                    b) There is no need to continue state-space exploration in order to check the provided property 
                       (e.g. we do not need to explore the successors of a target state if we only want to check a 
                       single reachability formula). Again, Storm just adds a single self loop choice in order to 
                       get a valid MDP.
                    '''
                    choice_string = ":loop:"
                    break
                # elif "action-label" in non_deterministic_choice["origin"] and non_deterministic_choice["origin"]["action-label"]:
                #     choice_string = non_deterministic_choice["origin"]["action-label"]
                else:
                    if json.dumps(non_deterministic_choice["origin"], ensure_ascii=False) not in long_action:
                        long_action[json.dumps(non_deterministic_choice["origin"], ensure_ascii=False)] = new_long_action
                        new_long_action = new_long_action + 1
                    if "action-label" in non_deterministic_choice["origin"] and non_deterministic_choice["origin"]["action-label"]:
                        choice_string_prefix = non_deterministic_choice["origin"]["action-label"]
                    else:
                        choice_string_prefix = "act"
                    choice_string = f'{choice_string_prefix}{long_action[json.dumps(non_deterministic_choice["origin"], ensure_ascii=False)]}'

                if choice_string not in choice_to_index:
                    index_to_choice[new_action_index] = choice_string
                    choice_to_index[choice_string] = new_action_index
                    new_action_index = new_action_index + 1

                index = choice_to_index[choice_string]
                y_current.append(index+1)

            if ":loop:" in choice_string:
                continue

            y_list.append(y_current)

            # Add state
            state = entry["s"]
            if not x_variables:
                x_variables = list(state.keys())

            x_list.append(list(state.values()))

        x = np.array(x_list)
        y = np.full((len(y_list), max([len(e) for e in y_list])), -1, dtype=np.int16)
        for i, row in enumerate(y_list):
            y[i][0:len(row)] = np.array(row)

        x_metadata = dict()
        x_metadata["variables"] = x_variables
        x_metadata["categorical"] = []
        x_metadata["min_inner"] = x_metadata["min_outer"] = [float(i) for i in np.amin(x, axis=0)]
        x_metadata["max_inner"] = x_metadata["max_outer"] = [float(i) for i in np.amax(x, axis=0)]
        x_metadata["step_size"] = [1 for _ in x[0]]

        index_to_actual = {i+1: i for i in index_to_choice.keys()}

        y_metadata = dict()
        y_metadata["categorical"] = [0]  # we always have exactly one output, and it is categorical
        y_metadata["category_names"] = {0: [v.strip() for v in sorted(choice_to_index.keys(), key=choice_to_index.get)]}
        y_metadata["min"] = [min(index_to_actual.values())]
        y_metadata["max"] = [max(index_to_actual.values())]
        y_metadata["step_size"] = [int((y_metadata["max"][0] - y_metadata["min"][0]) / (len(index_to_actual) - 1))]

        logging.debug(x_metadata)
        logging.debug(y_metadata)

        return (x, x_metadata, y, y_metadata, index_to_actual)
