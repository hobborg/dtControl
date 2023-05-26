# Installing dtControl as a New Developer

This is a short guide on how to install dtControl as a new contributer. If you want to install the tool as a user, please refer to our [documentation](https://dtcontrol.readthedocs.io/en/latest/userman.html#installation) or the [ReadMe file](https://gitlab.lrz.de/i7/dtcontrol/-/blob/master/README.rst).
Both proposed ways of installation should work on Linux (tested on Ubuntu 20.04) and MacOS.

First of all, make sure you have Python 3.8 (or newer), pip3 (usually included in the Python installation) and python3-venv for creating virtual environments. See the Manual Installation section in the [ReadMe file](https://gitlab.lrz.de/i7/dtcontrol/-/blob/master/README.rst) on how to install those.

## Version 1: PyCharm

This is a straightforward way to get an executable and modifiable version of dtControl using PyCharm. In this version, you don't need to create a virtual environment beforehand.
 
1. Clone the repository.
2. Open the project, i.e. the top-level folder containing [setup.py](https://gitlab.lrz.de/i7/dtcontrol/-/blob/master/setup.py), in PyCharm.
3. When you open the project in PyCharm for the first time, after a few seconds you should get a pop-up as follows: "File setup.py contains project dependencies. Would you like to create a virtual environment using it?" The default options (e.g. `Location: /yourpath/dtcontrol, Base interpreter: /usr/bin/python3.9, Dependencies: /yourpath/dtcontrol/setup.py`) will automatically create a virtual environment and install the requirements specified in [setup.py](https://gitlab.lrz.de/i7/dtcontrol/-/blob/master/setup.py). \
If you get no pop-up, PyCharm will still propose "Create a virtual environment using setup.py" if you try to run anything, as there is no Python interpreter configured for the project. This option will lead you to the same pop-up. \
   See [here](https://www.jetbrains.com/help/pycharm/creating-virtual-environment.html#env-requirements) for a more detailed description of this step.
4. Run the project in PyCharm. To start the frontend, you can right-click on [app.py](https://gitlab.com/live-lab/software/dtcontrol/-/blob/master/dtcontrol/frontend/app.py) and run the file directly. Of course, you can also use the PyCharm terminal to run the project, e.g. with the command `$ dtcontrol-frontend` or by directly using the command line interface of dtControl as described in the [documentation](https://dtcontrol.readthedocs.io/en/latest/index.html). 
5. Optional: If you want to run the program using your command-line, you first need to activate the virtual environment created by PyCharm. You will find the respective folder at the path you specified before, i.e. usually the parent folder of your project. By default the virtual environment is also called `dtcontrol`. Activate the environment with this command:

       $ source dtcontrol/bin/activate
   Now you can run dtControl directly from the command-line without opening PyCharm.


## Version 2: pip


1. Use a virtual environment to make sure that the installation is clean and easy, and does not interfere with any other python packages installed in your system. Create a new folder `dtcontrol`, create a virtual environment inside it and activate the virtual environment:

       $ mkdir dtcontrol
       $ cd dtcontrol
       $ python3 -m venv venv
       $ source venv/bin/activate

   Run `$ python` and verify that the displayed version is greater than 3.8. Press ``Ctrl+D`` to exit the python console again.
2. Clone the repository.
3. Navigate to the top-level project folder containing [setup.py](https://gitlab.lrz.de/i7/dtcontrol/-/blob/master/setup.py). In that folder and with the virtual environment activated, run:

       (venv) $ pip install -e .

   This will install the requirements specified in [setup.py](https://gitlab.lrz.de/i7/dtcontrol/-/blob/master/setup.py). The ``-e`` means that the project will be installed in editable mode, i.e. changes made in the code will be reflected when you run the program.
4. Run the project using the command-line, e.g. with the command `$ dtcontrol-frontend` to start the frontend or by directly using the command line interface of dtControl as described in the [documentation](https://dtcontrol.readthedocs.io/en/latest/index.html). 
5. Optional: When you are working on the project in PyCharm, you can of course use the PyCharm terminal in the same way. If you want to use PyCharm to run [app.py](https://gitlab.com/live-lab/software/dtcontrol/-/blob/master/dtcontrol/frontend/app.py) directly, you need to configure a Python interpreter and add the virtual environment you just created. This can be done for example as follows: \
`Settings -> Project: dtcontrol -> Python Interpreter -> Add Interpreter -> Add Local Interpreter... -> Virtualenv Environment -> Environment: Existing`. Next, you need to specify the path to your virtual environment, e.g. `/yourpath/venv/bin/python3.9`. \
Now you can also run the project in PyCharm using the same virtual environment.



## Notes
In case of problems, the Common Installation Issues section in the [ReadMe file](https://gitlab.lrz.de/i7/dtcontrol/-/blob/master/README.rst) might help you.

Using `$ pip install dtcontrol` might seem tempting, but it will not give you a modifiable version of dtControl. We also don't recommend trying to install the requirements this way.

# Further Onboarding

The first chapter of the [documentation](https://dtcontrol.readthedocs.io/en/latest/index.html), the [tutorial videos](https://dtcontrol.model.in.tum.de/tutorials/) on our website and the [related publications](https://dtcontrol.model.in.tum.de/#related-publications) serve as an introduction to new developers and new users alike.

To new contributers, we like to suggest writing a custom splitting strategy as a first task to get familiar with the architecture of the project. The idea of this task is not to come up with anything new or even reasonable, but to get an impression of the different classes involved in encoding a dataset, performing a split and building a decision tree. 

