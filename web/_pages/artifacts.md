---
permalink: "/artifacts/"

layout: artifacts

logo: /assets/images/logo.png

title: dtControl

summary: Represent CPS controllers as decision trees. Improve memory footprint, boost explainability while preserving guarantees.

toc: true
---

# Artifact Evaluation Instructions

Here we explain how to reproduce the results of the QEST 2020 submission **Compact and explainable strategy representations using dtControl**.
More concretely, we show how to 
1. Install all requirements
2. Install dtControl
3. Download and unpack the case studies
4. Run dtControl
5. Interpret the output

In the end, you will obtain Figure 1 and all the numbers reported in Table 1.

Here is a demonstration video from which you may copy-paste the commands.

<script id="asciicast-3NugWnvM7h2KXN7pcUsm18XME" src="https://asciinema.org/a/3NugWnvM7h2KXN7pcUsm18XME.js" async></script>

More detailed instructions follow.

## Paper abstract 

Recent advances have shown how decision trees are apt data structures for concisely representing strategies arising out of both model checking as well as controller synthesis for cyber-physical systems.
Moreover, they make the strategy explainable and help boost understanding and trust.
This tool demonstration paper presents dtControl -- a tool that can represent strategies arising from strategy synthesis using tools like [PRISM](https://www.prismmodelchecker.org/), [Storm](www.stormchecker.org/), [UPPAAL STRATEGO](https://people.cs.aau.dk/~marius/stratego/), and [SCOTS](https://gitlab.lrz.de/hcs/scots).
We demonstrate the ease-of-use both when employing dtControl as a black box as well as when controlling all hyper-parameters.
We compare the decision tree representation to BDDs and also demonstrate the possibility of obtaining even smaller decision trees using the specialized algorithms available in the tool.


## Requirements

To run dtControl, you need an up-to-date version of Python 3 (>=3.6.8) and the Python package installer pip.
Additionally, for downloading the case studies, we also require that you have Git installed.
Remaining dependencies of dtControl will be automatically installed by pip.
All of these are installed together with our tool, since it is distributed using the pip package management system.


The experiments reported in the paper have been conducted on an Ubuntu Linux machine with 192GB of RAM and a Intel Xeon CPU E5-2630 v4 @ 2.20GHz. 
The full set of experiments require 22GB of RAM and takes about 2-3 hours to complete, however we also provide a reduced set of experiments which require only 1GB of RAM and finishes in less than 5 minutes.
The commands in this tutorial assume you are using command line, but an advanced user should be able to transfer the commands given here and make it work on Windows.


## Preparation

### Installing git

You will clone a git repository to obtain the case studies.
If you do not have it, install git by following their advice [on their official downloads website](https://git-scm.com/downloads).

### Installing python

Make sure you have Python 3.6.8 (or newer), `pip3` and `python3-venv` for creating virtual environments.

On **Ubuntu** 16.10 or newer:

```
$ sudo apt-get install python3 python3-pip python3-venv
```

On **MacOS**, you can install with the help of the package manager [Homebrew](https://brew.sh/).

```
$ brew install python3
```

or refer to this [tutorial](https://docs.python-guide.org/starting/install3/osx/) if you don't have Homebrew installed.

On **Windows**, one may follow [this](https://docs.python-guide.org/starting/install3/win/) or [this](https://installpython3.com/windows/) tutorial.


### Creating a virtual environment

We use a [virtual environment](https://docs.python.org/3/library/venv.html) to make sure that the installation is clean and easy, and does not interfere with the python packages installed in your system. 

For the purpose of this artifact evaluation, let us create a folder `dtcontrol` in your home directory and place our virtual environment in the folder `~/dtcontrol/venv`. This can be accomplished by running:

```
$ python3 -m venv ~/dtcontrol/venv
```

After evaluating our artifact, you can delete this folder and thereby all traces of the python packages you installed for reproducing our results.

To activate the virtual environment, run

```
$ source ~/dtcontrol/venv/bin/activate
```


## Installing dtControl


After activating the virtual environment, execute

```
$ pip3 install dtcontrol
```


## Obtaining the case studies

To obtain all case studies, first go to the dtcontrol directory

```
$ cd ~/dtcontrol
```

and then download the examples by executing

```
$ git clone https://gitlab.lrz.de/i7/dtcontrol-examples.git
```

Most of the input files are zipped. You can unpack them by executing

```
$ cd dtcontrol-examples && ./unzip_qest.sh
```


## Running dtControl

### Complete table: Python bindings

Since we want to execute several algorithms of dtControl on multiple case studies, it is quicker to use the built-in benchmarking functionality.
Download the file [qest20-artifact.py][1] and put it into the `~/dtcontrol` directory or run
```
$ cd ~/dtcontrol
$ wget https://dtcontrol.model.in.tum.de/files/qest20-artifact.py
```

This file must be placed inside the `~/dtcontrol` folder as it uses relative paths to access the case studies.
Then (assuming you have activated the virtual environment where dtControl is installed) execute

```
$ python qest20-artifact.py
```

We estimate the execution to take upto 3 hours depending on your machine specifications and will require atleast 22GB of RAM.
If you want to run a smaller subset that takes only 15 mins and requires only 1GB of RAM, you can instead use [qest20-artifact-subset.py][2]
```
$ cd ~/dtcontrol
$ wget https://dtcontrol.model.in.tum.de/files/qest20-artifact-subset.py
```

*Note that you might see many warnings and messages during execution, however, as long as all experiments run, it should be safe to ignore them.*


### Single case-study: Command line interface

To run dtControl on a single case study, execute the following (assuming you have activated the virtual environment, installed dtControl and unzipped the case studies) from the `~/dtcontrol` folder:

```
$ dtcontrol --input ~/dtcontrol/dtcontrol-examples/<case_study> --use-preset <preset>
```

where `<case_study>` is the file name of the case study, e.g. cartpole.scs
and `<preset>` is one of the available presets. For the paper, we used the `avg` preset for the MDP case studies and `mlentropy` preset for the CPS case studies.


## Reading the output

Here, we assume that you have finished running either the [complete script][1] or the [subset script][2] as described in the previous section.

### Table 1

Running dtControl creates several files. One of them is `~/dtcontrol/benchmark.html`. Open this file in a browser, and you will see a table containing the results of all the case study - algorithm combinations which were executed.

The contents of the table are the following.
- Every row corresponds to one of the case studies in Table 1 of the paper, although some of their names here contain more information (e.g. `beb.3-4.LineSeized` instead of `beb`).
- The name of each case study is accompanied with two numbers `#(s,a)`, the number of state-action pairs, and `#doc`, the domain of controller. We report `#doc` under the "Lookup table" column of Table 1 in the paper. This is size of the domain when the strategy is seen as a map from states to set of allowed actions (f: S ➔ 2ᴬ).
- The column DT which give the number of nodes in the decision tree directly correspond to the DT column in Table 1.
- There also are two BDD columns (if you ran the full script), as there are two possible approaches to encode the information in a BDD, and there is no clear winner among them. In Table 1, we report the best of the numbers we obtained. Note that we randomize the initial variable ordering of the BDD and run reordering heuristics until convergence, so the numbers you get can be different from those in Table 1. The order of magnitude should still match.


*Extra details for the curious*: All the CPS case studies use the *Multi-label Entropy* approach which exploits the non-determinism in the controller. For the MDP case studies, we use the *Attribute-value Grouping* approach which works with categorical variables.


### Figure 1

To reproduce Figure 1, you may open `~/dtcontrol/benchmark.html` in a browser and click on the "DOT" link in the DT column for `firewire_abst`.

dtControl also stores the source of this image in [Graphviz/DOT](https://graphviz.org/) format in the file `~/dtControl/decision_trees/DT/firewire_abst/DT.dot`.

### Figure 2

Figure 2 shows an overview of the modular structure of dtControl. 
To verify this structure, you can download the [source code as zip](https://gitlab.lrz.de/i7/dtcontrol/-/archive/master/dtcontrol-master.zip) or [view it on gitlab](https://gitlab.lrz.de/i7/dtcontrol).
The source code is in the dtcontrol folder. 
There you can see:
- The abstract dataset_loader in the folder dataset, with all the instantiations for the different tools
- A folder for the Determinizer, the Predicate Generator (called splitting) and the Predicate Selector (called impurity) in the folder decision_tree. 
Inside the folder, you can see the possible instantiations for each of these hyper-parameters.
- The outputting is taken care of by the `print_dot` and `print_c` methods in the `decision_tree/decision_tree.py`.

[1]:{{ site.url }}/files/qest20-artifact.py
[2]:{{ site.url }}/files/qest20-artifact-subset.py