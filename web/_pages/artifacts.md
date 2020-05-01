---
permalink: "/artifacts/"

layout: default

logo: /assets/images/logo.png

title: dtControl

summary: Represent CPS controllers as decision trees. Improve memory footprint, boost explainability while preserving guarantees.

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

## Paper abstract 
<details>
<summary>Click to expand</summary>

Recent advances have shown how decision trees are apt data structures for concisely representing strategies arising out of both model checking as well as controller synthesis for cyber-physical systems.
Moreover, they make the strategy explainable and help boost understanding and trust.
This tool demonstration paper presents dtControl -- a tool that can represent strategies arising from strategy synthesis using tools like [PRISM](https://www.prismmodelchecker.org/), [Storm](www.stormchecker.org/), [UPPAAL STRATEGO](https://people.cs.aau.dk/~marius/stratego/), and [SCOTS](https://gitlab.lrz.de/hcs/scots).
We demonstrate the ease-of-use both when employing dtControl as a black box as well as when controlling all hyper-parameters.
We compare the decision tree representation to BDDs and also demonstrate the possibility of obtaining even smaller decision trees using the specialized algorithms available in the tool.
</details>

## Requirements
<details>
<summary>Click to expand</summary>

To run dtControl, you need an up-to-date version of Python 3 (>=3.6.8) and the Python package installer pip.
Additionally, for downloading the case studies, we also require that you have Git installed.
Remaining dependencies of dtControl will be automatically installed by pip.
All of these are installed together with our tool, since it is distributed using the pip package management system.


The experiments reported in the paper have been conducted on an Ubuntu Linux machine with 192GB of RAM and a Intel Xeon CPU E5-2630 v4 @ 2.20GHz. 
The full set of experiments require 22GB of RAM and takes about 2-3 hours to complete, however we also provide a reduced set of experiments which require only 1GB of RAM and finishes in less than 15 minutes.
The commands in this tutorial assume you are using command line, but an advanced user should be able to transfer the commands given here and make it work on Windows.
</details>



## Preparation
<details>
<summary>Click to expand</summary>

### Installing git

You will clone a git repository to obtain the case studies.
If you do not have it, install git by following their advice [on their official downloads website](https://git-scm.com/downloads).

### Installing python

Make sure you have Python 3.6.8 (or newer) and `pip3`

On Ubuntu 16.10 or newer:

```
$ sudo apt-get install python3 python3-pip
```

On MacOS:

```
$ brew install python3
```

On Windows, one of the ways to install Python 3 and `pip` could be using [Chocolatey](https://docs.python-guide.org/starting/install3/win/).


### Installing graphviz 

If you want to reproduce Figure 1, you need to convert a dot-file to a pdf. For this, you need graphviz. Since you have python, you can install it using

```
$ pip install graphviz
```

### Creating a virtual environment

We use `virtualenv` to make sure that the installation is clean and easy, and does not interfere with the python packages installed in your system. Install `virtualenv` by running 

```
$ sudo pip3 install virtualenv
```

Then run 

```
$ virtualenv -p python3 ~/dtcontrol/venv
```

to create a virtual environment for dtControl. 
This will create the folder `dtcontrol` in your home directoy along with the virtual environment installed into `dtcontrol/venv`. 
After evaluating our artifact, you can delete this folder and thereby all traces of the python packages you installed for reproducing our results.

To activate the virtual environment, run

```
$ source ~/dtcontrol/venv/bin/activate
```

</details>



## Installing dtControl

<details>
<summary>Click to expand</summary>


After activating the virtual environment, execute

```
$ pip install dtcontrol
```

</details>

## Obtaining the case studies

<details>
<summary>Click to expand</summary>

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

</details>


## Running dtControl

### Single case-study: Command line interface

<details>
<summary>Expand to see how to run on a single case study</summary>

To run dtControl on a single case study, execute the following (assuming you have activated the virtual environment, installed dtControl and unzipped the case studies) from the `~/dtcontrol` folder:

```
$ dtcontrol --input ~/dtcontrol/dtcontrol-examples/<case_study> --use-preset <preset>
```

where `<case_study>` is the file name of the case study, e.g. cartpole.scs
and `<preset>` is one of the available presets. For the paper, we used the `avg` preset for the MDP case studies and `mlentropy` preset for the CPS case studies.

</details>

### Complete table: Python bindings

<details>
<summary>Expand to see how to run all experiments with our prepared script</summary>

Since we want to execute several algorithms of dtControl on multiple case studies, it is quicker to use the built-in benchmarking functionality.
Download the file [qest20-artifact.py][1] and put it into the `~/dtcontrol` directory. 
This is important, as this file uses relative paths to access the case studies.
Then (assuming you have activated the virtual environment where dtControl is installed) execute

```
$ python qest20-artifact.py
```

We estimate the execution to take upto 3 hours depending on your machine specifications and will require atleast 22GB of RAM.
If you want to run a smaller subset that takes only 15 mins and requires only 1GB of RAM, you can instead use [qest20-artifact-subset.py][2].
[1]:{{ site.url }}/files/qest20-artifact.py
[2]:{{ site.url }}/files/qest20-artifact-subset.py
</details>

## Reading the output

<details>
<summary>Click to expand</summary>

### Table 1

Running dtControl creates several files. One of them is `~/dtcontrol/benchmark.html`. Open this file in a browser, and you will see a table containing the results of all the case study - algorithm combinations which were executed.
Every row corresponds to one of the case studies in Table 1 of the paper, although some of their names here contain more information (e.g. `beb.3-4.LineSeized` instead of `beb`).

In this table, there are more columns than in Table 1 of the paper.
There are two decision tree algorithms, namely *AVG* and *Multi-label*. In the paper, we report the results of AVG for the MDPs and of Multi-label for the CPS.
The other algorithm is only run since our benchmark suite runs every classifier on every model. Note that AVG does not work on the CPS, as those do not contain categorical variables, but numeric ones. The number of nodes for AVG and Multi-label correspond exactly to those in Table 1 of the paper.
There also are two BDD columns (if you used the full script), as there are two possible approaches to encode the information in a BDD, and there is no clear winner among them.
Also, we randomize the initial variable ordering of the BDD, so the numbers you get can be different from those in Table 1. The order of magnitude should still match.

### Figure 1

For every resulting decision tree, dtControl procudes a dot file for visualization. 
The one used in Figure 1 is located in `~/dtControl/decision_trees/AVG/firewire_abst.dot`.
Execute

```
$ dot -Tpdf ~/dtControl/decision_trees/AVG/firewire_abst.dot -o Figure1.pdf
```

to produce a pdf from the dot-file and then open Figure1.pdf with you favourite PDF-viewer.

### Figure 2

Figure 2 shows an overview of the modular structure of dtControl. 
To verify this structure, you can download the [source code as zip](https://gitlab.lrz.de/i7/dtcontrol/-/archive/master/dtcontrol-master.zip) or [view it on gitlab](https://gitlab.lrz.de/i7/dtcontrol).
The source code is in the dtcontrol folder. 
There you can see:
- The abstract dataset_loader in the folder dataset, with all the instantiations for the different tools
- A folder for the Determinizer, the Predicate Generator (called splitting) and the Predicate Selector (called impurity) in the folder decision_tree. 
Inside the folder, you can see the possible instantiations for each of these hyper-parameters.
- The outputting is taken care of by the `print_dot` and `print_c`methods in the `decision_tree/decision_tree.py`.

</details>


