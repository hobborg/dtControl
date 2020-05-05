***************************************************************************
dtControl: Decision Tree Learning Algorithms for Controller Representation
***************************************************************************

*******************
System requirements
*******************

To run dtControl, you need Python 3.6.8 or higher with several other libraries which are automatically installed if installing with the python-based ``pip`` package manager. We have tested the installation and basic functionality on Ubuntu Linux, MacOS Catalina and Windows 10.


************************************
Installing dtControl on your machine
************************************

For most users, running the following command should install the latest version of dtControl, as long as you have Python 3.6.8 or newer and ``pip`` installed on your system::

    $ pip install dtcontrol

Note that in case you have both Python 2 as well as Python 3 installed, you might have to run ``python3 -m pip install dtcontrol``.


*******************
Manual Installation
*******************

*Note: In case of difficulty when following any of the instructions in this section, please check the section 'Common Installation Issues' below*

1. Make sure you have Python 3.6.8 (or newer), `pip3` and `python3-venv` for creating virtual environments.

   On **Ubuntu** 16.10 or newer::

    $ sudo apt-get install python3 python3-pip python3-venv

   On **MacOS**, you can install with the help of the package manager `Homebrew <https://brew.sh/>`_::

    $ brew install python3

   or refer to this `tutorial <https://docs.python-guide.org/starting/install3/osx/>`_ if you don't have Homebrew installed.

   On **Windows**, one may follow `this <https://docs.python-guide.org/starting/install3/win/>`__ or `this <https://installpython3.com/windows/>`__ tutorial.

2. Use a virtual environment to make sure that the installation is clean and easy, and does not interfere with any other python packages installed in your system. Create a new folder ``dtcontrol`` and create a virtual environment inside it and activate the virtual environment::

       $ mkdir dtcontrol
       $ cd dtcontrol
       $ python3 -m venv venv
       $ source venv/bin/activate

   Run ``python`` and verify that the displayed version is greater than 3.6.8. Press ``Ctrl+D`` to exit the python console again.
3. With the virtual environment activated, run::

       $ pip install dtcontrol

   This should install *dtControl* and all its dependencies. Try running *dtControl* by typing dtControl in the console. It should print the help text.


**Uninstallation** You can delete the ``dtcontrol`` folder created above to delete all traces of dtcontrol as well as its dependencies.

**************************
Common Installation Issues
**************************

1. If ``sudo apt-get install python3.6`` does not work, this `askubuntu answer <https://askubuntu.com/questions/865554/how-do-i-install-python-3-6-using-apt-get)>`_ might help you.
2. In case of errors when trying to run ``virtualenv``, check that it is located in a directory that is included in your path; this `stackoverflow answer <https://stackoverflow.com/questions/31133050/virtualenv-command-not-found>`_ might be relevant.
3. If you don't see what went wrong, leave the virtual environment (run "deactivate"), delete the folder ``rm -rf ~/dtcontrol-venv`` and go through all the installation steps again. If errors still occur, please `raise an issue <https://gitlab.lrz.de/i7/dtcontrol/-/issues/new?issue%5Bassignee_id%5D=&issue%5Bmilestone_id%5D=>`_ or `contact us <https://dtcontrol.model.in.tum.de>`_.

***********************
Running the experiments
***********************

This section assumes you have installed *dtControl* so that upon entering dtControl in your command line, the help text is displayed. Additionally it assumes that you have unzip-ed all examples in ``./dtcontrol/examples``. You can `download dtControl examples <https://gitlab.lrz.de/i7/dtcontrol-examples/-/archive/master/dtcontrol-examples-master.zip>`_ and extract them into `./dtcontrol/examples` or run the following from the terminal::

    $ cd ./dtcontrol
    $ git clone https://gitlab.lrz.de/i7/dtcontrol-examples.git examples

Further, you may either manually unzip the specific case study you would like to run or use the following command to unzip all case studies at once::

    $ find . -name "*.zip" | while read filename; do unzip -o -d "`dirname "$filename"`" "$filename"; done;

However, be warned that this would use up about 13GB of space.

To execute a single algorithm on a single model, run a command like::

    $ dtcontrol --input ./dtcontrol/examples/cartpole.scs --use-preset maxfreq --timeout 30m

If run successfully, this should create a ``benchmark.html`` file displaying the results of the current run. It should also create a ``decision_trees`` folder containing the output (DOT and C files) decision trees.

We have pre-defined a few preset methods, which can be listed using::

    $ dtcontrol preset --list

Run ``dtcontrol preset --sample`` or see the `manual <https://dtcontrol.readthedocs.io>`_ for details on how to pick and mix your own presets.

Other commands can be found by running::

    $ dtcontrol --help

******************
Reading the output
******************

To get an overview of the results, the file ``benchmark.html`` is created in the directory from which you call dtControl.  You can open it in any browser.
