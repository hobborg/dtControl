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
from os import makedirs, remove
from os.path import exists, isfile, splitext
import shutil

from collections import namedtuple
from tabulate import tabulate

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
from dtcontrol.decision_tree.impurity.gini_index import GiniIndex
from dtcontrol.decision_tree.impurity.max_minority import MaxMinority
from dtcontrol.decision_tree.impurity.twoing_rule import TwoingRule

# Import splitting strategies
from dtcontrol.decision_tree.splitting.axis_aligned import AxisAlignedSplittingStrategy
from dtcontrol.decision_tree.splitting.categorical_multi import CategoricalMultiSplittingStrategy
from dtcontrol.decision_tree.splitting.linear_classifier import LinearClassifierSplittingStrategy
from dtcontrol.decision_tree.splitting.oc1 import OC1SplittingStrategy  # TODO Doesn't work on MacOS, check
from dtcontrol.post_processing.safe_pruning import SafePruning


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
        try:
            default_config_file = resource_filename(Requirement.parse("dtcontrol"),
                                                    "config.yml")  # System-level config file
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
                    if 'user-presets' not in user_config:
                        logging.warning("WARNING: config file does not contain the 'user-presets' key. "
                                        "No user configurations could be loaded. Ensure that user presets "
                                        "are defined under the user-presets key.\n")
            else:
                logging.info("WARNING: --config switch not used, only loading pre-defined run configurations.")

            list_presets(user_config, system_config)
        elif args.sample:
            print("# Paste the following contents into a .yml file and \n"
                  "# pass the file to dtcontrol using --config <filename>.yml\n"
                  "user-presets:\n"
                  "  my-config:\n"
                  "    determinize: maxfreq\n"
                  "    predicates: ['axisonly']\n"
                  "    impurity: 'entropy'\n"
                  "    safe-pruning: False\n"
                  "  another-config:\n"
                  "    determinize: minnorm\n"
                  "    predicates: ['linear-logreg']\n"
                  "    impurity: 'entropy'\n"
                  "    safe-pruning: False")
        else:
            parser_conf.print_help()

        sys.exit(0)

    def list_presets(user_config, system_config):
        Row = namedtuple('Row', ['Name', 'Predicate', 'Determinize', 'Impurity', 'SafePruning'])

        run_config_table = []
        if user_config and 'user-presets' in user_config:
            for preset in user_config['user-presets']:
                split = user_config['user-presets'][preset]['predicates']
                determinize = user_config['user-presets'][preset]['determinize']
                impurity = user_config['user-presets'][preset]['impurity']
                safe_pruning = user_config['user-presets'][preset]['safe-pruning']
                run_config_table.append(Row(Name=preset, Predicate=split, Determinize=determinize, Impurity=impurity,
                                            SafePruning=safe_pruning))

        if run_config_table:
            logging.info("The following user presets (run configurations) are available:\n")
            print(tabulate(run_config_table, ['name', 'predicates', 'determinize', 'impurity', 'safe-pruning'],
                           tablefmt="presto"), end="\n\n")

        run_config_table = []
        if system_config and 'system-presets' in system_config:
            for preset in system_config['system-presets']:
                split = system_config['system-presets'][preset]['predicates']
                determinize = system_config['system-presets'][preset]['determinize']
                impurity = system_config['system-presets'][preset]['impurity']
                safe_pruning = system_config['system-presets'][preset]['safe-pruning']
                run_config_table.append(Row(Name=preset, Predicate=split, Determinize=determinize, Impurity=impurity,
                                            SafePruning=safe_pruning))

        logging.info("The following pre-defined presets (run configurations) are available:\n")
        print(tabulate(run_config_table, ['name', 'predicates', 'determinize', 'impurity', 'safe-pruning'],
                       tablefmt="presto"), end="\n\n")
        logging.info("User presets take precedence over pre-defined presets. "
                     "Try running, for example,\n\tdtcontrol --input examples/cartpole.scs --use-preset qest19-sos")

    def get_preset(preset, user_config, default_config):
        if user_config and preset in user_config['user-presets']:
            value = user_config['user-presets'][preset]
        elif preset in default_config['system-presets']:
            value = default_config['system-presets'][preset]
        else:
            sys.exit(f"Preset '{preset}' not found.\n"
                     f"Please ensure that the specified config file contains a "
                     f"configuration called '{preset}'. You may run the command\n"
                     f"\tdtcontrol preset --sample > user-config.yml\n"
                     f"to generate a configuration file and use it with the help of the "
                     f"--config and --use-preset switches (see help).\n"
                     f"Refer to the User Manual (https://dtcontrol.readthedocs.io/) for details on how to write presets.")

        default_value = default_config['system-presets']['default']

        # Obtain the different settings from the value dict
        # In case something is not defined, choose the default from default_value dict
        if 'predicates' in value:
            predicates = value['predicates']
        else:
            predicates = default_value['predicates']

        if 'determinize' in value:
            determinize = value['determinize']
        else:
            determinize = default_value['determinize']

        if 'impurity' in value:
            impurity = value['impurity']
        else:
            impurity = default_value['impurity']

        if 'safe-pruning' in value:
            safe_pruning = value['safe-pruning']
        else:
            safe_pruning = default_value['safe-pruning']

        return predicates, determinize, impurity, safe_pruning

    def get_classifier(split, determinize, impurity, safe_pruning=False, name=None):
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
            'oc1': OC1SplittingStrategy()  # TODO See import comment, doesn't work on Mac
        }
        impurity_map = {
            'auroc': AUROC(),
            'entropy': Entropy(),
            'gini': GiniIndex(),
            'maxminority': MaxMinority(),
            'twoing': TwoingRule()
        }

        # Sanity check
        for sp in split:
            if sp not in splitting_map:
                raise ValueError(f"{sp} is not a valid predicate type. Exiting...")

        if determinize not in determinization_map:
            raise ValueError(f"{determinize} is not a valid determinization strategy. Exiting...")

        if impurity not in impurity_map:
            raise ValueError(f"{impurity} is not a valid impurity measure. Exiting...")

        if not name:
            name = f"{determinize}-({','.join(split)})-{impurity}"

        classifier = DecisionTree(determinization_map[determinize],
                                  [splitting_map[sp] for sp in split],
                                  impurity_map[impurity],
                                  name)

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
        default_config = load_default_config()
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

        classifiers = []
        run_config_table = []
        Row = namedtuple('Row', ['Name', 'Predicate', 'Determinize', 'Impurity', 'SafePruning'])

        if args.use_preset:
            for preset in args.use_preset:
                split, determinize, impurity, safe_pruning = get_preset(preset, user_config, default_config)
                classifiers.append(get_classifier(split, determinize, impurity, safe_pruning=safe_pruning, name=preset))
                run_config_table.append(Row(Name=preset, Predicate=split, Determinize=determinize, Impurity=impurity,
                                            SafePruning=safe_pruning))

        if not classifiers:
            sys.exit("Please select a valid preset. Read the user manual for more details.")

        logging.info("The following configurations would now be run:\n")
        print(tabulate(run_config_table, ['name', 'predicates', 'determinize', 'impurity', 'safe-pruning'],
                       tablefmt="presto"), end="\n\n")

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
                                   "representation would be saved (c and dot)")

    input_output.add_argument("--benchmark-file", "-b", metavar="FILENAME", type=str,
                              help="Saves statistics pertaining the construction of the decision trees and their "
                                   "sizes into a JSON file, and additionally allows to view it via an HTML file.")

    run_config = parser.add_argument_group('run configurations')
    run_config.add_argument("--config", "-c", metavar="CONFIGFILE", type=str,
                            help="Specify location of a YAML file containing run configurarions. Use along with the "
                                 "--use-preset switch. More details in the User Manual.")

    run_config.add_argument("--use-preset", "-p", type=str, nargs="+",
                            help="Run one or more presets defined in the CONFIGFILE. If the --config switch has not "
                                 "been used, then presets are chosen from the system-level configuration file. Refer "
                                 "the User Manual for more details.")

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
