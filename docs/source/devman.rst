Developer Manual
================

This document aims to provide the reader with the necessary information to be able to extend or customize dtControl. We first briefly describe how new decision tree algorithms can be added to the tool. Subsequently, we outline how new file formats can be supported.

dtControl is written entirely in Python and makes use of both the `numpy <https://numpy.org/>`_ and `scikit-learn <https://scikit-learn.org/stable/>`_ packages for data representation and manipulation. A basic familiarity with this programming environment is assumed throughout this manual. More information on dependencies can be found in the provided readme and setup.py files.

Extending dtControl with new algorithms
---------------------------------------

dtControl already supports a wide variety of decision tree construction algorithms. Furthermore, the tool can readily be extended with new algorithms, as we will see in this section.

The general decision tree structure is provided in the abstract base class ``CustomDT``. While it is not necessary for new classifiers to extend this class, it is highly recommended, since it already satisfies the interface that dtControl expects. This includes the following attributes and methods:

- ``name``: the name of the algorithm, as it will be displayed in the benchmark results.
- ``fit(dataset)``: constructs the decision tree for a ``dataset``.
- ``predict(dataset)``: returns a list of control inputs predicted for the dataset.
- ``get_stats()``: returns the statistics to be displayed in the benchmark results as a dictionary. This will mainly include the number of nodes and potentially some algorithm-specific statistics.
- ``is_applicable(dataset)``: some algorithms might be restricted to either single- or multi-output datasets, in which case this method can be used to indicate that an algorithm is not applicable to a ``dataset``.
- ``save()``: saves a representation of the class that can be used for debugging.
- ``export_dot()``: saves a representation of the decision tree in the `DOT <https://en.wikipedia.org/wiki/DOT_(graph_description_language)>`_ format.
- ``export_c()``: exports the decision tree to a C-file as a chain of if-else statements.

A ``CustomDT`` object also contains a reference to the root node of the decision tree (which is ``None`` before ``predict()`` is first called). The abstract base class ``Node`` provides the actual tree data structure and various methods that can be overridden to customize its behavior.

To implement a new algorithm, you thus need to provide two classes: One represents the actual decision tree and should extend ``CustomDT``, while the other represents nodes in the decision tree and extends the ``Node`` class.

The ``fit()`` method is given a dataset object, which is used to construct the decision tree. The two most important attributes of datasets are ``X_train``, a numpy array containing all states, and ``Y_train``, containing the actions that can be performed in those states. Depending on whether the dataset is single- or multi-output, the format of ``Y_train`` differs:

* In the case of single-output datasets, ``Y_train`` is a two-dimensional array, where each row contains all (non-deterministic) actions that can be performed at the corresponding row of ``X_train``. Instead of the actual floating point values, we use integer indices representing those values throughout the code; the mapping of indices to the actual values can be found in ``dataset.index_to_value``. Since numpy usually cannot deal with rows of different sizes, but we have varying numbers of possible actions, some rows have to be filled with ``-1`` s. These ``-1`` s have to be ignored during tree construction.
* In the case of multi-output datasets, ``Y_train`` is a three-dimensional array whose first dimension (or axis) corresponds to the different control inputs. Thus, there is a two-dimensional array for each control-input, which exactly matches the structure outlined above. To get the possible (multi-input) actions for a specific state, the arrays for the different control inputs have to be "stacked" in order to get the list of action tuples that can be performed.

The dataset class provides various methods to convert the format of ``Y_train`` to a more convenient representation to be used in decision tree construction. For example, ``get_unique_labels()`` maps all non-deterministic actions to a single index and thus returns simply a list of indices, which can directly be used as labels for any decision tree algorithm. After the tree has been constructed, its labels can be mapped back to the original non-deterministic actions using the ``set_labels()`` method provided in the Node class.

For examples of how new algorithms are implemented, it could be instructive to look at the ``LinearClassifierDT`` and ``MaxFreqDT`` classes, which implement tree construction using predicates from linear classifiers and the MaxFreq determinization procedure, respectively.


Supporting new file formats
---------------------------

dtControl currently supports the file formats generated by the the tools `SCOTS <https://www.hcs.ei.tum.de/en/software/scots/>`_ and `Uppaal Stratego <http://people.cs.aau.dk/~marius/stratego/>`_. There are two ways to make the tool work with other formats, as described in the following.


The CSV format
^^^^^^^^^^^^^^

The first option is to convert the new file format to a custom CSV format that dtControl also supports. We now describe the specification of the custom CSV format.

The first two lines of the file are reserved for metadata. The first line must always reflect whether the controller is permissive (non-deterministic) or non-permissive (deterministic). This is done using either of the following lines::

   #PERMISSIVE

or

   #NON-PERMISSIVE

The second line must reflect the number of state variables (or the state dimension) and the number of control input variables (or the input dimension). This line looks as follows:::

   #BEGIN N M

where `N` is the state dimension and `M` is the input dimension.

Every line after the 2nd line lists the state action/input pairs as a comma separated list:::

   x1,x2,...,xN,y1,y2,...,yM

if the controller prescribes the action ``(y1,y2,...,yM)`` for the state ``(x1,x2,...,xN)``. If the state allows more actions, for example, ``(y1’,y2’,...,yM’)``, then this should be described on a new line:::

   x1,x2,...,xN,y1,y2,...,yM
   x1,x2,...,xN,y1’,y2’,...,yM’

An excerpt of the ``10rooms.scs`` controller written in this CSV format would look as follows:::

   #PERMISSIVE
   #BEGIN 10 2
   18.75,20.0,18.75,18.75,20.0,18.75,18.75,18.75,18.75,18.75,1.0,1.0
   20.0,20.0,18.75,18.75,20.0,18.75,18.75,18.75,18.75,18.75,1.0,1.0
   21.25,20.0,18.75,18.75,20.0,18.75,18.75,18.75,18.75,18.75,1.0,1.0
   18.75,21.25,18.75,18.75,20.0,18.75,18.75,18.75,18.75,18.75,0.0,1.0
   18.75,21.25,18.75,18.75,20.0,18.75,18.75,18.75,18.75,18.75,0.5,1.0
   18.75,21.25,18.75,18.75,20.0,18.75,18.75,18.75,18.75,18.75,1.0,1.0
   20.0,21.25,18.75,18.75,20.0,18.75,18.75,18.75,18.75,18.75,0.0,1.0

dtControl will automatically look for files with a .csv extension and parse them with the assumption that they follow this format.

Implementing a new dataset loader
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Additionally, it is also possible to integrate the new file format natively into dtControl by providing a dataset loader. This should be a class that sub-classes the ``DatasetLoader`` class and provides exactly one method: ``_load_dataset()`` parses a file in the new format and returns a tuple with the following elements:

- ``X_train``: the data array as outlined above.
- ``X_metadata``: is a dictionary containing various information about the dataset, such as the names of the columns in ``X_train`` and the minimum and maximum values for each column.
- ``Y_train``: the label array as outlined above.
- ``Y_metadata``: is a dictionary containing information about ``Y_train``.
- ``index_to_value``: maps from integer indices to the actual floating point values used as control inputs.

The new dataset loader can be registered in the ``extension_to_loader`` attribute of the ``Dataset`` class. Now, if dtControl encounters a file with an extension of the new file format, it will attempt to load it using the registered loader.

Examples of such dataset loaders can be found in the ``ScotsDatasetLoader`` and ``UppaalDatasetLoader`` classes, however, they are very specific to the file formats used by the two tools.