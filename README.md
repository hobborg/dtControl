# dtControl: Decision Tree Learning Algorithms for Controller Representation

### System requirements 

To run dtControl, you need Python 3.6.8 or higher with several libraries, namely numpy, pandas, scikit-learn, jinja2 and tqdm. This README explains how to install all of these on a Linux machine.


## Installing dtControl on your machine

For most users, running

```
$ pip install dtcontrol
```

inside a new virtual environment (for details, see next section) should install the latest version of dtControl, as long as you have `python >= 3.6.8` and `pip` installed on your system (if not, install python by following the steps in the next section and try again). In case you have both `python2` as well as `python3` installed on your system, you might have to run `python3 -m pip install dtcontrol`.

### Manual Installation

*Note: In case of difficulty when following any of the instructions in this section, please check the section 'Common Installation Issues' below*

1. Make sure you have `python3.6.8` (or newer) and `pip3`

Ubuntu 16.10 or newer:
```
$ sudo apt-get install python3.6 python3-pip
```

MacOS:
```
$ brew install python3
```

2. We use a virtual environment to make sure that the installation is clean and easy, and does not interfere with the python packages installed in your system. Create a new folder `dtcontrol` and create a virtual environment inside it

```
$ mkdir dtcontrol
$ cd dtcontrol
$ python3 -m venv venv
```

to create a virtual environment for _dtControl_. This will create the folder `venv` inside your `dtcontrol` folder. To uninstall the tool, you can delete this folder and thereby all traces of the python packages you installed for using it.

4. Run 

```
$ source venv/bin/activate
```

to enter the virtual environment. Run `python` and check that the displayed version is greater than 3.6.8 (if not, see (3) in the next section). Press Ctrl+D to exit the python console again.

5. With the virtual environment activated, run 

```
$ pip install dtcontrol
```

This should install _dtControl_ and all its dependencies. Try running _dtControl_ by typing `dtcontrol` in the console. It should print the help text.


### Common Installation Issues

1. If `sudo apt-get install python3.6` does not work, this might help you: https://askubuntu.com/questions/865554/how-do-i-install-python-3-6-using-apt-get.
2. In case of errors when trying to run `virtualenv`, check that it is located in a directory that is included in your path; this might help you: https://stackoverflow.com/questions/31133050/virtualenv-command-not-found.
3. If you don't see what went wrong, leave the virtual environment (run "deactivate"), delete the folder `rm -rf ~/dtcontrol-venv` and go through all the installation steps again. If errors still occur, look at section *Fail safe: Virtual machine*.


## Running the experiments

This section assumes you have installed _dtControl_ so that upon entering `dtcontrol` in your command line, the help text is displayed. Additionally it assumes that you have unzip-ed all examples in `./dtcontrol/examples`.

Note that running all experiments may take several hours, or possibly run out of memory. A sensible subset of case studies which run quickly (less than 5 minutes per case study/algorithm combination) is: `cartpole`, `tworooms`, `10rooms` and `vehicle` (vehicle not for the linsvm method).

To execute a single algorithm on a single model, run a command like
```
$ dtcontrol --input ./dtcontrol/examples/cartpole.scs --use-preset maxfreq --timeout 30m
```

More information can be found by running

```
$ dtcontrol --help
```


## Reading the output

To get an overview of the results, the file `benchmark.html` is created in the directory from which you call `dtcontrol`.  You can open it in any browser.

