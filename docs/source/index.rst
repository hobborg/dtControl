dtControl documentation
=====================================

.. toctree::
   :maxdepth: 3
   :caption: Table of Contents

   userman
   devman


Introduction
============

dtControl is a tool for compressing memoryless controllers arising out of automatic controller synthesis of cyber-physical systems (CPS). dtControl takes as input a controller synthesised by various formal verification tools and represents them in the form of decision trees. In the process, the size of the controller is reduced greatly, and at the same time, it becomes more explainable. While in principle, memoryless strategies in any format can be handled by dtControl, currently it supports controllers output by two tools:
SCOTS (link)
Uppaal Stratego (link)

Moreover, it also supports a CSV-based format which allows the user to quickly experiment with the techniques provided by dtControl.

We provide a :doc:`User Manual<userman>`, which gives information necessary to use dtControl and run the various decision tree learning algorithms implemented in it, as described in the paper "dtControl: Decision Tree Learning Algorithms for Controller Representation" appearing at the 23rd ACM International Conference on Hybrid Systems: Computation and Control (HSCC 2020).

An additional :doc:`Developer Manual<devman>` is made available for those who are interested in interfacing their own controller synthesis tools with dtControl and/or those interested in implementing their own strategy representation algorithms.


.. Indices and tables
.. ==================

.. * :ref:`genindex`
.. * :ref:`modindex`
.. * :ref:`search`

