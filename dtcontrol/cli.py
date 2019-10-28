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
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC

from dtcontrol.benchmark_suite import BenchmarkSuite
from dtcontrol.classifiers.cart_custom_dt import CartDT
from dtcontrol.classifiers.linear_classifier_dt import LinearClassifierDT
from dtcontrol.classifiers.max_freq_dt import MaxFreqDT
from dtcontrol.classifiers.max_freq_linear_classifier_dt import MaxFreqLinearClassifierDT
from dtcontrol.classifiers.max_freq_multi_dt import MaxFreqMultiDT
from dtcontrol.classifiers.norm_dt import NormDT
from dtcontrol.classifiers.norm_linear_classifier_dt import NormLinearClassifierDT
from dtcontrol.classifiers.oc1_wrapper import OC1Wrapper
from dtcontrol.classifiers.random_dt import RandomDT


def main():
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
                'none': [CartDT()],  # TODO: remove lists and directly map to classifiers
                'maxfreq': [MaxFreqDT()],
                'minnorm': [NormDT(min)],
                # 'random': [RandomDT()],
            },
            'linsvm': {
                'none': [LinearClassifierDT(LinearSVC, max_iter=5000)],
                'maxfreq': [MaxFreqLinearClassifierDT(LinearSVC, max_iter=5000)],
                'minnorm': [NormLinearClassifierDT(min, LinearSVC, max_iter=5000)],
            },
            'logreg': {
                'none': [LinearClassifierDT(LogisticRegression, solver='lbfgs', penalty='none')],
                'maxfreq': [MaxFreqLinearClassifierDT(LogisticRegression, solver='lbfgs', penalty='none')],
                'minnorm': [NormLinearClassifierDT(min, LogisticRegression, solver='lbfgs', penalty='none')],
            },
            'oc1': {
                'none': [OC1Wrapper(num_restarts=20, num_jumps=5)]
            }
        }

        # construct all possible method - determinization strategy combinations
        classifiers = []

        if 'all' in methods:
            methods = method_map.keys()

        for method in methods:
            if method not in method_map:
                logging.warning(f"No method '{method}' exists. Skipping...")
                continue

            if 'all' in det_strategies:
                classifiers.extend(
                    [classifier for cls_group in method_map[method].values() for classifier in cls_group])
            else:
                for det_strategy in det_strategies:
                    if det_strategy not in method_map[method]:
                        logging.warning(f"Method '{method}' and determinization strategy '{det_strategy}' "
                                        f"don't work together (yet). Skipping...")
                        continue
                    classifiers.extend(method_map[method][det_strategy])

        # returns a flattened list
        return classifiers

    logging.basicConfig(level=logging.INFO, format='%(message)s')

    parser = argparse.ArgumentParser(prog="dtcontrol")

    version = pkg_resources.require("dtcontrol-tum")[0].version
    parser.add_argument("-v", "--version", action='version',
                        version=f'%(prog)s {version}')

    parser.add_argument("--input", "-i", nargs="+", type=(lambda x: is_valid_file_or_folder(parser, x)),
                        help="The input switch takes in one or more space separated file names or "
                             "a folder name which contains valid controllers (.scs, .dump or .csv)")

    parser.add_argument("--method", "-m", default=['all'], nargs="+",
                        help="The method switch takes in one or more space separated method names as "
                             "arguments. Available methods are: 'cart', 'linsvm', 'logreg', 'oc1'. Running "
                             "with --method 'all' will run all possible methods. For description about each method, "
                             "see manual. If this switch is omitted, defaults to 'all'")

    parser.add_argument("--determinize", "-d", nargs='+', metavar='DETSTRATEGY', default=['none'],
                        help="In case of non-deterministic controllers, specify, if desired, the determinization "
                             "strategy. Possible options are 'minnorm' and 'maxfreq'. If the option 'none' is passed, "
                             "then the controller is not determinized. The shorthand '-d all' is equivalent to "
                             "'-d none maxfreq minnorm'.")

    parser.add_argument("--timeout", "-t", type=str,
                        help="Sets a timeout for each method. Can be specified in seconds, minutes "
                             "or hours (eg. 300s, 7m or 3h)")

    parser.add_argument("--benchmark-file", "-b", metavar="FILENAME", type=str,
                        help="Saves statistics pertaining the construction of the decision trees and their "
                             "sizes into a JSON file, and additionally allows to view it via an HTML file.")

    parser.add_argument("--output", "-o", type=str,
                        help="The output switch takes in a path to a folder where the constructed controller "
                             "representation would be saved (c and dot)")

    parser.add_argument("--rerun", "-r", action='store_true',
                        help="Rerun the experiment for all input-method combinations. Overrides the default "
                             "behaviour of not running benchmarks for combinations which are already present"
                             " in the benchmark file.")

    parser.add_argument("--artifact", action='store_true',
                        help="Makes the tool 'repeatability evaluation' friendly - providing artifact reviewers "
                             "results in a tabular form which is easy to compare to Table 1 of the paper. Please "
                             "do not use the --artifact switch if you desire to use dtControl on a controller that is "
                             "not listed in Table 1")

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
        kwargs["benchmark_file"] = 'benchmark'  # TODO best practise to set default?
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

    kwargs["is_artifact"] = args.artifact

    classifiers = get_classifiers(args.method, args.determinize)

    if not classifiers:
        sys.exit("Cound not find any valid method - determinization strategy combinations. "
                 "Please read the manual for valid combinations and try again.")

    suite = BenchmarkSuite(**kwargs)
    suite.add_datasets(dataset)
    suite.benchmark(classifiers)


if __name__ == "__main__":
    main()
