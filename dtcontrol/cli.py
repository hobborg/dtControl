#!/usr/bin/env python

"""
README

Run dtcontrol --help to see usage. Some examples are given below.

Example:
dtcontrol --input controller.scs --output decision_trees --method maxcart

will read controller.scs and use maxcart on it and print the c, dot, vhdl files
into the decision_trees folder


dtcontrol --input controller1.scs controller2.scs --output decision_trees --benchmark_file benchmarks.json

will read controller1.scs and controller2.scs, try out all methods and save the
results in decision_trees; moreover save the run and tree statistics in
benchmark.json and a nice HTML table in benchmark.html


dtcontrol --input dumps --output decision_trees --method all --determinize maxfreq minnorm

will read all valid controllers in dumps, run the determinized variants (using the maxfreq
 and minnorm determinization strategies) of all methods on them and save the decision
trees in decision_trees

"""

import argparse
import logging
import re
import sys
from os import makedirs
from os.path import exists, isfile, splitext

import pkg_resources
from pkg_resources import Requirement, resource_filename

from ruamel.yaml import YAML
from ruamel.yaml.scanner import ScannerError

from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC

from dtcontrol.benchmark_suite import BenchmarkSuite
from dtcontrol.decision_tree.decision_tree import DecisionTree

# Import determinizers
from dtcontrol.decision_tree.determinization.max_freq_determinizer import MaxFreqDeterminizer
from dtcontrol.decision_tree.determinization.max_freq_multi_determinizer import MaxFreqMultiDeterminizer
from dtcontrol.decision_tree.determinization.non_determinizer import NonDeterminizer
from dtcontrol.decision_tree.determinization.norm_determinizer import NormDeterminizer
from dtcontrol.decision_tree.determinization.random_determinizer import RandomDeterminizer

# Import impurity measures
from dtcontrol.decision_tree.impurity.auroc import AUROC
from dtcontrol.decision_tree.impurity.entropy import Entropy
from dtcontrol.decision_tree.impurity.max_minority import MaxMinority

# Import splitting strategies
from dtcontrol.decision_tree.splitting.axis_aligned import AxisAlignedSplittingStrategy
from dtcontrol.decision_tree.splitting.categorical_multi import CategoricalMultiSplittingStrategy
from dtcontrol.decision_tree.splitting.linear_classifier import LinearClassifierSplittingStrategy
from dtcontrol.decision_tree.splitting.oc1 import OC1SplittingStrategy

def main():
    def is_valid_file_or_folder(parser, arg):
        if not exists(arg):
            parser.error(f"The file/folder {arg} does not exist.")
        else:
            return arg

    def is_valid_file(parser, arg):
        if not isfile(arg):
            parser.error(f"The file {arg} does not exist. Give a valid JSON file path.")
        else:
            return arg

    def load_default_config():
        default_config = None

        try:
            default_config_file = resource_filename(Requirement.parse("dtcontrol"),"config.yml") # System-level config file
        except pkg_resources.DistributionNotFound:
            sys.exit(f"pkg_resources could not find a distribution called 'dtcontrol'. Please report this error to the developers.")

        try:
            default_config = yaml.load(open(default_config_file))
        except FileNotFoundError:
            sys.exit(f"Error finding the default config file. Please raise an issue with the developers.")
        except ScannerError:
            sys.exit(f"Scan error in the default YAML configuration file '{default_config_file}'. Please raise an issue with the developers.")
        return default_config

    def parse_timeout(timeout_string: str):
        """
        Parses the timeout string

        :param timeout_string: string describing timeout - an integer suffixed with s, m or h
        :return: timeout in seconds
        """
        # Default timeout set to 2 hours
        unit_to_factor = {'s': 1, 'm': 60, 'h': 3600}
        if re.match(r'^[0-9]+[smh]$', timeout_string):
            factor = unit_to_factor[timeout_string[-1]]
            timeout = int(args.timeout[:-1]) * factor
        else:
            # In case s, m or h is missing; then interpret number as timeout in seconds
            try:
                timeout = int(timeout_string)
            except ValueError:
                parser.error("Invalid value passed as timeout.")
        return timeout

    def get_classifiers(split, determinize, impurity, name=None):
        """
        Creates classifier objects for each method

        :param methods: list of method strings
        :param det_strategies: list of determinization strategies
        :return: list of classifier objects
        """

        determinization_map = {
            'maxfreq': MaxFreqDeterminizer(),
            'maxmultifreq': MaxFreqMultiDeterminizer(),
            'none': NonDeterminizer(),
            'maxnorm': NormDeterminizer(max),
            'minnorm': NormDeterminizer(min),
            'random': RandomDeterminizer(),
        }
        splitting_map = {
            'axisonly': AxisAlignedSplittingStrategy(),
            'categorical': CategoricalMultiSplittingStrategy(),
            'linear-logreg': LinearClassifierSplittingStrategy(LogisticRegression, solver='lbfgs', penalty='none'),
            'linear-linsvm': LinearClassifierSplittingStrategy(LinearSVC, max_iter=5000),
            'oc1': OC1SplittingStrategy()
        }
        impurity_map = {
            'auroc': AUROC(),
            'entropy': Entropy(),
            'maxminority': MaxMinority()
        }

        # Sanity check
        if "all" in split:
            split = splitting_map.keys()
        else:
            for sp in split:
                if sp not in splitting_map:
                    raise ValueError(f"{sp} is not a valid argument for the --split switch. Exiting...")

        if determinize == "all":
            determinize = determinization_map.keys()
        else:
            if determinize not in determinization_map:
                raise ValueError(f"{det} is not a valid determinization strategy. Exiting...")
            else:
                determinize = [determinize]

        if impurity == "all":
            impurity = impurity_map.keys()
        else:
            if impurity not in impurity_map:
                raise ValueError(f"{imp} is not a valid impurity measure. Exiting...")
            else:
                impurity = [impurity]

        # construct all possible method - determinization strategy combinations
        classifiers = []

        for det in determinize:
            assert det in determinization_map
            for imp in impurity:
                assert imp in impurity_map
                if not name:
                    name = f"{det}-({','.join(split)})-{imp}"
                classifier = DecisionTree(determinization_map[det],
                                          [splitting_map[sp] for sp in split],
                                          impurity_map[imp],
                                          name)
                classifiers.append(classifier)

        # returns a flattened list
        return classifiers

    logging.basicConfig(level=logging.INFO, format='%(message)s')

    parser = argparse.ArgumentParser(prog="dtcontrol")

    version = pkg_resources.require("dtcontrol")[0].version
    parser.add_argument("-v", "--version", action='version',
                        version=f'%(prog)s {version}')

    parser.add_argument("--benchmark-file", "-b", metavar="FILENAME", type=str,
                        help="Saves statistics pertaining the construction of the decision trees and their "
                             "sizes into a JSON file, and additionally allows to view it via an HTML file.")

    parser.add_argument("--config", "-c", metavar="CONFIGFILE", type=str,
                        help="Specify location of a YAML file containing run configurarions. Use along with the "
                             "--presets switch. More details in the User Manual.")

    parser.add_argument("--determinize", "-d", metavar='DETSTRATEGY', default='none',
                        help="In case of non-deterministic controllers, specify, if desired, the determinization "
                             "strategy. Possible options are 'none', 'maxfreq', 'maxmultifreq', 'maxnorm', 'minnorm' "
                             "and 'random'. If the option 'none' is passed, then the controller is not determinized. "
                             "The shorthand '-d all' tries to run all methods with all determinization strategies.")

    parser.add_argument("--impurity", "-m", default='entropy',
                        help="The impurity switch takes in one or more space separated impurity measures as "
                             "arguments. Available impurity measures are: 'auroc', 'entropy' and 'maxminority'. "
                             "If this switch is omitted, defaults to using 'entropy'.")

    parser.add_argument("--input", "-i", nargs="+", type=(lambda x: is_valid_file_or_folder(parser, x)),
                        help="The input switch takes in one or more space separated file names or "
                             "a folder name which contains valid controllers (.scs, .dump or .csv)")

    parser.add_argument("--output", "-o", type=str,
                        help="The output switch takes in a path to a folder where the constructed controller "
                             "representation would be saved (c and dot)")

    parser.add_argument("--presets", "-p", type=str, nargs="+",
                        help="Run one or more presets defined in the CONFIGFILE. If the --config switch has not "
                             "been used, then presets are chosen from the system-level configuration file. Refer "
                             "the User Manual for more details.")

    parser.add_argument("--split", "-s", default=['axisonly'], nargs="+",
                        help="The split switch takes in one or more space separated splitting strategies as "
                             "arguments. Available strategies are: 'axisonly', 'categorical', 'linear-logreg', "
                             "'linear-linsvm' and 'oc1'. This switch determines the set of predicates from which "
                             "each splitting predicate will be drawn. Running with '--split all' will attempt to "
                             "use all possible splitting predicates. If this switch is omitted, defaults to "
                             "'axisonly' splits.")

    parser.add_argument("--rerun", "-r", action='store_true',
                        help="Rerun the experiment for all input-method combinations. Overrides the default "
                             "behaviour of not running benchmarks for combinations which are already present"
                             " in the benchmark file.")

    parser.add_argument("--timeout", "-t", type=str,
                        help="Sets a timeout for each method. Can be specified in seconds, minutes "
                             "or hours (eg. 300s, 7m or 3h)")

    args = parser.parse_args()

    kwargs = dict()

    if args.input:
        dataset = args.input
    else:
        parser.print_help()
        sys.exit()

    kwargs["timeout"] = 2 * 60 * 60
    if args.timeout:
        kwargs["timeout"] = parse_timeout(args.timeout)

    if args.benchmark_file:
        filename, file_extension = splitext(args.benchmark_file)
        kwargs["benchmark_file"] = filename
    else:
        kwargs["benchmark_file"] = 'benchmark'
        logging.warning("--benchmark-file/-b was not set. Defaulting to use 'benchmark.json'")

    if args.output:
        try:
            makedirs(args.output, exist_ok=True)
            kwargs["output_folder"] = args.output
        except PermissionError:
            sys.exit("Ensure permission exists to create output directory")

    kwargs["rerun"] = args.rerun
    if not args.rerun and isfile(kwargs["benchmark_file"]):
        logging.warning(
            f"Dataset - method combinations whose results are already present in '{kwargs['benchmark_file']}' "
            f"would not be re-run. Use the --rerun flag if this is what is desired.")

    suite = BenchmarkSuite(**kwargs)
    suite.add_datasets(dataset)


    # Parse config files
    yaml = YAML()

    default_config = load_default_config()
    user_config = None

    if args.config:
        try:
            user_config = yaml.load(open(args.config))
        except FileNotFoundError:
            sys.exit(f"Error finding the config file. Please check if the file '{args.config}' exists in the current directory")
        except ScannerError:
            sys.exit(f"Scan error in the YAML configuration file '{args.config}'. Please re-check syntax.")

    def get_preset(preset, user_config, default_config):
        if user_config and preset in user_config['custom']:
            value = user_config['custom'][preset]
        elif preset in default_config['presets']:
            value = default_config['presets'][preset]
        else:
            sys.exit(f"Preset '{preset}' not found. Please ensure that the specified config file contains a configuration called {preset}. Refer to the User Manual for details on how to write presets.")
            return None
        return value['predicates'], value['determinize'], value['impurity']

    classifiers = []
    if args.presets:
        for preset in args.presets:
            split, determinize, impurity = get_preset(preset, user_config, default_config)
            classifiers.extend(get_classifiers(split, determinize, impurity, name=preset))

        if args.split or args.determinize or args.impurity:
            logging.warning("WARNING: Since --presets switch is used to define run configurarions, ignoring the --split, --determinize and --impurity switches.\n")

    if not args.presets:
        classifiers = get_classifiers(args.split, args.determinize, args.impurity)
    if not classifiers:
        sys.exit("Could not find any valid method - determinization strategy combinations. "
                 "Please read the manual for valid combinations and try again.")

    suite.benchmark(classifiers)


if __name__ == "__main__":
    main()
