User Manual
===========


This document equips the user with the information necessary to use dtControl and run the various decision tree learning algorithms implemented in it.

Capabilities
------------

dtControl achieves best results on non-deterministic or permissive controllers. The following algorithms are supported for such controllers:

Non-determinism preserving

1. CART
2. CART with predicates from Linear SVM (LinSVM)
3. CART with predicates from Logistic Regression (LogReg)
4. CART with predicates from OC1 (OC1)

Determinizing

1. CART + maximal frequencies (MaxFreq)
2. LinSVM/LogReg + maximal frequencies (MaxFreqLC)
3. CART + minimal norm (MinNorm)
4. LinSMV/LogReg + minimal norm (MinNormLC)

dtControl can also be used with deterministic controllers, however empirical results with such controllers are not as significant as with nondeterministic controllers.

Quick Start with Command-line Interface
----------------------------------------

Once the dtControl package is installed, the command line interface can be accessed from your favourite shell using the dtcontrol command. Get started by running::

   $ dtcontrol -h

If your installation has run successfully, you will now see the help page detailing the usage and arguments.::

   usage: dtcontrol [-h] [-v] [--input INPUT [INPUT ...]] [--output OUTPUT]
                    [--method METHOD [METHOD ...]]
                    [--determinize DETSTRATEGY [DETSTRATEGY ...]]
                    [--timeout TIMEOUT] [--no-multiprocessing] [--artifact]
                    [--benchmark-file FILENAME] [--rerun]

   optional arguments:
     -h, --help            show this help message and exit
     -v, --version         show program's version number and exit
     --input INPUT [INPUT ...], -i INPUT [INPUT ...]
                           The input switch takes in one or more space separated
                           file names or a folder name which contains valid
                           controllers (.scs, .dump or .csv)
     --output OUTPUT, -o OUTPUT
   .
   .
   .
   .

First Run
^^^^^^^^^

The examples folder available in the RE package contains all the SCOTS (*.scs sparse-matrix format) and UPPAAL (*.dump format) examples against which dtControl has been benchmarked, as shown in Table 1 of the paper.

To run the CART algorithm on, say, the *cartpole* example (``cartpole.scs``), use the following command::

   $ dtcontrol --input examples/cartpole.scs --method cart

This will produce some new files and folders in the current folder::

   decision_trees
   |-- CART
   |   `-- cartpole
   |       |-- CART.c
   |       |-- CART.dot
   benchmark.json
   benchmark.html

where

- ``CART.c`` contains the C-code of the decision tree
- ``CART.dot`` contains the DOT source code which can be compiled, for example, using the dot -Tpdf CART.dot -o CART.pdf command
- ``benchmark.json`` contains a JSON file containing some statistics (tree size, bandwidth, construction time and other metadata)
- ``benchmark.html`` summarizes the experiments whose results are stored in benchmark.json


Determinization
^^^^^^^^^^^^^^^

Now let us see another example where our best determinizing technique, MaxFreq, is used along with CART.::

   $ dtcontrol -i examples/cartpole.scs -m cart -d maxfreq

(Note the use of the ``-i``, ``-m`` and ``-d`` switches instead of their full versions: ``--input``, ``--method`` and ``--determinize``.)

Output
^^^^^^

After dtControl finishes execution, the directory structure should look like this:::

   decision_trees
   |-- CART
   |   `-- cartpole
   |       |-- CART.c
   |       |-- CART.dot
   |-- MaxFreqDT
   |   `-- cartpole
   |       |-- MaxFreqDT.c
   |       |-- MaxFreqDT.dot
   benchmark.json
   benchmark.html

The ``benchmark.html`` file is updated after every run. View a tabular summary of all the results stored in ``benchmark.json`` by opening ``benchmark.html`` in your favourite browser.

Multiple input controllers and methods
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

dtControl can run multiple methods on multiple controllers. For example, if one desires to evaluate *LinSVM* and *LogReg* methods along with the *MinNorm* determinizing strategy on *cartpole* and *10rooms*, the following command may be used.::

   $ dtcontrol \
     --input examples/cartpole.scs examples/10rooms.scs \
     --method linsvm logreg \
     --determinize minnorm

Both the ``--method`` and ``--determinize`` flags support the *all* shorthand. For example, the following command will run all methods with all determinization strategies on *cartpole*.::

   $ dtcontrol -i examples/cartpole.scs -m all -d all

where ``-m`` all is a shorthand for ``-m cart linsvm logreg oc1`` and ``-d`` all is a shorthand for ``-d none minnorm maxfreq``

dtControl can also take whole folders or wildcards as input. In case the ``-i`` switch gets a valid folder as argument, dtControl tries to read all ``*.scs``, ``*.dump`` and ``*.csv`` as inputs for its methods. Wildcards behave as you would expect in any shell.::

   $ dtcontrol -i examples -m cart
   $ dtcontrol -i examples/*.dump -m cart -d maxfreq


A list of methods supported by dtControl and their respective command-line switches is given in the table below.

.. csv-table:: List of methods
   :header: "Method", "Switch"
   :widths: 50,30

   "CART","``-m cart -d none``"
   "Linear SVM","``-m linsvm -d none``"
   "Logistic Regression","``-m logreg -d none``"
   "OC1","``-m oc1 -d none``"
   "CART + maximal frequencies (MaxFreq)","``-m cart -d maxfreq``"
   "LogReg + maximal frequencies (MaxFreqLC)","``-m logreg -d maxfreq``"
   "CART + minimal norm (MinNorm)","``-m cart -d minnorm``"
   "LinSMV/LogReg + minimal norm (MinNormLC)","``-m logreg -d minnorm``"


Advanced Features
-----------------
Output location
^^^^^^^^^^^^^^^

By default, the decision trees are stored in the decision_trees folder and the statistics are stored in the benchmark.json and benchmark.html files. This can however be customized with the help of the ``--output/-o`` and the ``--benchmark-file/-b`` switches. For example,::

   $ dtcontrol -i examples/cartpole.scs -m cart \
     --output cartpole_trees \
     --benchmark-file cartpole_stats

Will produce the following files and directories::

   cartpole_trees
   |-- CART
   |   `-- cartpole
   |       |-- CART.c
   |       |-- CART.dot
   cartpole_stats.json
   cartpole_stats.html

Timeout
^^^^^^^

Another useful feature is timeout which can be set with the ``--timeout/-t`` switch. For example,::

   $ dtcontrol -i examples/truck_trailer.scs -m cart -t 3m 

will run CART on the *truck_trailer* example, and time out if it is taking longer than 3 minutes to finish. The ``--timeout/-t`` switch can accept timeout in seconds, minutes and hours (``-t 42s`` or ``-t 30m`` or ``-t 1h``). The timeouts are applied for each method individually, and not for the whole set of experiments.

Re-run
^^^^^^

By default, new results are appended to ``benchmark.json`` (or the file passed to the ``--benchmark-file`` switch) and experiments are not re-run if results already exist. In case you want to re-run a method and overwrite existing results, use the ``--rerun`` flag.::

   $ dtcontrol -i examples/truck_trailer.scs -m cart -t 3m --rerun


Quick Start with Python Interface
---------------------------------

More advanced users can use dtControl programmatically using Python. Here is a sample code.::

   # imports
   # user might have to import additional classifiers

   from sklearn.linear_model import LogisticRegression
   from sklearn.svm import LinearSVC
   from benchmark_suite import BenchmarkSuite
   from dtcontrol.classifiers.cart_custom_dt import CartDT
   from dtcontrol.classifiers.linear_classifier_dt import LinearClassifierDT
   from dtcontrol.classifiers.max_freq_dt import MaxFreqDT
   from dtcontrol.classifiers.max_freq_linear_classifier_dt import MaxFreqLinearClassifierDT
   from dtcontrol.classifiers.norm_dt import NormDT
   from dtcontrol.classifiers.norm_linear_classifier_dt import NormLinearClassifierDT
   from dtcontrol.classifiers.oc1_wrapper import OC1Wrapper

   # instantiate the benchmark suite with a timeout of 2 hours
   # rest of the parameters behave like in CLI

   suite = BenchmarkSuite(timeout=60 * 60 * 2,
                          output_folder='decision_trees',
                          benchmark_file='benchmark',
                          is_artifact=True,
                          rerun=False)

   # Add the 'examples' directory as the base where
   # the different controllers will be searched for

   suite.add_datasets(
       # names of the folder containing scs/dump/csv files
       ['examples'],
       # names of the scs/dump/csv files without the extension
       include=["cartpole", "10rooms"],
   )

   # select the methods which would be applied on the datasets
   classifiers = [
       # CART
       CartDT(),
       # LinSVM
       LinearClassifierDT(LinearSVC, max_iter=5000),
       # LogReg
       LinearClassifierDT(LogisticRegression, solver='lbfgs', penalty='none'),
       # OC1
       OC1Wrapper(num_restarts=20, num_jumps=5),
       # MaxFreq
       MaxFreqDT(),
       # MaxFreqLC
       MaxFreqLinearClassifierDT(LogisticRegression, solver='lbfgs', penalty='none'),
       # MinNorm
       NormDT(min),
       # MinNormLC
       NormLinearClassifierDT(min, LogisticRegression, solver='lbfgs', penalty='none'),
   ]

   # finally, execute the benchmarks
   suite.benchmark(classifiers)