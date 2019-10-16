"""
README

Usage: dtcontrol [-h] [-v] [--input INPUT [INPUT ...]] [--output OUTPUT]
                 [--method METHOD [METHOD ...]]
                 [--determinize DETSTRATEGY [DETSTRATEGY ...]]
                 [--timeout TIMEOUT] [--benchmark-file FILENAME] [--rerun]

                --input,-i  (<input_files>... | <input_folder>)
                        The input switch takes in one or more space separated file names
                        or a folder name which contains valid controllers (.scs, .vector or .dump)

                --output,-o  <output_folder>
                        The output switch takes in a path to a folder where the constructed controller
                        representation would be saved (c, dot and vhdl)

                --method,-m  <method_names>...
                        The method switch takes in one or more space separated method names as
                        arguments
                            cart        - the standard decision tree learning algorithm
                            maxcart     - modified version of cart with smart determinization
                            maxlc       - smart determinization with linear predicates
                            linsvm      - decision tree where predicates are obtained through
                                          LinearSVM
                            logreg      - decision tree where predicates are obtained through
                                          Logistic Regression
                            oc1         - oblique decision tree algorithm with randomized splits
                            all         - runs all of the above methods
                        If absent, defaults to --methods all
                --determinize,-d <determinization_strategies>...
                        In case of non-deterministic controllers, specify, if necessary the determinization
                        strategy. Possible options are 'maxnorm', 'minnorm', 'maxfreq' and 'multimaxfreq'.
                        If no determinization strategy is provided, then each set non-deterministic set
                        of control inputs is treated uniquely.
                --benchmark-file,-b <filename>
                        Saves statistics pertaining the construction of the decision trees and their
                        sizes into <filename>.json, and additionally allow to view it via <filename>.html
                --rerun, -r
                        Rerun the experiment for all input-method combinations. Overrides the default
                        behaviour of not running benchmarks for combinations which are already present
                        in the benchmark file.

                When multiple inputs with multiple methods and determinization strategies are passed,
                dtControl tries to run every valid method-determinization strategy combination on each
                input.


Example:
dtcontrol --input controller.scs --output controller.c --method maxcart

will read controller.scs and use maxcart on it to obtain controller.c


dtcontrol --input controller1.scs controller2.scs --output out

will read controller1.scs and controller2.scs, try out all methods and save the
results in out; moreover print a table summarizing all the results


dtcontrol --input dumps --output out --method cart --save_results res

will read all valid controllers in dumps, run cart on them and print both dot
and c files in out; and store stats in res

"""

import argparse
import re
import sys
from os import makedirs
from os.path import exists, isfile, splitext

from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC

from benchmark_suite import BenchmarkSuite
from classifiers.cart_custom_decision_tree import CartCustomDecisionTree
from classifiers.linear_classifier_decision_tree import LinearClassifierDecisionTree
from classifiers.max_every_node_decision_tree import MaxCartDecisionTree
from classifiers.max_every_node_lc_decision_tree import MaxLCDecisionTree
from classifiers.max_every_node_multi_decision_tree import MaxEveryNodeMultiDecisionTree
from classifiers.oc1_wrapper import OC1Wrapper


def is_valid_file_or_folder(parser, arg):
    if not exists(arg):
        parser.error(f"The file/folder {arg} does not exist")
    else:
        return arg


def is_valid_file(parser, arg):
    if not isfile(arg):
        parser.error(f"The file {arg} does not exist. Give a valid JSON file path.")
    else:
        return arg


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


def get_classifiers(methods, det_strategies):
    """
    Creates classifier objects for each method

    :param methods: list of method strings
    :param det_strategies: list of determinization strategies
    :return: list of classifier objects
    """
    method_map = {
        'cart': {
            'nondet': CartCustomDecisionTree(),
            'maxnorm': MaxCartDecisionTree(),
            'minnorm': MaxCartDecisionTree(),
            'maxfreq': MaxCartDecisionTree(),
            'multimaxfreq': MaxEveryNodeMultiDecisionTree(),
        },
        'linsvm': {
            'nondet': LinearClassifierDecisionTree(LinearSVC, max_iter=5000),
            'maxnorm': MaxLCDecisionTree(LinearSVC, max_iter=5000),
            'minnorm': MaxLCDecisionTree(LinearSVC, max_iter=5000),
            'maxfreq': MaxLCDecisionTree(LinearSVC, max_iter=5000),
        },
        'logreg': {
            'nondet': LinearClassifierDecisionTree(LogisticRegression, solver='lbfgs', penalty='none'),
            'maxnorm': MaxLCDecisionTree(LogisticRegression, solver='lbfgs', penalty='none'),
            'minnorm': MaxLCDecisionTree(LogisticRegression, solver='lbfgs', penalty='none'),
            'maxfreq': MaxLCDecisionTree(LogisticRegression, solver='lbfgs', penalty='none'),
        },
        'oc1': {
            None: OC1Wrapper(num_restarts=20, num_jumps=5)
        }
    }

    if not methods:
        return [method[strat] for method in method_map for strat in det_strategies]

    if 'all' in methods:
        return [cls for strats in method_map.values() for cls in strats.values()]

    for method in methods:
        if not method in method_map.keys():
            parser.print_help()
            sys.exit("Invalid method provided")

    if not det_strategies:
        return [method_map[method]['nondet'] for method in methods]
    else:
        classifiers = []
        for method in methods:
            if 'all' in det_strategies:
                classifiers.append(method_map[method].values())
            else:
                for strat in det_strategies:
                    try:
                        classifiers.append(method_map[method][strat])
                    except KeyError:
                        parser.print_help()
                        sys.exit("Invalid determinization strategy provided")
        return classifiers

parser = argparse.ArgumentParser(prog="dtcontrol")

parser.add_argument("-v", "--version", action='version', version='%(prog)s 1.0')

parser.add_argument("--input", "-i", nargs="+", type=(lambda x: is_valid_file_or_folder(parser, x)),
                    help="The input switch takes in one or more space separated file names or "
                         "a folder name which contains valid controllers (.scs, .vector or .dump)")

parser.add_argument("--output", "-o", type=str,
                    help="The output switch takes in a path to a folder where the constructed controller "
                         "representation would be saved (c, dot and vhdl)")

parser.add_argument("--method", "-m", default=['all'], nargs="+",
                    help="The method switch takes in one or more space separated method names as "
                         "arguments. Available methods are: 'cart', 'linsvm', 'logreg', 'oc1'. Running "
                         "with --method 'all' will run all possible methods. For description about each method, "
                         "refer manual. If this switch is omitted, defaults to 'all'")

parser.add_argument("--determinize", "-d", nargs='+', metavar='DETSTRATEGY', default='nondet',
                    help="In case of non-deterministic controllers, specify, if necessary the determinization "
                         "strategy. Possible options are 'maxnorm', 'minnorm', 'maxfreq' and 'multimaxfreq'")

parser.add_argument("--timeout", "-t", type=str,
                    help="Sets a timeout for each method. Can be specified in seconds, minutes "
                         "or hours (eg. 300s, 7m or 3h)")

parser.add_argument("--benchmark-file", "-b", metavar="FILENAME", type=str,
                    help="Saves statistics pertaining the construction of the decision trees and their "
                         "sizes into a JSON file, and additionally allow to view it via an HTML file.")

parser.add_argument("--rerun", "-r", action='store_true',
                    help="Rerun the experiment for all input-method combinations. Overrides the default "
                         "behaviour of not running benchmarks for combinations which are already present"
                         "in the benchmark file.")

args = parser.parse_args()

kwargs = dict()

dataset = []
if args.input:
    dataset = args.input
else:
    parser.print_help()
    sys.exit("Input files/folders missing")

kwargs["timeout"] = 2 * 60 * 60
if args.timeout:
    kwargs["timeout"] = parse_timeout(args.timeout)

if args.benchmark_file:
    filename, file_extension = splitext(args.benchmark_file)
    kwargs["benchmark_file"] = filename

if args.output:
    try:
        makedirs(args.output, exist_ok=True)
        kwargs["output_folder"] = args.output
    except PermissionError:
        sys.exit("Ensure permission exists to create output directory")

kwargs["rerun"] = args.rerun

classifiers = get_classifiers(args.method, args.determinize)

suite = BenchmarkSuite(**kwargs)
suite.add_datasets(dataset)
suite.benchmark(classifiers)
