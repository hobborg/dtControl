dtControl documentation
=====================================

Introduction
------------

dtControl is a tool for compressing memoryless controllers arising out of automatic controller synthesis of cyber-physical systems (CPS). dtControl takes as input a controller synthesised by various formal verification tools and represents them in the form of decision trees. In the process, the size of the controller is reduced greatly, and at the same time, it becomes more explainable. While in principle, memoryless strategies in any format can be handled by dtControl, currently it supports controllers output by two tools:
`SCOTS <https://www.hyconsys.com/software/scots/>`_ and `Uppaal Stratego <https://people.cs.aau.dk/~marius/stratego/>`_. Additionally, there is rudimentary support for strategies produced by `PRISM Model Checker <https://www.prismmodelchecker.org>`_ and a pipeline with the model checker `Storm <http://www.stormchecker.org/index.html>`_ is under works.

Moreover, it also supports a CSV-based format which allows the user to quickly experiment with the techniques provided by dtControl.

We provide a :doc:`User Manual<userman>`, which gives information necessary to use dtControl and run the various decision tree learning algorithms implemented in it, as described in the paper "dtControl: Decision Tree Learning Algorithms for Controller Representation" appearing at the 23rd ACM International Conference on Hybrid Systems: Computation and Control (HSCC 2020).

An additional :doc:`Developer Manual<devman>` is made available for those who are interested in interfacing their own controller synthesis tools with dtControl or interested in implementing their own strategy representation algorithms.

If you find any mistakes in this documentation or have any questions, we are happy to receive your message. You may contact `Maxi <mailto:maxi.weininger@tum.de>`_, `Christoph <mailto:christoph.weinhuber@tum.de>`_, `Jan <mailto:jan.kretinsky@tum.de>`_ or `Tabea <mailto:tabea.frisch@tum.de>`_.

.. toctree::
   :maxdepth: 3
   :caption: Table of Contents

   userman
   devman


.. Indices and tables
.. ==================

.. * :ref:`genindex`
.. * :ref:`modindex`
.. * :ref:`search`

