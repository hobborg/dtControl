import logging
from os.path import splitext, exists
import numpy as np
from dtcontrol.dataset.dataset_loader import DatasetLoader

def get_possible_evaluations(liste, index, vals=[0,1]):
    new_list = []
    for element in liste:
        for val in vals:
            ne = [i for i in element]
            ne[index] = val
            new_list.append(ne)
    return new_list

class StrixDatasetLoader(DatasetLoader):
    '''
    Loads a STRIX file
    '''
    def _load_dataset(self, filename):
        logging.info(f"Reading from {filename}")

        f = open(filename)
        read_lines = f.readlines()
        f.close()

        # first line gives you the inputs
        # second line gives you the outputs
        # third line number of inputs
        # fourth line number of outputs
        # fifth line number of products ?
        # sixth linenumber of states used ?
        # seventh line reset state ?
        # following lines
        # per line: first the input, second the current state, third the goal state, fourth the output

        input_size = int(read_lines[2].split(' ')[-1])
        output_size = int(read_lines[3].split(' ')[-1])
        lines = int(read_lines[4].split(' ')[-1])
        num_states = int(read_lines[5].split(' ')[-1])
        size_per_state = len(read_lines[6].split(' ')[-1].split(','))

        state_size = input_size + size_per_state

        x_list = []
        action_index_mapping = []
        y_list = []
        max_non_determinism = 0

        # find all possible values that the goal state can contain
        opened = [i.split(' ')[1:2] for i in read_lines[7:7+lines]]
        flatten = lambda l: [item.replace('(','').replace(')','').replace('-','').replace('+','').replace('\n','').replace(',','') for sublist in l for item in sublist]
        opened = np.unique(np.array([i for i  in flatten(opened) if i!=''], dtype=int))

        for li in range(lines):
            line = read_lines[7 + li]
            inp = line.split(' ')[0]

            # get all possible inputs
            inp = [c for c in inp]
            non_determined_input_bits = [i for i, ltr in enumerate(inp) if ltr == '-']
            input_array = [-1]*len(inp)
            for i in range(len(inp)):
                if not i in non_determined_input_bits:
                    input_array[i] = int(inp[i])
            list_of_possible_inputs = [input_array]
            for index in non_determined_input_bits:
                list_of_possible_inputs = get_possible_evaluations(list_of_possible_inputs, index)


            # get all possible start states
            start_state = line.split(' ')[1][1:-1].split(',')
            if len(start_state) == 1 and start_state[0] == '':
                list_of_possible_start_states = [[]]
            else:
                non_determined_input_bits = [i for i, ltr in enumerate(start_state) if ltr == '-']
                start_state_array = [-1]*len(start_state)
                for i in range(len(start_state)):
                    if not i in non_determined_input_bits:
                        start_state_array[i] = int(start_state[i])
                list_of_possible_start_states = [start_state_array]
                for index in non_determined_input_bits:
                    list_of_possible_start_states = get_possible_evaluations(list_of_possible_start_states, index, opened)

            # combine both
            add_list = []
            for inpu in list_of_possible_inputs:
                for state in list_of_possible_start_states:
                    sst = [i for i in inpu]
                    sst.extend(state)
                    add_list.append(sst)
            number_of_added = len(add_list)
            x_list.extend(add_list)

            # get all possible goal states
            goal_state = line.split(' ')[2][1:-1].split(',')
            if len(goal_state) == 1 and goal_state[0] == '':
                list_of_possible_goal_states = [[]]
            else:
                non_determined_input_bits = [i for i, ltr in enumerate(goal_state) if ltr == '-']
                goal_state_array = [-1]*len(goal_state)
                for i in range(len(goal_state)):
                    if not i in non_determined_input_bits:
                        goal_state_array[i] = int(goal_state[i])
                list_of_possible_goal_states = [goal_state_array]
                for index in non_determined_input_bits:
                    list_of_possible_goal_states = get_possible_evaluations(list_of_possible_goal_states, index, opened)

            # get all possible output values
            outputs = line[:-1].split(' ')[3:]
            outputs = [a for a in outputs if not a=='+']
            outputs_to_add = []
            for element in outputs:
                input_array = [-1]*len(element)
                for i in range(len(element)):
                    if not element[i]=='-':
                        input_array[i] = int(element[i])
                list_of_possible = [input_array]
                if element.find('-')>=0:
                    non_determined = [i for i, ltr in enumerate(element) if ltr == '-']
                    for index in non_determined:
                        list_of_possible = get_possible_evaluations(list_of_possible, index)
                outputs_to_add.extend(list_of_possible)
            # combine both
            add_list = []
            for goal in list_of_possible_goal_states:
                for output in outputs_to_add:
                    gsl = [i for i in goal]
                    gsl.extend(output)
                    add_list.append(gsl)
            if len(add_list)>max_non_determinism:
                max_non_determinism = (len([i for i in add_list]))
            y_list.extend([add_list]*number_of_added)
        x = np.array(x_list)

        y_flat = [item for sublist in y_list for item in sublist]
        unique_label_to_float = {x+1: y for x, y in enumerate(np.unique(y_flat))}
        float_to_label = {y: x+1 for x,y in enumerate(np.unique(y_flat))}
        replace_float = lambda l : [float_to_label[item] for item in l]

        min_value = np.ones(size_per_state + output_size)*np.infty
        for i,element in enumerate(y_list):
            element = [replace_float(item) for item in element]
            y_list[i] = element
            minvals = np.min(element, axis=0)
            for val in range((size_per_state + output_size)):
                if minvals[val]<min_value[val]:
                    min_value[val] = minvals[val]
            y_list[i].extend([[-1]*(size_per_state + output_size)]*(max_non_determinism-len(element)))
        y_list = np.array(y_list)

        y_metadata = dict()
        y_metadata["variables"] = [f"so_{i}" for i in range(size_per_state)]
        y_metadata["variables"].extend([f"o_{i}" for i in range(output_size)])
        y_metadata["min"] = [int(i) for i in min_value]
        y_metadata["max"] = [i for i in np.amax(y_list, axis=(0,1))]
        y_metadata["step_size"] = [1 for _ in x[0]]

        y = np.zeros((np.shape(y_list)[2],np.shape(y_list)[0],np.shape(y_list)[1]))
        for i in range(np.shape(y_list)[2]):
            y[i,:,:] = y_list[:,:,i]

        x_metadata = dict()
        x_metadata["variables"] = [f"i_{i}" for i in range(input_size)]
        x_metadata["variables"].extend([f"s_{i}" for i in range(size_per_state)])
        x_metadata["categorical"] = []
        x_metadata["min"] = [int(i) for i in np.amin(x, axis=0)]
        x_metadata["max"] = [int(i) for i in np.amax(x, axis=0)]
        x_metadata["step_size"] = [1 for _ in x[0]]


        logging.debug(x_metadata)
        logging.debug(y_metadata)

        #action_index_mapping = {k: element for k,element in enumerate(np.unique(y_list.reshape(-1,y_list.shape[-1]), axis=0))}


        return (x, x_metadata, y, y_metadata, unique_label_to_float)
