#!/usr/bin/env sh

# Single --split
python cli.py --input examples/cartpole.scs --split axisonly --rerun
# Multiple --split
python cli.py --input examples/cartpole.scs --split linear-logreg linear-svm --rerun
# --split all
python cli.py --input examples/cartpole.scs --split all --rerun

# Single --determinize
python cli.py --input examples/cartpole.scs --determinize maxfreq --rerun
# Multiple --determinize
python cli.py --input examples/cartpole.scs --determinize maxmultifreq minnorm random --rerun
# --determinize all
python cli.py --input examples/cartpole.scs --determinize all --rerun

# omit all
python cli.py --input examples/cartpole.scs --rerun

# Single --impurity
python cli.py --input examples/cartpole.scs --impurity entropy --rerun
# Multiple --impurity
python cli.py --input examples/cartpole.scs --impurity entropy maxminority --rerun
# --impurity all
python cli.py --input examples/cartpole.scs --impurity all --rerun

# cartpole all
python cli.py --input examples/cartpole.scs --split all --determinize all --impurity all --rerun