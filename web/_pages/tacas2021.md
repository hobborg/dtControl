---
permalink: "/artifacts/tacas2021/"

layout: artifacts

logo: /assets/images/logo.png

title: dtControl

summary: Represent controllers as decision trees. Improve memory footprint, boost explainability while preserving guarantees.

toc: true
---

# Artifact Evaluation Instructions: TACAS 2021 submission 

Here we explain how to reproduce the results of the TACAS 2021 submission **dtControl 2.0: Explainable Strategy Representation via Decision Tree Learning Steered by Experts**.
More concretely, we show how to 
1. Prepare your machine in order to run dtControl dtControl
2. Reproduce all figures and tables from the paper using pre-written scripts
3. Use the tool in general (Robustness testing)

More detailed instructions follow. 
Note that we always assume you are inside [our artifact folder][1] and give paths relative to that. E.g. just executing 'ls' should result in seeing the folders examples, installation and results as well as 9 python scripts.

## Paper abstract 

Recent advances have shown how decision trees are apt data
structures for concisely representing strategies (or controllers) satisfying
various objectives. Moreover, they also make the strategy more explainable.
The recent tool dtControl had provided pipelines with tools supporting strategy synthesis for hybrid systems, such as SCOTS and Uppaal
Stratego. We present dtControl  2.0, a new version with several fundamentally novel features. Most importantly, the user can now provide
domain knowledge to be exploited in the decision tree learning process
and can also interactively steer the process based on the dynamically
provided information. To this end, we also provide a graphical user interface. It allows for inspection and re-computation of parts of the result,
suggesting as well as receiving advice on predicates, and visual simulation
of the decision-making process. Besides, we interface model checkers of
probabilistic systems, namely STORM and PRISM and provide dedicated
support for categorical enumeration-type state variables. Consequently,
the controllers are more explainable and smaller.


## Preparation

### Technical setup

We tested the artifact on a PC with a 64 bit Windows 10 operating system, 24 GB RAM and a 3.00 GHz AMD Phenom II X6 1075T processor.
We ran the virtual machine with 12 GB of RAM and 2 cores of the processor, using VirtualBox 6.0.16.
The case studies have a size of ~4.5GB, so the experiments require ~5GB hard drive.
The original experiments were conducted on an Ubuntu 19.10 server with much more power, namely 250 GB RAM and a 2.2GHz Intel Xeon CPU E5-2630 v4, and we parallelized a lot.
More concrete details on the scripts are in Section "Reproducing the results of the paper"

To run dtControl, you need Python 3.7.9 or higher (which is installed automatically on the TACAS 21 VM) as well as several libraries which are included in the [zip of the artifact][1].

### Installing dtControl
We assume that you start on a clean version of the [TACAS 2021 VM](https://zenodo.org/record/4041464) and use it only for this evaluation, hence we do not bother with virtual environments.
We assume that python 3.8 and pip are already installed.
To install dtControl with all its dependencies, go to the 'installation' folder of our artifact and execute 
'''
pip3 install *
'''

TODO: This prints some errors; @Pranav: Fix this or tell people that they can ignore the error.
    launchpadlib 1.10.13 requires testresources, which is not installed.
    dtcontrol 1.13.14 has requirement psutil==5.6.7, but you'll have psutil 5.7.2 which is incompatible.

This installs dtControl in the .local/bin directory. We have to add this to the path so that we can easily execute our tool, i.e. execute
'''
export PATH="PATH:/home/tacas21/.local/bin"
'''
You can check that it worked by typing 'dtcontrol', which should print the help text of dtcontrol.

### Unpacking the case studies

The case studies are located in folder 'examples'.
To unpack them, first
'''
cd examples/cps
'''
then 
'''
unzip '*.zip' 
'''
and do the same for examples/storm. The examples in the prism and csv folder are not zipped as they are very small.

### Checking that everything worked.

We want to verify that three things work properly: The command line interface (CLI), the graphical user interface (GUI) and the python bindings which we use for the large scripts.
To do so, first execute
'''
dtcontrol
'''
which should print the help text. If it doesn't, make sure you have set the path correctly.
Then execute
'''
dtcontrol-frontend
'''
and then open firefox and go to https://127.0.0.1:5000 You should see the GUI (and not a 404 not found).
Finally, in the top level of our artifact folder, execute the script quickcheck.py by typing
'''
python quickcheck.py
'''
This executes 3 different algorithms on 2 case studies and finally opens a results page in firefox.


## Reproducing the results of the paper


### A note on the scripts we have

We offer eight scripts to reproduce the two tables we have. 
Every script is named after the schema models-representation-set, where 
- models is either 'CPS' or 'MDP'. CPS (Cyber physical systems) are the case studies for Table 1 and MDP (Markov decision processes) are the case studies for Table 2.
- representation is either 'BDD' (binary decision diagram) or 'DT' (decision tree), the two ways of representing the controller we compare in the tables.
- set is either 'subset' or 'all'. Running all experiments is very memory intensive (e.g. constructing a BDD for the larger case studies can take more than 11 GB of RAM) and time intensive (the larger case studies take more than 2 hours, and for BDD every experiment is repeated 20 times). Thus, we offer a meaningful subset for all experiments, repeating BDDs only twice and excluding the largest case studies. 

Note for the interested: You can modify the scripts yourself to modify the subset of experiments, e.g. to include a large case study for BDDs, but not repeat it 20 times.
For this, here is a quick description of the two important parameters in the scripts:
1) There always is a line 'suite.add_datasets(..., include=[...])'.
In this 'include' list, all cast studies are explicitly listed, and you can remove or add them as you see fit.
2) Similarly, there is the command 'classifiers = [...]' where all algorithms for representation are listed. By commenting some of the classifiers, you can omit them in the computation (for an example, compare the cps-bdd-subset to the cps-bdd-all script: Two case studies where excluded and all but two classifiers have been commented).
By modifying the scripts, you can reproduce as many of the results as your computational resources and time allow.

Here we report the time and memory requirements of the different scripts. We marked those we suggest to run in *bold*.
scriptname      | max RAM | time on Windows VM | theoretical maximum
*quickcheck*      | 100MB | 20sec | 6min
*cps-dt-subset*   | 870MB | 42min | 3.5h
*cps-bdd-subset*  | ~8GB  | 63min | 2.5h
cps-dt-all        | >11GB |Failed | 3.5d
cps-bdd-all       | >11GB |Failed | 17.5d
*mdp-dt-subset*   |   ?   |   ?   | 11h
*mdp-bdd-subset*  |   ?   |   ?   | 16h
mdp-dt-all        |   ?   |   ?   | 9.5d
mdp-bdd-all       |   ?   |   ?   | 47.5d
Provided that you have a good setup, you can also run the scripts in parallel to speed things up (as we did when running them for the paper).

*Expected error*: Note that we have several times observed the following behaviour of the BDD scripts: after completing several instances, the script terminates with an error related to garbage collection. In all cases, it was sufficient to just restart the script, and it continued without this error, picking up from the point where it failed.


### Table 1 - Cyber-physical systems (CPS)
To reproduce this table, we suggest to run the scripts cps-dt-subset.py and cps-bdd-subset.py, i.e. execute 
'''python cps-dt-subset.py''' and '''python cps-bdd-subset.py'''.
The results are saved in multiple formats, namely in the folders decision_trees, saved_classifiers and results. The former two are not relevant for reproducing the table.
In the results folder, you see an html and a json-file that report all the statistics of every combination of algorithm and case study. 
By running '''results/create_table.py cps''', you can automatically read the json-files and create something with the same structure as Table 1 in the paper. 
The script selects the minimum sized dtControl1, dtControl2 and BDD results from the different DT-algorithms respectively the multiple BDD repetitions and writes them to the file 'results/table2.csv'


### Table 2 - Probabilistic model checking (concretely Markov decision processes, MDP)
For this table, we suggest to run '''python mdp-dt-subset.py''' and '''python mdp-bdd-subset.py''', followed by '''results/create_table.py mdp''' to create the file 'results/table2.csv'.


### Figure 1, 4 and 5
These figures show small illustrative examples that need not be reproduced via the tool.

### Figure 3
This figure shows a screenshot of the new GUI. To start the GUI, run dtcontrol-frontend (assuming you added '/home/tacas21/.local/bin' to the PATH; note that restarting the VM resets this, so you will have to do it again).
The sidebar on the left allows the selection of the case study and the preset. 
By clicking the browse button, you can select the case study. 10rooms.scs and cartpole.scs are located in our-artifact-folder/examples/cps and firewire_abst.prism is in 
our-artifact-folder/examples/prism.
The dropdown menu allows to select the preset, i.e. the exact DT construction algorithm. Every preset induces a choice of hyperparameters. 
These hyperparamters can also be tuned by hand, but to recreate the screenshot, you do not need to use the advanced options.

Adding the case studies with their respective preset as in screenshot and then clicking the run button on the right for the first two recreates the Figure.


### Figure 2
This figure shows all the workflow and software architecture of dtControl 2.0. We suggest to read the description of the figure in the paper before continuing here.
- Controller: The CPS scripts use controllers from SCOTS and UPPAAL, the MDP scripts controllers from Storm (and hence also PRISM models). Moreover, in the description of Figure 3, we use a PRISM model. We also include an example csv controller. See [our documentation](https://dtcontrol.readthedocs.io/en/latest/devman.html#the-csv-format) for a description of the csv format.
- Predicate Domain: All these options are offered in the advanced options menu. When selecting algebraic predicates, you also are required to enter domain knowledge predicates. TODO: Describe how to use algebraic predicates, maybe how to recreate the cruise model [@Christoph?]
- Predicate Selector: Many impurity measures (including Entropy) are offered in the advanced options menu. You can use the interactive predicate selection as follows:
Assume you have reproduced Figure 3. Then click on the view icon, then 
TODO: describe edit functionality
- Determinizer: Note that this box merges several things, namely pre- and post-processing with Safe early stopping. All of these things are offered in the advanced option menu (note that MLE is considered an impurity measure, but it requires the determinizing early stopping option to be true. For more details, read Section 7 of the paper).
- User Choice and Domain Knowledge: These things were described as part of the Predicate Domain and Predicate Selector.
- Decision Tree: If you have executed any experiment, then the folder decision_trees has been created in our artifact folder. Inside this, ordered by preset and case study, you find the C-, json- and dot-files for every DT. The interactive graph is what you see when clicking the view button in the frontend, as e.g. in the description of the interactive predicate selection.
- Visualized simulation: This functionality can be accessed when viewing the interactive graph for a DT. 
TODO: Add dynamics file to examples folder and add description of how to use simulator.

## Robustness testing

You can play around with GUI and CLI, trying any combination of hyper parameters on any case study. You can also download further case studies from the Quantitative Verification Benchmark set or from our examples repository. 
You can explore DTs in the GUI and try to get better understanding, or see whether you can come up with useful predicates.

[1]:{{ site.url }}/files/tacas21.zip


TODO: 
Complete table about scripts, using the new dtControl for FTF fix; for dt-cps-all, only run the additional case studies.
Verify that the prism thing in frontend is working, actually recreate screenshot.
Write scripts to read the results.
Fix layout issues (code being displayed nicely, links, etc.)
We wanted to ahve a look at the documentation.

== For reference: If installation doesn't work, this might help ==
First install pip3 (I think it is actually there). Go to the packages folder of our zip, then run 
'''
sudo dpkg -i python3-pip_20.0.2-5ubuntu1.1_all.deb
'''
TODO: libblas3, liblapack3
Or maybe: libopenblas-dev
sudo apt-get install gfortran libopenblas-dev 