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
1. Prepare your machine in order to run dtControl
2. Reproduce all figures and tables from the paper using pre-written scripts
3. Use the tool in general (Robustness testing)

More detailed instructions follow. 
Note that we always assume you are inside our unzipped [artifact folder](https://dtcontrol.model.in.tum.de/files/tacas21-artifact.zip) and give 
paths relative to that. E.g. just executing `ls` should result in seeing the folders 
`examples`, `installation` and `results` as well as 9 Python scripts.

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

## Statement on archival

The artifact, on passing the artifact evaluation review, would be archived on [Zenodo](https://zenodo.org/) and made publicly available through our [website](https://dtcontrol.model.in.tum.de/artifacts/).


## Preparation

### Contents of this artifact

This artifact contains the following files and folders
- `tacas21-dtcontrol-artifact` countaining the installation files, examples and run scripts
- `TACAS_2021_paper_146.pdf`, the manuscript submitted for review and `Full-Paper-with-Appendix.pdf`, the extended version containing the appendix.
- `License.txt` containing the license text
- `Readme.txt` containing instructions on how to reproduce the tables and figures of the paper.


### Technical setup

We tested the artifact on a PC with a 64 bit Windows 10 operating system, 24 GB RAM and a 3.00 GHz AMD Phenom II X6 1075T processor.
We ran the virtual machine with 12 GB of RAM and 2 cores of the processor, using VirtualBox 6.0.16.
The case studies have a size of ~4.5GB, so the experiments require ~5GB hard drive.
The experiments in the paper were conducted on an Ubuntu 19.10 server with much more power, 
namely 250 GB RAM and a 2.2GHz Intel Xeon CPU E5-2630 v4, with multiple experiments running in parallel.
More concrete details on the scripts are in Section "Reproducing the results of the paper"

To run dtControl, you need Python 3.7.9 or higher (which is installed automatically on the TACAS 21 VM) as well as 
several libraries which are included in the [zip of the artifact](https://dtcontrol.model.in.tum.de/files/tacas21-artifact.zip). The web-based graphical user interface was tested
on Firefox 80, which comes bundled with the VM.

### Installing dtControl
We assume that you start on a clean version of the [TACAS 2021 VM](https://zenodo.org/record/4041464) and use it only 
for this evaluation, hence we do not bother with virtual environments.
We assume that `python3.8` and `pip3` are already installed.

First, we have to add `~/.local/bin` to the path so that `dtcontrol` can easily be found after installation

	$ echo "export PATH=\"$PATH:/home/tacas21/.local/bin\"" >> ~/.bashrc
	$ source ~/.bashrc

To install dtControl with all its dependencies, go to the `installation` folder of our artifact and execute 

	$ cd installation && pip3 install *

This installs dtControl in the `.local/bin` directory. 
You can check that it worked by typing `dtcontrol`, which should print the help text of dtcontrol.

### Unpacking the case studies

The case studies are located in folder `examples`.
To unpack them, first

	$ cd examples

then run 

	$ find . -name "*.zip" | while read filename; do unzip -o -d "`dirname "$filename"`" "$filename"; done;

to extract the zipped examples within all the subfolders (`examples/cps` and `examples/storm`). 
The examples in the `prism` and `csv` folder are not zipped as they are very small.

### Checking that everything worked.

We want to verify that three things work properly: The command line interface (CLI), the graphical user interface (GUI) and the python bindings which we use for the large scripts.
To do so, first execute

	$ dtcontrol

which should print the help text. If it doesn't, make sure you have set the path correctly.
Then execute

	$ dtcontrol-frontend

and then open firefox and go to `http://127.0.0.1:5000` You should see the GUI (and not a 404 not found).
Finally, in the top level of our artifact folder, execute the script `quickcheck.py` by typing

	$ python quickcheck.py

This executes 3 different algorithms on 2 case studies and finally opens a results page in firefox.


## Reproducing the results of the paper

### Scripts for convenience

We offer eight scripts (using the dtControl python bindings) to reproduce the two tables we have. 
Every script is named after the schema `<models>`-`<representation>`-`<set>.py`, where 
- `<models>` are either 'CPS' or 'MDP'. CPS (Cyber-physical systems) are the case studies for Table 1 and 
MDP (Markov decision processes) are the case studies for Table 2.
- `<representation>` is either 'BDD' (binary decision diagram) or 'DT' (decision tree), 
the two ways of representing the controllers we compare in the tables.
- `<set>` is either 'subset' or 'all'. Running all experiments is very memory intensive 
(e.g. constructing a BDD for the larger case studies can take more than 11 GB of RAM) and 
time intensive (the larger case studies take more than 2 hours, and for BDD every experiment is repeated 20 times). 
Thus, we offer a meaningful subset for all experiments, repeating BDDs only twice and excluding the largest case studies. 

Note for the interested: You can modify the scripts yourself to modify the subset of experiments, e.g. to include a 
large case study for BDDs, but not repeat it 20 times.
For this, here is a quick description of the two important parameters in the scripts:
1) There always is a line `suite.add_datasets(..., include=[...])`.
In this 'include' list, all cast studies are explicitly listed, and you can remove or add them as you see fit.
2) Similarly, there is the command `classifiers = [...]` where all algorithms for representation are listed. By commenting some of the classifiers, you can omit them in the computation (for an example, compare the cps-bdd-subset to the cps-bdd-all script: Two case studies where excluded and all but two classifiers have been commented).
By modifying the scripts, you can reproduce as many of the results as your computational resources and time allow.

Here we report the time and memory requirements of the different scripts.
Note that we are not benchmarking the memory or time requirements, and hence these are ballpark figures to help
the reviewer choose the experiments to reproduce.

We mark some suggested experiments in **bold**. OOM indicates that the script ran out of memory on our VM.

Script Name        | Max RAM | Time on TACAS VM   | Theoretical Maximum
-------------------|---------|--------------------|--------------------
**quickcheck**     | 100MB   |  20 sec            | 6min
**cps-dt-subset**  | ~1GB    |  89 min            | 3.5h
**cps-bdd-subset** | ~8GB    |  63 min            | 2.5h
cps-dt-all         | 12GB+   |  OOM               | 3.5d
cps-bdd-all        | 12GB+   |  OOM               | 17.5d
**mdp-dt-subset**  | ~1.4GB  |  37 min            | 11h
**mdp-bdd-subset** | ~3.4GB  |  38 min            | 16h
mdp-dt-all         | ~5.8GB  |  5 hours           | 9.5d
mdp-bdd-all        | 12GB+   |  OOM               | 47.5d


Provided that you have a good setup, you can also run the scripts in parallel to speed things up (as we did when running them for the paper).

*Expected error*: Note that we have several times observed the following behaviour of the BDD scripts: after completing 
several instances, the script terminates with an error related to garbage collection. In all cases, it was sufficient 
to just restart the script, and it continued without this error, picking up from the point where it failed.


### Table 1 - Cyber-physical systems (CPS)
To reproduce this table, we suggest to run the scripts `cps-dt-subset.py` and `cps-bdd-subset.py`
    
    $ python cps-dt-subset.py
    $ python cps-bdd-subset.py
    
The results are saved in multiple formats, namely in the folders `decision_trees`, `saved_classifiers` and `results`. 
The former two are not relevant for reproducing the table. In the results folder, you see an html and a 
json file that report all the statistics of every combination of algorithm and case study. You may open the 
`results/DT-CPS.html` file and the `results/BDD-CPS.html` file in a browser to compare the results with the paper.
We report the minimum sized dtControl1, dtControl2 and BDD results from the different DT-algorithms 
respectively the multiple BDD repetitions.

### Table 2 - Probabilistic model checking (concretely Markov decision processes, MDP)

To reproduce this table, we suggest to run the scripts `mdp-dt-subset.py` and `mdp-bdd-subset.py`.

    $ python mdp-dt-subset.py
    $ python mdp-bdd-subset.py

The results of Table 2 may be compiled as described for Table 1, from the `results/DT-MDP.html` file and 
the `results/BDD-MDP.html` file generated by the above commands.

### Figure 1, 4 and 5
These figures show small illustrative examples that need not be reproduced via the tool.

### Figure 3
This figure shows a screenshot of the new GUI. To start the GUI, run `dtcontrol-frontend`. 
The sidebar on the left allows the selection of the case study and the preset. 
By clicking the browse button, you can select the case study. `10rooms.scs` and `cartpole.scs` are located 
in `<our-artifact-folder>/examples/cps` and `firewire_abst.prism` is in `<our-artifact-folder>/examples/prism`.
The dropdown menu allows to select the preset, i.e. the exact DT construction algorithm. Every preset induces 
a choice of hyper-parameters. These hyper-parameters can also be tuned by hand, but to recreate the screenshot, 
you do not need to use the advanced options.

Adding the case studies with their respective preset as in screenshot and then clicking the run button on the 
right for the first two recreates the Figure.

### Figure 2
This figure shows all the workflow and software architecture of dtControl 2.0. We suggest to read the description 
of the figure in the paper before continuing here.
- Controller: The CPS scripts use controllers from SCOTS and UPPAAL, the MDP scripts controllers from 
Storm (and hence also PRISM models). Moreover, in the description of Figure 3, we use a PRISM model. 
We also include an example CSV controller. See [our documentation](https://dtcontrol.readthedocs.io/en/latest/devman.html#the-csv-format) 
for a description of the CSV format.
- Predicate Domain: All these options are offered in the advanced options menu. 
When selecting algebraic predicates, you also are required to enter domain knowledge predicates. 
The domain knowledge has to follow the structure presented in [Appendix B.2](https://dtcontrol.model.in.tum.de/dtcontrol2.pdf). 
In general, x-variables are used to refer to features. 
For example, x_0 references the first feature (whereas c-variables describe coefficients).
In order to apply the predicate **x₀ - log(x₁) >= 150**,
you only have to enter `x_0 - log(x_1) >= 150` within the input field.
For a list of provided functions see the [SymPy documentation](https://docs.sympy.org/latest/modules/functions/index.html#contents).
Multiple predicates can be separated by a newline.

- Predicate Selector: Many impurity measures (including Entropy) are offered in the advanced options menu. 
You can use the interactive predicate selection as follows:
Assume you have reproduced Figure 3. Then click on the view icon (symbolized by the eye icon). 
After clicking the edit button which can be found in the top left area, you can select a node to be modified. 
After a node is selected (visualized by an orange colour), you can click on the desired editing-technique. 
  - "Retrain from selected node" uses the *preset* which is selected in the dropdown menu above on the selected node and all its children.
  - "Start interactive tree builder from selected" provides an interactive interface for predicate selection of the selected node and all its children.
  Once this button is pressed, predicates (in our special syntax, mentioned in the *predicate domain* section above) may be added and chosen for the selected node. 
- Determinizer: Note that this box merges several things, namely pre- and post-processing with Safe early stopping. All of these things are offered in the advanced option menu (note that MLE is considered an impurity measure, but it requires the determinizing early stopping option to be true. For more details, read Section 7 of the paper).
- User Choice and Domain Knowledge: These things were described as part of the Predicate Domain and Predicate Selector.
- Decision Tree: If you have executed any experiment, then the folder `decision_trees` has been created in our artifact folder. Inside this, ordered by preset and case study, you find the C-, json- and dot-files for every DT. The interactive graph is what you see when clicking the view button in the frontend, as e.g. in the description of the interactive predicate selection.
- Visualized simulation: This functionality can be accessed by clicking on the "Simulate" button (in the top left area), when
 viewing the interactive graph of the DT. The user first needs to select a dynamics file (we provide `examples/cps/10rooms_dynamics.txt` and 
 `examples/cps/cartpole_dynamics.txt` for reference), then select some initial values (or press the randomize button), and click submit to start
 the simulation. A simulation trace can be sampled using the Play/Next buttons. The decision path is highlighted in each step. Further, charts
 displaying the progress of simulation are displayed at the bottom of the page. 

## Robustness testing

You can play around with CLI and GUI, trying any combination of hyper-parameters on any case study. 
You can also download further case studies from the [Quantitative Verification Benchmark set](http://qcomp.org/benchmarks/index.html) 
or from our [examples repository](https://gitlab.lrz.de/i7/dtcontrol-examples). You can explore DTs in the GUI and 
try to get better understanding, or see whether you can come up with useful predicates.

### Single case-study: Command line interface

To run dtControl on a single case study, execute the following (assuming that you have 
installed dtControl and unzipped the examples):

	$ dtcontrol --input examples/<location_of_controller_file> --use-preset <preset>

where `<location_of_controller_file>` is the path to an example, e.g. `cps/cartpole.scs` or `storm/wlan_dl.0.80.deadline.storm.json`.
and `<preset>` is one of the available presets (run `dtcontrol preset --list` to list all available presets, we recommend
`avg` for MDPs and `mlentropy` for the CPS benchmarks).

Note that, for the `avg` preset, there needs to be a `<controller_name>_config.json` file containing the metadata present
in the same location as the controller file.

The output tree (in JSON, C and DOT formats) can be found inside the `decision_trees/<present_name>/<controller_name>/` folder, 
and a summary will be available in the `benchmarks.html` file in the folder from which `dtcontrol` was run. 

### Interactive DT building in the GUI

To reproduce Figure 9 of the Appendix, one may follow these steps
1. Run `dtcontrol-frontend` to start the GUI and navigate to `http://127.0.0.1:5000` in the browser.
2. Upload the `examples/cps/10rooms.scs` controller along with the metadata file `examples/cps/10rooms_config.json`.
3. Select the `mlentropy` preset and run the experiment.
4. Open the interactive DT viewer by pressing the *eye icon* in the results table.
5. In the top left area, click the **Edit** mode button.
6. Click on the `x[4] <= 20.625` predicate in the tree by clicking on it and press on the "Start interactive tree builder ..." 
button in the left side bar.
7. Click on the Add predicate button in the Predicate Collection table and enter `x_0 + 3*x_1 <= c_0` and wait until
 the Instantiated Predicate table reloads.

## In case of malfunction

In case of problems with the evaluation scripts, you may try
1. The `*.json` files in the `results` folder.
2. Making sure that all the examples are unzipped.
3. Deleting the `.benchmark_suite` hidden folder inside each of the examples folders. 

In case the dtControl CLI is not working properly, you can clean up the cache by deleting
1. The `*.json` files in the folder from which `dtcontrol` is run
2. The `.benchmark_suite` hidden folder inside each of the examples folders.
3. Running `dtcontrol --help`

In case the dtControl GUI is malfunctioning, you may try
1. Looking at the server logs displayed in the terminal in which `dtcontrol-frontend` is run.
2. Looking at the browser console by pressing the F12 button (in Firefox).
3. If there are any errors, you may restart the server (press `Ctrl+C` in the terminal to kill `dtcontrol-frontend`)
and try again.

## User and Developer Manuals

More information on dtControl and its functionality can be found in the user and developer manuals at
 [dtcontrol.readthedocs.io](https://dtcontrol.readthedocs.io/en/latest/).
 
## Source Code

dtControl is developed as an open-source software, with the source available in [LRZ Gitlab](https://gitlab.lrz.de/i7/dtcontrol/). 
