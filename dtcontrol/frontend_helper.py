#!/usr/bin/env python

"""
README

Run dtcontrol --help to see usage.
"""

import logging
import random
import sys
import time
from collections import namedtuple, OrderedDict
from os import path
from os.path import exists
from typing import Tuple, Union

import pkg_resources
from pkg_resources import Requirement, resource_filename
from ruamel.yaml import YAML
from ruamel.yaml.scanner import ScannerError
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC

from dtcontrol.benchmark_suite import BenchmarkSuite
from dtcontrol.dataset.multi_output_dataset import MultiOutputDataset
from dtcontrol.dataset.single_output_dataset import SingleOutputDataset
from dtcontrol.decision_tree.decision_tree import DecisionTree, Node
from dtcontrol.decision_tree.determinization.label_powerset_determinizer import LabelPowersetDeterminizer
# Import determinizers
from dtcontrol.decision_tree.determinization.max_freq_determinizer import MaxFreqDeterminizer
# Import impurity measures
from dtcontrol.decision_tree.impurity.auroc import AUROC
from dtcontrol.decision_tree.impurity.entropy import Entropy
from dtcontrol.decision_tree.impurity.gini_index import GiniIndex
from dtcontrol.decision_tree.impurity.max_minority import MaxMinority
from dtcontrol.decision_tree.impurity.multi_label_entropy import MultiLabelEntropy
from dtcontrol.decision_tree.impurity.multi_label_gini_index import MultiLabelGiniIndex
from dtcontrol.decision_tree.impurity.multi_label_twoing_rule import MultiLabelTwoingRule
from dtcontrol.decision_tree.impurity.twoing_rule import TwoingRule
# Import splitting strategies
from dtcontrol.decision_tree.splitting.axis_aligned import AxisAlignedSplittingStrategy
from dtcontrol.decision_tree.splitting.categorical_multi import CategoricalMultiSplittingStrategy
from dtcontrol.decision_tree.splitting.categorical_single import CategoricalSingleSplittingStrategy
from dtcontrol.decision_tree.splitting.context_aware.richer_domain_cli_strategy import RicherDomainCliStrategy
from dtcontrol.decision_tree.splitting.linear_classifier import LinearClassifierSplittingStrategy
from dtcontrol.decision_tree.splitting.oc1 import OC1SplittingStrategy
from dtcontrol.post_processing.safe_pruning import SafePruning
from dtcontrol.decision_tree.splitting.context_aware.richer_domain_splitting_strategy import RicherDomainSplittingStrategy
from dtcontrol.decision_tree.splitting.split import Split
# Import preprocessing strategies
from dtcontrol.pre_processing.norm_pre_processor import NormPreProcessor
from dtcontrol.pre_processing.random_pre_processor import RandomPreProcessor


# Subset of cli.py with core_parser replaced with train
from dtcontrol.util import Caller


def get_classifier(numeric_split, categorical_split, determinize, impurity, tolerance=1e-5, safe_pruning=False,
                   name=None, user_predicates=None, fallback=None):
    """
    Creates classifier objects for each method

    :param name:
    :param safe_pruning:
    :param impurity:
    :param determinize:
    :param split:
    :param tolerance:
    :param value_grouping:
    :return: list of classifier objects
    """

    combined_split = numeric_split + categorical_split
    # Give the preset a name, if doesn't exist
    if not name:
        name = f"{determinize}-({','.join(combined_split)})-{impurity}"

    if not isinstance(tolerance, float):
        raise ValueError(f"{tolerance} is not a valid tolerance value (enter a float, e.g., 1e-5). Exiting...")

    if not isinstance(safe_pruning, bool):
        raise ValueError(f"{safe_pruning} is not a valid value for safe-pruning in preset {name}. Exiting...")

    determinization_map = {
        'maxfreq': lambda x: MaxFreqDeterminizer(),
        'minnorm': lambda x: NormPreProcessor(min),
        'maxnorm': lambda x: NormPreProcessor(max),
        'random': lambda x: RandomPreProcessor(),
        'none': lambda x: LabelPowersetDeterminizer(),
        'auto': lambda x: MaxFreqDeterminizer()
    }
    splitting_map = {
        'axisonly': lambda x: AxisAlignedSplittingStrategy(),
        'linear-logreg': lambda x: LinearClassifierSplittingStrategy(LogisticRegression, determinizer=x,
                                                                     solver='lbfgs', penalty='none'),
        'linear-linsvm': lambda x: LinearClassifierSplittingStrategy(LinearSVC, determinizer=x, max_iter=5000),
        'oc1': lambda x: OC1SplittingStrategy(determinizer=x),
        'multisplit': lambda x: CategoricalMultiSplittingStrategy(value_grouping=False),
        'singlesplit': lambda x: CategoricalSingleSplittingStrategy(),
        'valuegrouping': lambda x: CategoricalMultiSplittingStrategy(value_grouping=True, tolerance=tolerance),
        'richer-domain': lambda x, y: RicherDomainSplittingStrategy(user_given_splits=x, determinizer=y),
    }
    impurity_map = {
        'auroc': lambda x: AUROC(determinizer=x),
        'entropy': lambda x: Entropy(determinizer=x),
        'gini': lambda x: GiniIndex(determinizer=x),
        'maxminority': lambda x: MaxMinority(determinizer=x),
        'twoing': lambda x: TwoingRule(determinizer=x),
        'multilabelentropy': lambda x: MultiLabelEntropy(),
        'multilabelgini': lambda x: MultiLabelGiniIndex(),
        'multilabeltwoing': lambda x: MultiLabelTwoingRule(),
    }

    # Sanity check
    for sp in combined_split:
        if sp not in splitting_map:
            raise ValueError(f"{sp} is not a valid predicate type in preset {name}. Exiting...")

    if determinize not in determinization_map:
        raise ValueError(f"{determinize} is not a valid determinization strategy in preset {name}. Exiting...")

    if impurity not in impurity_map:
        raise ValueError(f"{impurity} is not a valid impurity measure in preset {name}. Exiting...")

    # Handle necessary cases which make the user interface simple
    label_pre_processor = None
    early_stopping = False
    if determinize in ['minnorm', 'random']:
        label_pre_processor = determinization_map[determinize](None)
        determinize = "none"
    if (determinize in ['maxfreq', 'auto']):
        early_stopping = True

    # determinizer must be auto when using multilablestuff
    if 'multilabel' in impurity:
        if not determinize == "auto":
            logging.error(
                f"{impurity} impurity measure automatically determinizes. Please use 'determinize: auto' when defining the preset.")
            sys.exit(-1)

    # if auto is used with any other, then give info message saying we use maxfreq
    if 'multilabel' not in impurity:
        if determinize == "auto":
            logging.info(
                f"INFO: Using the recommended maxfreq determinizer since the preset contained 'determinize: auto'.")
            determinize = "maxfreq"

    # if using logreg/svm/oc1, then determinizer must be passed to the split
    splitting_strategy = []
    for sp in combined_split:
        if sp in ['linear-logreg', 'linear-linsvm', 'oc1']:
            splitting_strategy.append(splitting_map[sp](determinization_map[determinize](None)))
        elif sp in ['richer-domain']:
            splitting_strategy.append(splitting_map[sp](user_predicates, determinization_map[determinize](None)))
            if fallback:
                # add fallbacks to strategy
                for fallback_sp in fallback[0]+fallback[1]:
                    if fallback_sp in ['linear-logreg', 'linear-linsvm', 'oc1']:
                        f_sp = splitting_map[fallback_sp](determinization_map[determinize](None))
                        f_sp.priority = 0
                        splitting_strategy.append(f_sp)
                    else:
                        f_sp = splitting_map[fallback_sp](None)
                        f_sp.priority = 0
                        splitting_strategy.append(f_sp)
        else:
            splitting_strategy.append(splitting_map[sp](None))

    impurity_measure = impurity_map[impurity](determinization_map[determinize](None))

    classifier = DecisionTree(splitting_strategy, impurity_measure, name,
                              early_stopping=early_stopping, label_pre_processor=label_pre_processor)

    if safe_pruning:
        logging.info(f"Enabling safe pruning for preset {name}")
        classifier = SafePruning(classifier)

    # returns a flattened list
    return classifier


def load_default_config() -> OrderedDict:
    try:
        default_config_file = resource_filename(Requirement.parse("dtcontrol"),
                                                "dtcontrol/config.yml")  # System-level config file
    except pkg_resources.DistributionNotFound:
        sys.exit(
            f"pkg_resources could not find a distribution called 'dtcontrol'. Please report this error to the developers.")

    try:
        yaml = YAML()
        default_config = yaml.load(open(default_config_file))
    except FileNotFoundError:
        sys.exit(f"Error finding the default config file. Please raise an issue with the developers.")
    except ScannerError:
        sys.exit(
            f"Scan error in the default YAML configuration file '{default_config_file}'. Please raise an issue with the developers.")
    return default_config


def get_key_or_default(preset_dict: OrderedDict, default_dict: OrderedDict, key: str):
    if key in preset_dict:
        return preset_dict[key]
    else:
        return default_dict[key]


def get_preset(preset: str, user_config: OrderedDict, default_config: OrderedDict) -> Tuple:
    if user_config and preset in user_config['presets']:
        value = user_config['presets'][preset]
    elif preset in default_config['presets']:
        value = default_config['presets'][preset]
    else:
        sys.exit(f"Preset '{preset}' not found.\n"
                 f"Please ensure that the specified config file contains a "
                 f"configuration called '{preset}'. You may run the command\n"
                 f"\tdtcontrol preset --sample > user-config.yml\n"
                 f"to generate a configuration file and use it with the help of the "
                 f"--config and --use-preset switches (see help).\n"
                 f"Refer to the User Manual (https://dtcontrol.readthedocs.io/) for details on how to write presets.")

    default_value = default_config['presets']['default']

    # Obtain the different settings from the value dict
    # In case something is not defined, choose the default from default_value dict
    for key in value.keys():
        if key not in ['numeric-predicates', 'categorical-predicates', 'determinize', 'impurity', 'tolerance',
                       'safe-pruning']:
            logging.warning(f"Ignoring unknown key {key} specified under preset {preset}.")

    numeric_predicates = get_key_or_default(value, default_value, 'numeric-predicates')
    categorical_predicates = get_key_or_default(value, default_value, 'categorical-predicates')
    determinize = get_key_or_default(value, default_value, 'determinize')
    impurity = get_key_or_default(value, default_value, 'impurity')
    tolerance = get_key_or_default(value, default_value, 'tolerance')
    safe_pruning = get_key_or_default(value, default_value, 'safe-pruning')

    return numeric_predicates, categorical_predicates, determinize, impurity, tolerance, safe_pruning


def is_valid_file_or_folder(arg):
    if not exists(arg):
        logging.error(f"The file/folder {arg} does not exist.")
        sys.exit(1)
    else:
        return arg


def intoJSON(rt, parent, address, y_metadata):
    # returns a string (JSON format that we need)
    # address is an array of integers
    if len(rt.children) > 0:
        rt_name = rt.split.print_c()
    else:
        try:
            # rt_name = rt.print_c_label()
            rt_name = rt.print_dot_label(y_metadata)
        except ValueError:
            # In interactive tree building, we often get trees that are incomplete
            # for such trees, print_c_label() throws an exception.
            rt_name = "Not yet homogeneous"
    strdummy = {"name": rt_name, "parent": parent, "coleur": "white", "children": [], "address": address}
    for i in range(len(rt.children)):
        strdummy["children"].append(intoJSON(rt.children[i], rt_name, address + [i], y_metadata))
    return strdummy

def get_mask_given_address(existing_tree=None, node_address=None, dataset=None):
    # Navigate to node_address in the saved_tree and call get_mask
    pointer: Node = existing_tree
    mask = pointer.split.get_masks(dataset)[node_address[0]]
    for pos in node_address:
        mask = [a and b for a, b in zip(mask, pointer.split.get_masks(dataset)[pos])]
        pointer = pointer.children[pos]
    # Get the split masks (one for each child) from the parent and pick the correct child
    # TODO P: we have to OR all the masks that lead up to this child node!
    return mask

def mask_as_int(mask):
    return int("".join([str(e) for e in [1] + list(map(int, mask))]), 2)

def train(args):
    # args will be passed as a dict to this function
    # works exactly like core_parser in cli.py
    # kwargs = dict()

    file = args["controller"]
    is_valid_file_or_folder(file)

    # kwargs["timeout"] = 20 * 60 * 60
    #
    # kwargs["benchmark_file"] = 'benchmark'

    # suite = BenchmarkSuite(**kwargs)
    # suite.add_datasets(dataset)
    ext = file.split(".")[-1]
    if BenchmarkSuite.is_multiout(file, ext):
        ds = MultiOutputDataset(file)
    else:
        ds = SingleOutputDataset(file)

    ds.is_deterministic = BenchmarkSuite.is_deterministic(file, ext)

    # Parse config files
    default_config: OrderedDict = load_default_config()
    user_config: Union[None, OrderedDict] = None

    fallback_numeric, fallback_categorical = None, None
    user_predicates = None

    # if "partial" in args.keys():
    #     if args["partial"]["address"]:
    #         ds.from_mask()

    if "config" in args.keys():
        presets = args["config"]

        if "algebraic" in presets:
            presets = args["config"]
            numeric_split = ["richer-domain"]
            categorical_split = []
            determinize = args["determinize"]
            impurity = args["impurity"]
            tolerance = float(args["tolerance"])
            safe_pruning = (args["safe-pruning"] == "true")
            fallback_numeric = get_preset(args["fallback"], user_config, default_config)[0]
            fallback_categorical = get_preset(args["fallback"], user_config, default_config)[1]
            user_predicates = args["user_predicates"]
        else:
            numeric_split, categorical_split, determinize, impurity, tolerance, safe_pruning = get_preset(presets,
                                                                                                          user_config,
                                                                                                          default_config)
    else:
        presets = "default"
        numeric_split = args["numeric-predicates"]
        categorical_split = args["categorical-predicates"]
        determinize = args["determinize"]
        impurity = args["impurity"]
        tolerance = float(args["tolerance"])
        safe_pruning = (args["safe-pruning"] == "true")

    classifier = None
    try:
        classifier = get_classifier(numeric_split, categorical_split, determinize, impurity,
                                    tolerance=tolerance,
                                    safe_pruning=safe_pruning, name=presets, user_predicates=user_predicates,
                                    fallback=(fallback_numeric, fallback_categorical))
    except EnvironmentError:
        logging.warning(f"WARNING: Could not instantiate a classifier for preset '{presets}'. This could be "
                        f"because the preset '{presets}' is not supported on this platform. Skipping...\n")
    except Exception:
        logging.warning(f"WARNING: Could not instantiate a classifier for preset '{presets}'. Skipping...\n")

    if not classifier:
        logging.warning(
            "No valid preset selected. Please try again with the correct preset name. Use 'dtcontrol preset --list' to see valid presets.")
        sys.exit("Exiting...")

    logging.info("Frontend: loading dataset...")
    ds.load_if_necessary()

    if "existing_tree" in args:
        if args["base_node_address"]:
            mask = get_mask_given_address(existing_tree=args["existing_tree"], node_address=args["base_node_address"],
                                          dataset=ds)
            ds = ds.from_mask(mask)
            ds.is_deterministic = BenchmarkSuite.is_deterministic(file, ext)

    start = time.time()
    # benchmark does a lot of other stuff as well, we just need load if necessary from it

    logging.info("Frontend: fitting dataset to tree...")
    classifier.fit(ds)
    logging.info("Frontend: tree constructed.")
    run_time = time.time() - start
    # intoJSON takes the classifier root and returns a JSON in required format
    try:
        address = args["base_node_address"]
    except KeyError:
        address = []
    classifier_as_json = intoJSON(classifier.root, "null", address, ds.y_metadata)
    return {
        "classifier": classifier, "classifier_as_json": classifier_as_json,
        "x_metadata": ds.x_metadata, "y_metadata": ds.y_metadata,
        "run_time": run_time
    }


def interactive(args):
    file = args["controller"]
    is_valid_file_or_folder(file)

    ext = file.split(".")[-1]
    if BenchmarkSuite.is_multiout(file, ext):
        ds = MultiOutputDataset(file)
    else:
        ds = SingleOutputDataset(file)

    ds.is_deterministic = BenchmarkSuite.is_deterministic(file, ext)

    classifier = DecisionTree([RicherDomainCliStrategy()], Entropy(), 'Interactive-Entropy', early_stopping=True)

    logging.info("Frontend: loading dataset...")
    ds.load_if_necessary()

    if "existing_tree" in args:
        if args["base_node_address"]:
            mask = get_mask_given_address(existing_tree=args["existing_tree"], node_address=args["base_node_address"],
                                          dataset=ds)
            ds = ds.from_mask(mask)
            ds.is_deterministic = BenchmarkSuite.is_deterministic(file, ext)

    start = time.time()
    # benchmark does a lot of other stuff as well, we just need load if necessary from it

    logging.info("Frontend: fitting dataset to tree...")
    classifier.fit(ds, caller=Caller.WEBUI, rounds=1)
    logging.info("Frontend: tree constructed.")
    run_time = time.time() - start
    # intoJSON takes the classifier root and returns a JSON in required format
    try:
        address = args["base_node_address"]
    except KeyError:
        address = []
    classifier_as_json = intoJSON(classifier.root, "null", address, ds.y_metadata)
    return {
        "classifier": classifier, "classifier_as_json": classifier_as_json,
        "x_metadata": ds.x_metadata, "y_metadata": ds.y_metadata,
        "run_time": run_time
    }

def get_random_point_from_dataset(controller_file):
    is_valid_file_or_folder(controller_file)
    ext = controller_file.split(".")[-1]
    if BenchmarkSuite.is_multiout(controller_file, ext):
        ds = MultiOutputDataset(controller_file)
    else:
        ds = SingleOutputDataset(controller_file)
    ds.load_if_necessary()
    discrete_point = random.choice(ds.x)
    return discrete_point


def start_websocket_with_frontend():
    from websocket import create_connection
    ws = create_connection("ws://127.0.0.1:8080")
    print("Sending 'Hello, World'...")
    while True:
        result = ws.recv()
        if result == "CLOSE":
            break
        print("Received '%s'" % result)
        ws.send(f"Thanks for {result}")
    ws.close()