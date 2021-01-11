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
from os import makedirs, remove
from os.path import exists, isfile, splitext
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

    def parse_timeout(timeout_string: str) -> int:
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

    def preset_parser(args):
        if args.list:
            system_config = load_default_config()
            user_config = None

            if args.config:
                try:
                    yaml = YAML()
                    user_config = yaml.load(open(args.config))
                except FileNotFoundError:
                    sys.exit(
                        f"Error finding the config file. Please check if the file '{args.config}' exists in the current directory")
                except ScannerError:
                    sys.exit(f"Scan error in the YAML configuration file '{args.config}'. Please re-check syntax.")
                else:
                    if 'presets' not in user_config:
                        logging.warning("WARNING: config file does not contain the 'presets' key. "
                                        "No user configurations could be loaded. Ensure that user presets "
                                        "are defined under the presets key.\n")
            else:
                logging.info("WARNING: --config switch not used, only loading pre-defined run configurations.")

            list_presets(user_config, system_config)
        elif args.sample:
            print("# Paste the following contents into a .yml file and \n"
                  "# pass the file to dtcontrol using --config <filename>.yml\n"
                  "presets:\n"
                  "  my-config:\n"
                  "    determinize: maxfreq\n"
                  "    numeric-predicates: ['axisonly']\n"
                  "    categorical-predicates: ['singlesplit']\n"
                  "    impurity: 'entropy'\n"
                  "    safe-pruning: False\n"
                  "  another-config:\n"
                  "    determinize: minnorm\n"
                  "    numeric-predicates: ['linear-logreg']\n"
                  "    categorical-predicates: ['valuegrouping']\n"
                  "    tolerance: 10e-4\n"
                  "    safe-pruning: False")
        else:
            parser_conf.print_help()

        sys.exit(0)

    def get_key_or_default(preset_dict: OrderedDict, default_dict: OrderedDict, key: str):
        if key in preset_dict:
            return preset_dict[key]
        else:
            return default_dict[key]

    def get_key_or_empty(preset_dict: OrderedDict, default_dict: OrderedDict, key: str):
        if key in preset_dict:
            return preset_dict[key]
        else:
            return ""

    def list_presets(user_config: OrderedDict, system_config: OrderedDict):
        Row = namedtuple('Row',
                         ['Name', 'NumericPredicate', 'CategoricalPredicate', 'Determinize', 'Impurity', 'Tolerance',
                          'SafePruning'])

        run_config_table = []
        default_value: OrderedDict = load_default_config()['presets']['default']

        if user_config and 'presets' in user_config:
            for preset in user_config['presets']:
                value = user_config['presets'][preset]
                run_config_table.append(Row(Name=preset,
                                            NumericPredicate=get_key_or_default(value, default_value,
                                                                                'numeric-predicates'),
                                            CategoricalPredicate=get_key_or_empty(value, default_value,
                                                                                  'categorical-predicates'),
                                            Determinize=get_key_or_default(value, default_value, 'determinize'),
                                            Impurity=get_key_or_default(value, default_value, 'impurity'),
                                            Tolerance=get_key_or_empty(value, default_value, 'tolerance'),
                                            SafePruning=get_key_or_empty(value, default_value, 'safe-pruning')))

        if run_config_table:
            logging.info("The following user presets (run configurations) are available:\n")
            logging.info(tabulate(run_config_table,
                                  ['name', 'numeric-predicates', 'categorical-predicates', 'determinize', 'impurity',
                                   'tolerance', 'safe-pruning'],
                                  tablefmt="presto"))
            logging.info("\n")

        run_config_table = []
        if system_config and 'presets' in system_config:
            for preset in system_config['presets']:
                value = system_config['presets'][preset]
                run_config_table.append(Row(Name=preset,
                                            NumericPredicate=get_key_or_default(value, default_value,
                                                                                'numeric-predicates'),
                                            CategoricalPredicate=get_key_or_empty(value, default_value,
                                                                                  'categorical-predicates'),
                                            Determinize=get_key_or_default(value, default_value, 'determinize'),
                                            Impurity=get_key_or_default(value, default_value, 'impurity'),
                                            Tolerance=get_key_or_empty(value, default_value, 'tolerance'),
                                            SafePruning=get_key_or_empty(value, default_value, 'safe-pruning')))

        logging.info("The following pre-defined presets (run configurations) are available:\n")
        logging.info(tabulate(run_config_table,
                              ['name', 'numeric-predicates', 'categorical-predicates', 'determinize', 'impurity',
                               'tolerance', 'safe-pruning'],
                              tablefmt="presto"))
        logging.info("\n")
        logging.info("User presets take precedence over pre-defined presets. "
                     "Try running, for example,\n\tdtcontrol --input examples/cartpole.scs --use-preset maxfreq")

    def fetch_presets_from_loaded_config(loaded_config: Union[None, OrderedDict]) -> List[str]:
        if loaded_config:
            return list(loaded_config['presets'].keys())
        else:
            return []

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

    # TODO Make early stopping user definable
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

    def clean_parser(args):
        if args.output_cache:
            clear_output_cache()
        if args.run_cache:
            clear_run_cache()
        if args.all:
            clear_output_cache()
            clear_run_cache()
        sys.exit()


    def clear_run_cache():
        logging.info("Clearing default benchmark files 'benchmark.html' and 'benchmark.json'...")
        if not exists('benchmark.html'):
            logging.warning("The file 'benchmark.html' does not exist. Please run dtcontrol "
                            "from the working directory or clear the run cache manually.")
        if not exists('benchmark.json'):
            logging.warning("The file 'benchmark.json' does not exist. Please run dtcontrol "
                            "from the working directory or clear the run cache manually.")
            sys.exit()
        try:
            remove('benchmark.html')
            remove('benchmark.json')
        except:
            logging.error("Error deleting 'benchmark.html' and 'benchmark.json'. Please delete manually.")
            sys.exit(-1)

    def clear_output_cache():
        logging.info("Clearing default output cache folder 'decision_trees'...")
        if not exists('decision_trees'):
            logging.warning("The folder 'decision_trees' does not exist. Please run dtcontrol "
                            "from the working directory or clear the output manually.")
            sys.exit()
        try:
            shutil.rmtree('decision_trees')
        except:
            logging.error("Error deleting 'decision_trees'. Please delete manually.")
            sys.exit(-1)

    def core_parser(args):
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
            logging.info("--benchmark-file/-b was not set. Defaulting to use 'benchmark.json'")

        if args.output:
            try:
                if args.output.startswith('stdout:'):
                    kwargs["stdout"] = True
                    if args.output == 'stdout:c':
                        kwargs["output_type"] = 'c'
                    elif args.output == 'stdout:dot':
                        kwargs["output_type"] = 'dot'
                    elif args.output == 'stdout:json':
                        kwargs["output_type"] = 'json'
                    else:
                        sys.exit("Invalid stdout type. Use either stdout:c, stdout:dot or stdout:json.")
                else:
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
        default_config: OrderedDict = load_default_config()
        user_config: Union[None, OrderedDict] = None

        if args.config:
            try:
                yaml = YAML()
                user_config = yaml.load(open(args.config))
            except FileNotFoundError:
                sys.exit(
                    f"Error finding the config file. Please check if the file '{args.config}' exists in the current directory")
            except ScannerError:
                sys.exit(f"Scan error in the YAML configuration file '{args.config}'. Please re-check syntax.")

        classifiers = []
        run_config_table = []
        Row = namedtuple('Row',
                         ['Name', 'NumericPredicate', 'CategoricalPredicate', 'Determinize', 'Impurity', 'Tolerance',
                          'SafePruning'])

        if args.use_preset:
            if "all-user" in args.use_preset:
                presets = fetch_presets_from_loaded_config(user_config)
                if not presets:
                    sys.exit("Please specify a user config file via the --config switch. See help for more details.")
            elif "all-system" in args.use_preset:
                presets = fetch_presets_from_loaded_config(default_config)
            elif "all" in args.use_preset:
                presets = fetch_presets_from_loaded_config(user_config) \
                          + fetch_presets_from_loaded_config(default_config)
            else:
                presets = args.use_preset
            for preset in presets:
                numeric_split, categorical_split, determinize, impurity, tolerance, safe_pruning = get_preset(preset,
                                                                                                              user_config,
                                                                                                              default_config)
                try:
                    classifier = get_classifier(numeric_split, categorical_split, determinize, impurity,
                                                tolerance=tolerance,
                                                safe_pruning=safe_pruning, name=preset)
                except EnvironmentError:
                    logging.warning(f"WARNING: Could not instantiate a classifier for preset '{preset}'. This could be "
                                    f"because the preset '{preset}' is not supported on this platform. Skipping...\n")
                    continue
                except Exception:
                    logging.warning(f"WARNING: Could not instantiate a classifier for preset '{preset}'. Skipping...\n")
                    continue

                classifiers.append(classifier)
                run_config_table.append(
                    Row(Name=preset, NumericPredicate=numeric_split, CategoricalPredicate=categorical_split,
                        Determinize=determinize, Impurity=impurity, Tolerance=tolerance,
                        SafePruning=safe_pruning))

        if not args.use_preset:
            logging.info("INFO: Assuming --use-preset default, since no preset explicitly specified.")
            preset = "default"
            numeric_split, categorical_split, determinize, impurity, tolerance, safe_pruning = get_preset(preset,
                                                                                                          user_config,
                                                                                                          default_config)
            try:
                classifier = get_classifier(numeric_split, categorical_split, determinize, impurity,
                                            tolerance=tolerance,
                                            safe_pruning=safe_pruning, name=preset)
            except Exception:
                logging.error("Could not instantiate the default classifier due a runtime error. Exiting...")
                sys.exit(-1)

            classifiers.append(classifier)

            run_config_table.append(
                Row(Name=preset, NumericPredicate=numeric_split, CategoricalPredicate=categorical_split,
                    Determinize=determinize, Impurity=impurity, Tolerance=tolerance,
                    SafePruning=safe_pruning))

        if not classifiers:
            logging.warning(
                "No valid preset selected. Please try again with the correct preset name. Use 'dtcontrol preset --list' to see valid presets.")
            sys.exit("Exiting...")

        logging.info("The following configurations would now be run:\n")
        logging.info(tabulate(run_config_table,
                              ['name', 'numeric-predicates', 'categorical-predicates', 'determinize', 'impurity',
                               'tolerance', 'safe-pruning'],
                              tablefmt="presto"))
        logging.info("\n")

        suite.benchmark(classifiers)

    logging.basicConfig(level=logging.INFO, format='%(message)s')

    parser = argparse.ArgumentParser(prog="dtcontrol",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="Scroll to the end of the help message for Quick Start.",
                                     epilog="Examples:\n"
                                            "Create a file storing run configurations\n"
                                            "    dtcontrol preset --sample > user-config.yml\n\n"
                                            "Display all presets available with dtcontrol\n"
                                            "    dtcontrol preset --config user-config.yml --list\n\n"
                                            "Run the 'my-config' preset on the SCOTS model located at 'examples/cartpole.scs'\n\n"
                                            "    dtcontrol --input examples/cartpole.scs --config user-config.yml --use-preset my-config")
    parser.set_defaults(func=core_parser)

    version = pkg_resources.require("dtcontrol")[0].version
    parser.add_argument("-v", "--version", action='version',
                        version=f'%(prog)s {version}')

    input_output = parser.add_argument_group('input/output')
    input_output.add_argument("--input", "-i", nargs="+", type=(lambda x: is_valid_file_or_folder(parser, x)),
                              help="The input switch takes in one or more space separated file names or "
                                   "a folder name which contains valid controllers (.scs, .dump or .csv)")

    input_output.add_argument("--output", "-o", type=str,
                              help="The output switch takes in a path to a folder where the constructed controller "
                                   "representation would be saved (c and dot). Use --ouptut stdout:c, stdout:dot or "
                                   "stdout:json to print the C, DOT or JSON files into stdout.")

    input_output.add_argument("--benchmark-file", "-b", metavar="FILENAME", type=str,
                              help="Saves statistics pertaining the construction of the decision trees and their "
                                   "sizes into a JSON file, and additionally allows to view it via an HTML file.")

    run_config = parser.add_argument_group('run configurations')
    run_config.add_argument("--config", "-c", metavar="CONFIGFILE", type=str,
                            help="Specify location of a YAML file containing run configurarions. Use along with the "
                                 "--use-preset switch. More details in the User Manual.")

    run_config.add_argument("--use-preset", "-p", type=str, nargs="+",
                            help="Run one or more presets defined in the CONFIGFILE. If the --config switch has not "
                                 "been used, then presets are chosen from the system-level configuration file. Special "
                                 "parameters for this switch include 'all', 'all-user', 'all-system'. Refer the User "
                                 "Manual for more details.")

    run_config.add_argument("--rerun", "-r", action='store_true',
                            help="Rerun the experiment for all input-method combinations. Overrides the default "
                                 "behaviour of not running benchmarks for combinations which are already present"
                                 " in the benchmark file.")

    run_config.add_argument("--timeout", "-t", type=str,
                            help="Sets a timeout for each method. Can be specified in seconds, minutes "
                                 "or hours (eg. 300s, 7m or 3h)")

    subparsers = parser.add_subparsers(title='other commands',
                                       # description = 'Supplementary commands',
                                       help='Run \'dtcontrol COMMAND --help\' to see command specific help')

    parser_conf = subparsers.add_parser(name="preset")
    parser_conf.add_argument("--config", "-c", metavar="CONFIGFILE", type=str,
                             help="Specify location of a YAML file containing run configurarions")
    parser_conf.add_argument("--list", "-l", action='store_true',
                             help="List all available presets (run configurations)")
    parser_conf.add_argument("--sample", "-s", action='store_true',
                             help="Print a sample user configuration file")
    parser_conf.set_defaults(func=preset_parser)

    parser_clean = subparsers.add_parser(name="clean")
    parser_clean.add_argument("--all", "-a", action='store_true',
                              help="Clear cache and outputs")
    parser_clean.add_argument("--run-cache", "-c", action='store_true',
                              help="Clear run cache")
    parser_clean.add_argument("--output-cache", "-o", action='store_true',
                              help="Clear output folder")
    parser_clean.set_defaults(func=clean_parser)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
