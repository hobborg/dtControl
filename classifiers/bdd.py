import pickle
import numpy as np
import random

from dataset.single_output_dataset import SingleOutputDataset

from omega.logic import bitvector as bv
from dd import autoref as _bdd # TODO: Might use cudd


class BDD:
    """
    Standard BDD classifier, using the dd python bindings for cudd (because sylvan was broken when I tried, 17.10.19)
    """

    def __init__(self, num_restarts=40, num_jumps=20):
        self.name = 'BDD'
        self.bdd = _bdd.BDD()
        self.bdd.configure(reordering=False)


    @staticmethod
    def is_applicable(dataset):
        return isinstance(dataset, SingleOutputDataset) #TODO: Add support for multi sets by using labels

    def get_stats(self):
        # TODO: Return number of nodes of the BDD
        # Not sure whether to use the self.bdd, or the result that I have at the end of fit
        pass

    def fit(self, dataset):
        # TODO
        # get metadata from dataset
        typeTable = dict()
        X_train = 0
        Y_train = 0
        numControlInputs=2
        # bitblast vars
        # make bb_table from type_table
        bb_table = bv.bitblast_table(typeTable)
        name2node = dict()
        # for each name in bb_table: declare name and name2node[name]=bdd.var(name)
        for name in bb_table.keys():
            if bb_table[name]["type"] == "bool":
                self.bdd.declare(name)
                name2node[name] = self.bdd.var(name)
            else:  # int
                for blasted_name in bb_table[name]["bitnames"]:
                    self.bdd.declare(blasted_name)
                    name2node[blasted_name] = self.bdd.var(blasted_name)

        # reorder randomly
        myOrder = dict()
        allNames = []
        for name in bb_table.keys():
            if bb_table[name]["type"] == "bool":
                allNames += [name]
            else:  # int
                allNames += bb_table[name]["bitnames"]

        for i in range(0, len(allNames)):
            c = random.choice(allNames)
            myOrder[c] = i
            allNames.remove(c)

        _bdd.reorder(self.bdd, myOrder)
        print("OrderStart:")
        for item in sorted(self.bdd.vars):
            print("%s: %s" % (item, self.bdd.vars[item]))
        # add X_train row by row, using the bitblast
        seen = []
        mods = 0
        ctr = 0

        for idx, row in X_train.iterrows():
            y = Y_train[idx]

            # actions first, to init subres
            # TODO: if we only have two actions, i.e. action is of type bool and not bitblasted, we need to handle it separately
            subres, first_playable_action = self.init_subres_action(y, bb_table, name2node)
            for i in range(first_playable_action + 1, len(numControlInputs)):
                if y[i] == 1:
                    actionSubres = self.blast("action", i, bb_table, name2node)
                    subres = self.bdd.apply('or', subres, actionSubres)

            # now all the other variables
            for i in range(0, len(X_train.columns)):
                name = X_train.columns[i]
                if name not in bb_table.keys():
                    continue  # need to keep this currently, since the columns are there in X_train, but need not remember the value => Probably can drop this now
                if bb_table[name]["type"] == "bool":
                    if row.values.astype(str)[i] == "1":
                        subres = self.bdd.apply('and', subres, name2node[name])
                    else:
                        subres = self.bdd.apply('and', subres, bdd.apply('not', name2node[name]))
                else:  # int
                    subres = self.bdd.apply('and', subres,
                                       self.blast(name, int(row.values.astype(str)[i]), bb_table, name2node))

            if idx == 0:
                result = subres
            else:
                result = self.bdd.apply('or', result, subres)

            # Debug stuff, currently kept since I do not know whether I might need it
            # models = list(bdd.pick_iter(result, care_vars=careV))
            # print(len(models))
            # print(list(row) + list(y))
            # if (list(row)) not in seen:
            # seen = seen + [(list(row))]
            # assert mods == len(models)-sum(y)
            # mods=len(models)
            # else:
            # assert mods == len(models)
            # print("seen")
            # ctr=ctr+1
            # if idx == int(X_train.shape[0]/4):
            #    break
            if ((idx + 1) % 10000) == 0:
                print("%s nodes, BDD size %s" % (idx + 1, len(result)))
                # break
                # print(result)

        print("%s nodes, BDD size %s" % (idx + 1, len(result)))
        # print(len(seen))
        # print(ctr)

        # collect garbage and reorder heuristics
        print("Before collecting garbage: result %s, BDD %s" % (len(result), len(self.bdd)))
        self.bdd.collect_garbage()
        print("After: result %s, BDD %s" % (len(result), len(self.bdd)))

        # reorder with dd until convergence
        bddSize = len(self.bdd)
        print("0: result %s, BDD %s" % (len(result), len(self.bdd)))
        _bdd.reorder(self.bdd)
        i = 1
        while bddSize != len(self.bdd):
            print(str(i) + ": result %s, BDD %s" % (len(result), len(bdd)))
            i = i + 1
            bddSize = len(self.bdd)
            _bdd.reorder(self.bdd)

        print("final: result %s , BDD %s" % (len(result), len(bdd)))

        # check whether there is some cool cudd stuff that we can utilize

    def blast(self, name, value, bb_table, name2node):
        # name is the variable, e.g. velocity; value is the value it shall take; rest is just context that we need
        # bitblasts value and sets the according bits (according to bb_table) in the subres, using bdd and name2node
        remainder = value
        if remainder < 0:
            remainder = pow(2, len(bb_table[name]["bitnames"])) + remainder  # 2s complement

        first = True
        # iterate over bits in reverse order, set to true or false accordingly
        for j in reversed(range(0, len(bb_table[name]["bitnames"]))):
            if first:
                first = False
                if remainder - pow(2, j) >= 0:
                    remainder = remainder - pow(2, j)
                    subres = name2node[name + "_" + str(j)]
                else:
                    subres = self.bdd.apply('not', name2node[name + "_" + str(j)])
            else:
                if remainder - pow(2, j) >= 0:
                    remainder = remainder - pow(2, j)
                    subres = self.bdd.apply('and', subres, name2node[name + "_" + str(j)])
                else:
                    subres = self.bdd.apply('and', subres, self.bdd.apply('not', name2node[name + "_" + str(j)]))

        if remainder != 0:
            print("ERROR: Remainder does not come out as 0 when blasting int variable " + name + "\nIt is " + str(
                remainder) + " and was " + str(value) +  # row.values.astype(str)[i] + " at the start. #bits: " + str(
                len(bb_table[name]["bitnames"]))

        return subres

    def init_subres_action(self, y, bb_table, name2node):
        for i in range(0, len(y)):
            if y[i] == 1:
                first_playable_action = i
                break
        return self.blast("action", first_playable_action, bb_table, name2node), first_playable_action

    def predict(self, dataset):
        # TODO
        # Not sure what this does; from looking at the others, it seems to check that everything in X_train is predicted correctly
        # We could have a predict method that returns all allowed actions for some state; then use that to iterate over whole dataset.
        pass

    def save(self, filename):
        with open(filename, 'wb') as outfile:
            pickle.dump(self, outfile)

    def export_dot(self, file=None):
        pass

    def export_c(self, file=None):
        # TODO
        # Use the ITE code from old notebook; using functions for all is not nice code, but that's why it's auto generated.
        # Anyway we should compare only the compiled versions.
        pass

    def export_vhdl(self, file=None):
        pass
