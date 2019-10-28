
# dtControl: Decision Tree Learning Algorithms for Controller Representation

## Repeatability Evaluation README
----------------------------------

dtControl is a tool for representing strategies/controllers (given as list of state-action-pairs) as decision trees.
Our software and data archive contains the following things:
   - The file `dtcontrol_tum-1.0.0.dev1-py3-none-any.whl`, which you can use to install dtcontrol, given that you possess python 3.6 or higher.
    - The folder `examples`, which contains zip-archives for all the case studies we use in the paper.
    - The scripts `quickExperiments.sh`, `severalExperiments.sh` and `allExperiments.sh` which run a quick subset of  experiments (~10min), several (those that are not prone to getting a memout, n hours) or all the experiments of the paper (n hours). TODO times
    - The `UserManual.pdf` which describes how to use `dtControl`.
    - The `DeveloperManual.pdf` which describes how you can extend `dtControl`.
    - The folder `dtcontrol`, which contains the source code for `dtControl`. 

You need this only if you are interested in looking at the code, it is not necessary for repeating the experiments.


### Elements of the paper included in the REP 

You can run our tool and verify that the input and output specifications we describe in Section 2 "Tool" of the paper are correct. For that, it makes sense to run all (or part of) the experiments, the results of which are aggregated in Table 1 on page 5 of the paper. This means running up to 8 algorithms on up to 10 case studies. Additionally, to test robustness, you could also run `dtcontrol` on other controllers given as UPPAAL (`*.dump`), SCOTS (`*.scs`) or generic (`*.csv`) files.


### System requirements 

To run dtControl, you need Python 3.6.8 or higher with several libraries, namely numpy, pandas, scikit-learn, jinja2 and tqdm. This README explains how to install all of these on a Linux machine. TODO hardware requirements


## Installing dtControl on your machine
---------------------------------------

_Note: In case of difficulty when following any of the instructions in this section, please check the section 'Common Installation Issues' below_

1. Make sure you have `python3.6.8` (or newer) and `pip3` (`sudo apt-get install python3.6 python3-pip`).
2. We use `virtualenv` to make sure that the installation is clean and easy, and does not interfere with the python packages installed in your system. Install `virtualenv` by running `sudo apt-get install virtualenv`. Try running `virtualenv` in the console. 
3. Then run `virtualenv ~/dtcontrol-venv` to create a virtual environment for _dtControl_. This will create the folder dtControl-virtualEnv in your home directoy. After evaluating our artifact, you can delete this folder and thereby all traces of the python packages you installed for the REP.
4. Run `source ~/dtcontrol-venv/bin/activate` to enter the virtual environment. Run `python` and check that the displayed version is greater than 3.6.8 (if not, see (3) in the next section). Press Ctrl+D to exit the python console again.
5. With the virtual environment activated, run `pip install dtcontrol_tum-1.0.0.dev1-py3.whl`. This should install _dtControl_ and all its dependencies. Try running _dtControl_ by typing `dtcontrol` in the console. It should print the help text.
6. Before you can run the experiments, you need to unzip all the examples; for this, go to the examples folder and execute    `unzip '*.zip'` (Note the quotation marks around `*.zip`)


### Common Installation Issues

1. If `sudo apt-get install python3.6` does not work, this might help you: https://askubuntu.com/questions/865554/how-do-i-install-python-3-6-using-apt-get.
2. In case of errors when trying to run `virtualenv`, check that it is located in a directory that is included in your path; this might help you: https://stackoverflow.com/questions/31133050/virtualenv-command-not-found.
3. If the python version is not greater than 3.6.8, `virtualenv` may have picked the wrong python version. This might help you to change that: https://stackoverflow.com/questions/45293436/how-to-specify-python-version-used-to-create-virtual-environment?rq=1.
4. If you don't see what went wrong, leave the virtual environment (run "deactivate"), delete the folder `rm -rf ~/dtcontrol-venv` and go through all the installation steps again. If errors still occur, look at section _Fail safe: Virtual machine_.


### Fail safe: Virtual machine

In case you cannot install _dtControl_ on you machine, you can use a virtual machine we prepared with _dtControl_ pre-installed. The VM image was tested with VirtualBox 5.1.38.
1. Download the virtual machine from TODO. (It is based on the vm of the TACAS20 artifact evaluation)
2. Open VirtualBox, import the VM you just downloaded and start it (we gave it 4GB RAM and 2 CPUs of a 4 core 3.2 GHz CPU).
3. To enter the virtual environment where everything is installed, run `source ~/dtcontrol-venv/bin/active`
4. Then you should be able to run _dtcontrol_ just by typing `dtcontrol`.


## Running the experiments
--------------------------

This section assumes you have installed _dtControl_ so that upon entering `dtcontrol` in your command line, the help text is displayed. Additionally it assumes that you have unzip-ed all examples in `~/examples` and that your working directory is the home folder.

Note that running all experiments may take several hours, or possibly run out of memory. A sensible subset of case studies which run quickly (less than 5 minutes per case study/algorithm combination) is: `cartpole`, `tworooms`, `10rooms` and `vehicle` (vehicle not for the linsvm method).

To execute a single algorithm on a single model, run a command like
```
dtcontrol -i ~/examples/cartpole.scs -m linsvm -t 30m --artifact
```
where you can replace `cartpole.scs` and `linsvm` with any example and method respectively.
   
We prepared three shell scripts to make your job simpler.
1. `sh quickExperiments.sh` runs all the case study/algorithm combinations which take less than 5 minutes; the whole script should not take more than 10 minutes.
2. `sh severalExperiments.sh` runs most of the experiments, but excludes those which need a lot of memory or which timed out even on our server. This gives you almost the complete table, but needs n hours. TODO: time
3. `sh allExperiments.sh` runs all the experiments that we used to get Table 1 of the paper. It will take several hours and might produce out-of-memory errors.

In case you want to run any other subset of the experiments, please read the User Manual (`UserManual.pdf`) or look at the contents of the above shell scripts to understand how to call `dtcontrol`.


## Reading the output
---------------------

To get an overview of the results, the file `benchmark.html` is created in the directory from which you call `dtcontrol`.  You can open it in any browser. It has the same structure as Table 1 in the paper, but the cells contain more information. The relevant number (which is reported in Table 1) is the number of decision paths (labeled 'paths'). As the algorithms involve some random choices, the number of decision paths can vary, but it should be in the correct order of magnitude. The DOT and C-Code representations of the decision trees are saved in the folder named `decision_trees` located in the folder from which you executed `dtcontrol`. You can also view them from the `benchmark.html` page by clicking "view dot/C file" in any cell. See the User Manual (`UserManual.pdf`) for more information on our output.

Note that in the paper, we report several "-" under the OC1 column due to failure to produce a result. Since then, we introduced a fallback mechanism that applies CART when OC1 fails to fit the data, so now in the OC1 column there may be results while in the paper we had "-".

