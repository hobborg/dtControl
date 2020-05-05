User Manual
===========

This document equips the user with the information necessary to use dtControl and run the various decision tree learning
algorithms implemented in it.

Capabilities
------------

(`Watch a 5 minute introductory video on YouTube <https://www.youtube.com/watch?v=qS8FQ3pCeE4>`_)

dtControl is a tool to represent controllers using `decision trees <https://en.wikipedia.org/wiki/Decision_tree>`_.
It uses `decision tree learning <https://en.wikipedia.org/wiki/Decision_tree_learning>`_ to achieve this. The 5-minute video
above gives a quick introduction to why and how one may benefit from using dtControl.

The decision tree algorithm running inside dtControl is highly configurable. You may choose to represent a
determinized controller, allow for more expressible decision predicates or even tune the heuristic used to pick the best
predicate. See :ref:`presets-and-configuration-files` for more details.

While dtControl achieves best results with permissive or non-deterministic controllers with determinization enabled,
it can also be used with deterministic controllers. However empirical results with such controllers are not as
significant as with non-deterministic controllers.

Getting Started
----------------

A quick start installation guide is available in the `README <https://gitlab.lrz.de/i7/dtcontrol/-/blob/master/README.rst>`_.
In this section, we elaborate a little more on the installation process.

Installation
^^^^^^^^^^^^^^^^^

Getting `dtControl <https://pypi.org/project/dtcontrol/>`_ from the Python Package Index (PyPI) is the recommended way to install it.
Before running the ``pip install`` command, we recommend creating a virtual environment so that dependencies of dtControl
do not conflict with any other packages already installed on your system. The official Python documentation for `creating virtual
environments <https://docs.python.org/3/library/venv.html#creating-virtual-environments>`_ may help you set it up. However,
we provide the most essential information here.

Once you have a recent version of Python 3 installed, you may run::

    $ python3 -m venv dtcontrol-venv

to create the virtual environment in a folder called ``dtcontrol-venv`` located in your current directory. You can enter the
virtual environment by running::

    $ source dtcontrol-venv/bin/activate

Typically, your shell might indicate that the virtual environment is activated by changing the prompt symbol ``$`` to
something like ``(dtcontrol-venv) $``. You can now proceed with installing dtControl from PyPI using ``pip``::

    (dtcontrol-venv) $ pip install dtcontrol

.. note::
    In case you want to get the development version of dtControl, you could instead run::

        (dtcontrol-venv) $ pip install git+https://gitlab.lrz.de/i7/dtcontrol.git

Once the dtControl package is installed, the command line interface can be accessed using the ``dtcontrol`` command.
Try running::

   (dtcontrol-venv) $ dtcontrol -h

If your installation has run successfully, you will now see the help page detailing the usage and arguments.::

   usage: dtcontrol [-h] [-v] [--input INPUT [INPUT ...]] [--output OUTPUT] [--benchmark-file FILENAME] [--config CONFIGFILE] [--use-preset USE_PRESET [USE_PRESET ...]] [--rerun]
                 [--timeout TIMEOUT]
                 {preset,clean} ...

    Scroll to the end of the help message for Quick Start.

    optional arguments:
      -h, --help            show this help message and exit
      -v, --version         show program's version number and exit

    input/output:
      --input INPUT [INPUT ...], -i INPUT [INPUT ...]
                            The input switch takes in one or more space separated file names or a folder name which contains valid controllers (.scs, .dump or .csv)
      --output OUTPUT, -o OUTPUT
                            The output switch takes in a path to a folder where the constructed controller representation would be saved (c and dot)
      --benchmark-file FILENAME, -b FILENAME
                            Saves statistics pertaining the construction of the decision trees and their sizes into a JSON file, and additionally allows to view it via an HTML file.

    run configurations:
      --config CONFIGFILE, -c CONFIGFILE
                            Specify location of a YAML file containing run configurarions. Use along with the --use-preset switch. More details in the User Manual.
      --use-preset USE_PRESET [USE_PRESET ...], -p USE_PRESET [USE_PRESET ...]
                            Run one or more presets defined in the CONFIGFILE. If the --config switch has not been used, then presets are chosen from the system-level configuration file.
                            Special parameters for this switch include 'all', 'all-user', 'all-system'. Refer the User Manual for more details.
      --rerun, -r           Rerun the experiment for all input-method combinations. Overrides the default behaviour of not running benchmarks for combinations which are already present in
                            the benchmark file.
      --timeout TIMEOUT, -t TIMEOUT
                            Sets a timeout for each method. Can be specified in seconds, minutes or hours (eg. 300s, 7m or 3h)

    other commands:
      {preset,clean}        Run 'dtcontrol COMMAND --help' to see command specific help

    Examples:
    Create a file storing run configurations
        dtcontrol preset --sample > user-config.yml

    Display all presets available with dtcontrol
        dtcontrol preset --config user-config.yml --list

    Run the 'my-config' preset on the SCOTS model located at 'examples/cartpole.scs'
        dtcontrol --input examples/cartpole.scs --config user-config.yml --use-preset my-config

Input format
^^^^^^^^^^^^

Supported tools
"""""""""""""""

dtControl currently supports the file formats generated by the tools `SCOTS <https://www.hcs.ei.tum.de/en/software/scots/>`_, `Uppaal Stratego <http://people.cs.aau.dk/~marius/stratego/>`_, and `PRISM <http://prismmodelchecker.org/>`_. To see how to add suppport for new file formats to dtControl, refer to the `Developer Manual <devman.html>`_.

SCOTS and Uppaal output ``.scs`` and ``.dump`` files, respectively, as the result of a controller synthesis process. These can directly be specified as input to dtControl.

For PRISM, dtControl expects a strategy file that maps state indices to actions and a states file that maps state indices to the corresponding values of state variables. These files can be generated by PRISM with the following options::

    prism firewire_abst.nm liveness_abst.pctl -const 'delay=50,fast=0.5000' -prop 1 -explicit -exportstrat 'firewire_abst.prism:type=actions' -exportstates 'firewire_abst_states.prism'

It is important that both files have a ``.prism`` extension and the states file has the same name as the actions file with an ``_states`` suffix.

It is also possible to run dtControl on all controllers in a given folder; the tool then simply looks for all files with one of the above extensions.

Specifying metadata
"""""""""""""""""""

While dtControl tries to obtain as much information as possible from the controller directly, it is sometimes necessary to provide additional metadata to the tool. For example, dtControl cannot know which variables in the controller are categorical, which is necessary for some of the specialized algorithms. It is also possible to specify names, e.g. for variables, which are used in the DOT output.

This metadata can be given in a JSON file named ``controller_name_config.json`` (where ``controller_name`` must match the name of the controller file), which allows to set the following options:

- ``x_column_types`` is a dictionary with two entries, ``numeric`` and ``categorical``. These entries are lists with indices specifying which variables are numeric or categorical, respectively.

- ``y_column_types`` provides the same information for the output variables.

- ``x_column_names`` is a list of variable names.

- ``x_category_names`` is a dictionary with one entry for every categorical variable (as specified in ``x_column_types[categorical]``). This entry can either be an index or a name from ``x_column_names`` and maps to a list of category names for the variable. For instance, an entry of the form ``"color": ["red", "green", "blue"]`` would mean that a 0 in the ``color`` variable stands for ``red``, a 1 means ``green``, and a 2 denotes ``blue``.

- ``y_category_names`` gives the same information for the output variables.

If any of the options in the metadata are not set, dtControl tries to fall back to reasonable defaults, such as ``x[i]`` for the column names or just integers ``i`` for the category names. By default, all variables are treated as numeric.

An example is given in form of the configuration file for the ``firewire_abst.prism`` case study::

    {
      "x_column_types": {
        "numeric": [
          0
        ],
        "categorical": [
          1
        ]
      },
      "x_column_names": [
        "clock",
        "state"
      ],
      "x_category_names": {
        "state": [
          "start_start",
          "fast_start",
          "start_fast",
          "start_slow",
          "slow_start",
          "fast_fast",
          "fast_slow",
          "slow_fast",
          "slow_slow"
        ]
      }
    }

This configuration provides the information that the two variables are ``clock`` and ``state``, the first of which is numeric and the second of which is categorical. Furthermore, a ``state`` of 0 corresponds to ``start_start``, a state of 1 to ``fast_start``, and so on. Note that, for PRISM models, dtControl automatically parses the names of the actions and it is thus not necessary to provide a ``y_category_names`` entry.

The Command-line Interface
^^^^^^^^^^^^^^^^^^^^^^^^^^^

This section shows how to configure and run dtControl. For this purpose, we assume that you have an ``examples`` folder
in your current directory containing ``cartpole.scs``. You can choose to download all of our examples from our
`Gitlab repository <https://gitlab.lrz.de/i7/dtcontrol/-/tree/master/examples>`_ via this
`zip archive <https://gitlab.lrz.de/i7/dtcontrol/-/archive/master/dtcontrol-master.zip?path=examples>`_. Extract the
contents of the archive into a folder called ``examples`` and unzip ``cartpole.scs.zip``. Alternatively, you can
run the following commands::

    $ mkdir -p examples && cd examples
    $ wget https://gitlab.lrz.de/i7/dtcontrol/-/raw/master/examples/cartpole.scs.zip
    $ unzip cartpole.scs.zip

Next, activate the virtual environment you installed dtControl in::

    $ source dtcontrol-venv/bin/activate

.. _running-your-first-command:

Running your first command
""""""""""""""""""""""""""

Finally, you can run dtControl with the default parameters on the *cartpole* example (``cartpole.scs``), use the following command::

    (dtcontrol-venv) $ dtcontrol --input examples/cartpole.scs

This will produce some new files and folders in the current folder::

   decision_trees
   |-- default
   |   `-- cartpole
   |       |-- default.c
   |       |-- default.dot
   benchmark.json
   benchmark.html

Open ``benchmark.html`` in your favourite browser to view a summary of the results. For more details on what these files
are, see :ref:`understanding-the-output`.

.. _presets-and-configuration-files:

Presets and configuration files
"""""""""""""""""""""""""""""""

dtControl allows the user to configure the learning algorithm using "presets" defined in a "configuration file". The
presets can be chosen using the ``--use-preset`` switch and the configuration file can be chosen using the ``--config``
switch. For your convenience, we have pre-defined a bunch of preset configurations that we believe are interesting.
You can list the available presets by running::

    (dtcontrol-venv) $ dtcontrol preset --list

This should produce the following table of presets.

===============  =============================   ======================  ============    ========     =========     ============
name             numeric-predicates              categorical-predicates  determinize     impurity     tolerance     safe-pruning
===============  =============================   ======================  ============    ========     =========     ============
default          ['axisonly']                    ['multisplit']           none           entropy      1e-05         False
cart             ['axisonly']                                             none           entropy                 
linsvm           ['axisonly', 'linear-linsvm']                            none           entropy                 
logreg           ['axisonly', 'linear-logreg']                            none           entropy                 
oc1              ['oc1']                                                  none           entropy                 
maxfreq          ['axisonly']                                             maxfreq        entropy                 
maxfreqlc        ['axisonly', 'linear-logreg']                            maxfreq        entropy                 
minnorm          ['axisonly']                                             minnorm        entropy                 
minnormlc        ['axisonly', 'linear-logreg']                            minnorm        entropy                 
sos              ['axisonly']                                             none           entropy                 
sos-safepruning  ['axisonly']                                             none           entropy                     True
linear-auroc     ['axisonly', 'linear-logreg']                            none           auroc                   
===============  =============================   ======================  ============    ========     =========     ============

The ``--use-preset`` argument takes in one or more preset names as argument. For each preset specified as argument, dtControl
will run the learning algorithm configured as described in this table and produce results in the folder: ``decision_trees/<preset_name>/<example_name>/``.

.. _configurable-options:

""""""""""""""""""""
Configurable options
""""""""""""""""""""

#. **numeric-predicates** can be used to configure the class of predicates that are considered for constructing the tree.
   It can take the values

        a. ``axisonly`` for predicates which compare a variable to a constant
        b. ``linear-logreg`` for predicates which compare a linear combination of variables to a constant (``ax + by < c``) obtained using `Logistic Regression <https://en.wikipedia.org/wiki/Logistic_regression>`_
        c. ``linear-linsvm`` for linear predicates obtained using linear `Support Vector Machines <https://en.wikipedia.org/wiki/Support-vector_machine>`_, and finally
        d. ``oc1`` for predicates obtained from the tool of `Murthy et. al <https://jhu.pure.elsevier.com/en/publications/oc1-randomized-induction-of-oblique-decision-trees-4>`_

#. **categorical-predicates** determines how non-numeric or categorical variables (such as ``color = blue``) should be
   dealt with. Currently, it only supports the option

        a. ``multisplit`` which creates a decision node with as many children as the number of possible categories the variable can take (e.g. ``color = blue``, ``color = green`` and ``color = red``).
        b. ``singlesplit`` which creates a decision node with just two children, one satisfying a categorical equality (``color = blue``) and the other that does not (``color != blue``).
        c. ``valuegrouping`` as described in M. Jackermeier's thesis (TODO link)

#. **determinize** determines the type of determinization used on permissive/non-deterministic controller when constructing the tree. Possible
   options are

        a. ``none`` to preserve permissiveness,
        b. ``minnorm`` to pick control inputs with the minimal norm,
        c. ``maxnorm`` to pick control inputs with the maximal norm,
        d. ``random`` to pick a control input uniformly at random,
        e. ``maxfreq`` to pick our in-house developed determinization strategy, details of which are available in M. Jackermeier's thesis (TODO link).
        f. ``auto`` to let dtControl automatically choose a determinization strategy; currently defaults to ``maxfreq``.

#. **impurity** allows users to choose the measure by which splitting predicates are evaluated. Possible options are

        a. ``entropy``
        b. ``gini``
        c. ``auroc``
        d. ``maxminority``
        e. ``twoing``
        f. ``multilabelentropy``
        g. ``multilabelgini``
        h. ``multilabeltwoing``

#. **tolerance** is a floating point value relevant only when choosing the ``valuegrouping`` categorical predicate.

#. **safe-pruning** decides whether to post-process the decision tree as specified in `Ashok et. al. (2019) <https://link.springer.com/chapter/10.1007%2F978-3-030-30281-8_9>`_.

"""""""""""""""""""""""""
Creating your own presets
"""""""""""""""""""""""""

As a user, you can define your own preset by mixing and matching the parameters from :ref:`configurable-options`. The presets
must be defined inside a ``.yml`` file as follows::

    presets:
      my-config:
        determinize: maxfreq
        numeric-predicates: ['axisonly']
        categorical-predicates: ['singlesplit']
        impurity: 'entropy'
        safe-pruning: False
      another-config:
        determinize: minnorm
        numeric-predicates: ['linear-logreg']
        categorical-predicates: ['valuegrouping']
        tolerance: 10e-4
        safe-pruning: False

.. note::
    The values for the keys ``numeric-predicates`` and ``categorical-predicates`` are lists. If the list contain
    more than one elements, e.g. ``numeric-predicates: ['axisonly', 'linear-svm']``, dtControl will construct predicates for
    each of the classes present (in this case, both axis-parallel and linear splits using a linear SVM) in the list and pick
    the best predicate amongst all the classes.

The above sample presets can be generated automatically and wrote into a ``user-config.yml`` file by running::

    (dtcontrol-venv) $ dtcontrol preset --sample > user-config.yml

Now, dtControl can be run on the *cartpole* example with the ``my-config`` preset by running::

    (dtcontrol-venv) $ dtcontrol --input examples/cartpole.scs --config user-config.yml --use-preset my-config


.. _understanding-the-output:

Understanding the output
^^^^^^^^^^^^^^^^^^^^^^^^^

Once dtControl is used to run some experiments, you may notice a bunch of new files and folders::

   decision_trees
   |-- default
   |   `-- cartpole
   |       |-- default.c
   |       |-- default.dot
   |-- my-config
   |   `-- cartpole
   |       |-- my-config.c
   |       |-- my-config.dot
   benchmark.json
   benchmark.html

* ``benchmark.html`` is the central file, which summarizes all the results obtained by dtControl. It may be opened
  using a browser of your choice.
* ``benchmark.json`` is a JSON file containing all the statistics collected by the tool (tree size, bandwidth, construction
  time and other metadata). The ``benchmark.html`` file is rendered from this JSON file at the end of the experiments.
* ``default.c`` contains the C-code of the decision tree
* ``default.dot`` contains the DOT source code which can be compiled using the ``dot -Tpdf default.dot -o default.pdf`` command
  or `viewed using a web-based tool <https://dreampuf.github.io/GraphvizOnline/>`_

By default, the decision trees are stored in the ``decision_trees`` folder and the statistics are stored in the ``benchmark.json``
and ``benchmark.html`` files. This can however be customized with the help of the ``--output`` and the ``--benchmark-file``
switches. For example::

   (dtcontrol-venv) $ dtcontrol --input examples/cartpole.scs \
                                --config user-config.yml \
                                --use-preset my-config \
                                --output cartpole_trees \
                                --benchmark-file cartpole_stats

Will produce the following files and directories::

   cartpole_trees
   |-- my-config
   |   `-- cartpole
   |       |-- my-config.c
   |       |-- my-config.dot
   cartpole_stats.json
   cartpole_stats.html

Timeout
^^^^^^^

Another useful feature is timeout which can be set with the ``--timeout/-t`` switch. For example,::

   $ dtcontrol --input examples/truck_trailer.scs --timeout 3m

will run CART on the *truck_trailer* example, and time out if it is taking longer than 3 minutes to finish. The
``--timeout/-t`` switch can accept timeout in seconds, minutes and hours (``-t 42s`` or ``-t 30m`` or ``-t 1h``).
The timeouts is applied for each preset individually, and not for the whole set of experiments.

Re-run
^^^^^^

By default, new results are appended to ``benchmark.json`` (or the file passed to the ``--benchmark-file`` switch) and
experiments are not re-run if results already exist. In case you want to re-run a method and overwrite existing results,
use the ``--rerun`` flag.::

   $ dtcontrol --input examples/cartpole.scs --rerun


Quick Start with the Python Interface
-------------------------------------

More advanced users can use dtControl programmatically using Python or as part of a Jupyter notebook. Here is an example of the Python interface with comments that give guidance on what is happening::

    # imports
    # you might have to import additional classifiers
    from sklearn.linear_model import LogisticRegression
    from dtcontrol.benchmark_suite import BenchmarkSuite
    from dtcontrol.decision_tree.decision_tree import DecisionTree
    from dtcontrol.decision_tree.determinization.max_freq_determinizer import MaxFreqDeterminizer
    from dtcontrol.decision_tree.impurity.entropy import Entropy
    from dtcontrol.decision_tree.impurity.multi_label_entropy import MultiLabelEntropy
    from dtcontrol.decision_tree.splitting.axis_aligned import AxisAlignedSplittingStrategy
    from dtcontrol.decision_tree.splitting.linear_classifier import LinearClassifierSplittingStrategy

    # instantiate the benchmark suite with a timeout of 2 hours
    # rest of the parameters behave like in CLI
    suite = BenchmarkSuite(timeout=60*60*2,
                           save_folder='saved_classifiers',
                           benchmark_file='benchmark',
                           rerun=False)

    # Add the 'examples' directory as the base where
    # the different controllers will be searched for
    # You can also choose to only include specific files
    # in the directory with the 'include' and 'exclude' list
    suite.add_datasets('examples')

    # setting up the predicates
    aa = AxisAlignedSplittingStrategy()
    logreg = LinearClassifierSplittingStrategy(LogisticRegression, solver='lbfgs', penalty='none')

    # select the DT learning algorithms we want to run and give them names
    classifiers = [
        DecisionTree([aa], Entropy(), 'CART'),
        DecisionTree([aa, logreg], Entropy(), 'LogReg'),
        DecisionTree([aa], Entropy(), 'Early-stopping', early_stopping=True),
        DecisionTree([aa], Entropy(MaxFreqDeterminizer()), 'MaxFreq', early_stopping=True),
        DecisionTree([aa], MultiLabelEntropy(), 'MultiLabelEntropy', early_stopping=True)
    ]
    # finally, execute the benchmark
    suite.benchmark(classifiers)
    # open the web browser and show the result
    suite.display_html()

As you can see, the Python interface provides mostly the same parameters as the CLI, but gives you some additional control. In particular, the following functionality is currently only supported by the Python interface:

- Using ``early_stopping`` with the label powerset method

- Parameters for safe pruning and early stopping which control the amount of nondeterminism preserved

- Choosing any determinizer for oblique splits

- Only allowing oblique splits in leaf nodes

- Various parameters of the OC1 heuristic

- The ``ScaledBincount`` impurity measure with a custom scaling function

The easiest way to get more information on the methods available in the Python interface is to directly browse the `source code <https://gitlab.lrz.de/i7/dtcontrol/-/tree/master/dtcontrol>`_ of dtControl.
