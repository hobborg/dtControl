#!/usr/bin/env python

"""
README

Run dtcontrol --help to see usage.
"""

import argparse
import logging
import re
import shutil
import sys
from collections import namedtuple, OrderedDict
from os import makedirs, remove, path
from os.path import exists, isfile, splitext
import platform
from typing import Tuple, Union, List

import pkg_resources
from pkg_resources import Requirement, resource_filename
from ruamel.yaml import YAML
from ruamel.yaml.scanner import ScannerError
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from tabulate import tabulate

from dtcontrol.benchmark_suite import BenchmarkSuite
from dtcontrol.decision_tree.decision_tree import DecisionTree
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
from dtcontrol.decision_tree.splitting.linear_classifier import LinearClassifierSplittingStrategy
from dtcontrol.decision_tree.splitting.oc1 import OC1SplittingStrategy
from dtcontrol.post_processing.safe_pruning import SafePruning
# Import preprocessing strategies
from dtcontrol.pre_processing.norm_pre_processor import NormPreProcessor
from dtcontrol.pre_processing.random_pre_processor import RandomPreProcessor

import json, ast
import numpy as np

def get_classifier(numeric_split, categorical_split, determinize, impurity, tolerance=1e-5, safe_pruning=False,
                    name=None):
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

def intoJSON(rt,parent):
    # returns a string
    rt_name = "sth"
    if(len(rt.children)>0):
        rt_name = rt.split.print_c()
    else:
        rt_name = rt.print_c_label()
    # print("Working on ",rt_name," with ",len(rt.children)," children\n")
    strdummy = {"name": rt_name,"parent": parent,"coleur": "white","children": []}
    for i in range(len(rt.children)):
        strdummy["children"].append(intoJSON(rt.children[i],rt_name))
    return strdummy

def main_parse(args):
    # args will be passed as a dict to this function
    kwargs = dict()

    dataset = path.realpath(path.dirname(__file__))+"/../examples/"+args["controller"]
    # print(dataset)
    is_valid_file_or_folder(dataset)

    kwargs["timeout"] = 20 * 60 * 60

    kwargs["benchmark_file"] = 'benchmark'

    suite = BenchmarkSuite(**kwargs)
    suite.add_datasets(dataset)

    # Parse config files
    default_config: OrderedDict = load_default_config()
    user_config: Union[None, OrderedDict] = None

    classifiers = []
    run_config_table = []
    Row = namedtuple('Row',
                        ['Name', 'NumericPredicate', 'CategoricalPredicate', 'Determinize', 'Impurity', 'Tolerance',
                        'SafePruning'])

    if "config" in args.keys():
        presets = args["config"]
        numeric_split, categorical_split, determinize, impurity, tolerance, safe_pruning = get_preset(presets, user_config, default_config)
    else:
        presets = "default"
        numeric_split = args["numeric-predicates"]
        categorical_split = args["categorical-predicates"]
        determinize = args["determinize"]
        impurity = args["impurity"]
        tolerance = float(args["tolerance"])
        safe_pruning = (args["safe-pruning"]=="true")

    try:
        classifier = get_classifier(numeric_split, categorical_split, determinize, impurity,
                                    tolerance=tolerance,
                                    safe_pruning=safe_pruning, name=presets)
    except EnvironmentError:
        logging.warning(f"WARNING: Could not instantiate a classifier for preset '{presets}'. This could be "
                        f"because the preset '{presets}' is not supported on this platform. Skipping...\n")
    except Exception:
        logging.warning(f"WARNING: Could not instantiate a classifier for preset '{presets}'. Skipping...\n")

    classifiers.append(classifier)
    run_config_table.append(
        Row(Name=presets, NumericPredicate=numeric_split, CategoricalPredicate=categorical_split,
            Determinize=determinize, Impurity=impurity, Tolerance=tolerance,
            SafePruning=safe_pruning))

    if not classifiers:
        logging.warning(
            "No valid preset selected. Please try again with the correct preset name. Use 'dtcontrol preset --list' to see valid presets.")
        sys.exit("Exiting...")

    # suite.benchmark(classifiers)
    suite.datasets[0].load_if_necessary()
    #benchmark does a lot of other stuff as well, we just need load if necessary from it
    classifiers[0].fit(suite.datasets[0])
    # print("Tried fit now printing root")

    # json_str = []
    retDict = intoJSON(classifiers[0].root,"null")
    # classifiers[0].root.predict_one_step(np.array([[3.5, 0]]))
    # print((classifiers[0].get_stats()))

    # print(suite.datasets[0].x_metadata)
    # print(suite.datasets[0].y_metadata)
    
    # print("Retdict type ",type(retDict))
    # json_str=json.dumps(retDict)
    return retDict,suite.datasets[0].x_metadata,suite.datasets[0].y_metadata, classifiers[0].root