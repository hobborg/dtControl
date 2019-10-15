'''
README

dtcontrol --input (<input_files>... | <input_folder>)
          --output (<output_files>... | <output_folder>)
          [--method <method_names>...] [--timeout <seconds>]
          [--print-statistics <file>] [--load-statistics <file>]

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
                --print-statistics,-p <filename>
                        Saves statistics pertaining the construction of the decision trees and their
                        sizes into <filename>.json, and additionally allow to view it via <filename>.html
                --load-statistics,-l <json_file>
                        Loads the saved statistics and prevents re-running of already executed
                        input-method combinations. Use along with --print-statistics to save
                        any newly generated information to the same or different file.



Example:
dtcontrol --input controller.scs --output controller.c --method maxcart

will read controller.scs and use maxcart on it to obtain controller.c


dtcontrol --input controller1.scs controller2.scs --output out

will read controller1.scs and controller2.scs, try out all methods and save the
results in out; moreover print a table summarizing all the results


dtcontrol --input dumps --output out --method cart --save_results res

will read all valid controllers in dumps, run cart on them and print both dot
and c files in out; and store stats in res

'''

import argparse
import re

from os.path import exists, isfile, splitext, dirname, isdir
from os import makedirs

from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC

from benchmark_suite import BenchmarkSuite
from classifiers.cart_custom_decision_tree import CartCustomDecisionTree
from classifiers.linear_classifier_decision_tree import LinearClassifierDecisionTree
from classifiers.max_every_node_decision_tree import MaxCartDecisionTree
from classifiers.max_every_node_lc_decision_tree import MaxLCDecisionTree
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
        timeout = int(args.timeout[:-1])*factor
    else:
        # In case s, m or h is missing; then interpret number as timeout in seconds
        try:
            timeout = int(timeout_string)
        except ValueError:
            raise Exception("Invalid value passed as timeout.")
    return timeout


def get_classifiers(method_list):
    """
    Creates classifier objects for each method

    :param method_list: list of method strings
    :return: list of classifier objects
    """
    method_map = {'cart': CartCustomDecisionTree(),
                  'maxcart': MaxCartDecisionTree(),
                  'minnorm': MaxCartDecisionTree(),
                  'maxnorm': MaxCartDecisionTree(),
                  'maxlin': MaxLCDecisionTree(LogisticRegression, solver='lbfgs', penalty='none'),
                  'linsvm': LinearClassifierDecisionTree(LinearSVC, max_iter=5000),
                  'logreg': LinearClassifierDecisionTree(LogisticRegression, solver='lbfgs', penalty='none'),
                  'oc1': OC1Wrapper(num_restarts=20, num_jumps=5)
                  }
    if not method_list or "all" in method_list:
        return method_map.values()
    else:
        return [method_map[method] for method in method_list]


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
                         "arguments. Available methods for axis-parallel splits are: 'cart', 'maxcart', "
                         "'maxnorm', 'minnorm'; for oblique splits: 'maxlin', 'linsvm', 'logreg', 'oc1'; "
                         "and 'all' for running all possible methods. For description about each method, "
                         "refer manual. If this switch is omitted, defaults to 'all'")

parser.add_argument("--timeout", "-t", type=str,
                    help="Sets a timeout for each method. Can be specified in seconds, minutes "
                         "or hours (eg. 300s, 7m or 3h)")

parser.add_argument("--print-statistics", "-p", metavar="FILENAME", type=str,
                    help="Saves statistics pertaining the construction of the decision trees and their "
                         "sizes into a JSON file, and additionally allow to view it via an HTML file.")

parser.add_argument("--load-statistics", "-l", metavar="JSON_FILE", type=(lambda x: is_valid_file(parser, x)),
                    help="Loads the saved statistics and prevents re-running of already executed "
                         "input-method combinations. Use along with --print-statistics to save"
                         " any newly generated information to the same or different file.")


#parser.print_help()
args = parser.parse_args()
print(args)

kwargs = dict()

dataset = []
if args.input:
    dataset = args.input
else:
    raise Exception("Invalid input files/folders")

kwargs["timeout"] = 2*60*60
if args.timeout:
    kwargs["timeout"] = parse_timeout(args.timeout)

classifiers = get_classifiers(args.method)

if args.print_statistics:
    filename, file_extension = splitext(args.print_statistics)
    kwargs["save_file"] = filename

if args.output:
    try:
        makedirs(args.output, exist_ok=True)
        kwargs["output_folder"] = args.output
    except PermissionError:
        raise Exception("Ensure permission exists to create output directory")

if args.load_statistics:
    kwargs["load_file"] = args.load_statistics
    _, ext = splitext(args.load_statistics)
    if not isfile(args.load_statistics):
        raise Exception("Ensure file passed via --load-statistics/-l is a valid file")
    if ext != "json":
        raise Exception("Ensure file passed via --load-statistics/-l is a .json file")

suite = BenchmarkSuite(**kwargs)
suite.add_datasets(dataset)
suite.benchmark(classifiers)
