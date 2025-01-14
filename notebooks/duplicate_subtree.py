import json
from tabulate import tabulate


class Node:
    def __init__(self, data):
        self.data = data
        self.true = self.false = None

    def __repr__(self):
        return str(self.data)

    def print_tree(self):
        print(self.data)
        if self.true is not None:
            self.true.print_tree()
        if self.false is not None:
            self.false.print_tree()


def reformat_tree(currentNode, tree_pointer):
    # Formats json tree into this simple Node structure.
    if currentNode["actual_label"] is None:

        tree_pointer = Node(currentNode["split"])

        tree_pointer.true = reformat_tree(currentNode["children"][0], tree_pointer.true)
        tree_pointer.false = reformat_tree(currentNode["children"][1], tree_pointer.false)
        return tree_pointer
    else:
        return Node(currentNode["actual_label"])


def inorder(node, m):
    if (not node):
        return ""

    Str = "("
    Str += inorder(node.true, m)
    Str += str(node.data)
    Str += inorder(node.false, m)
    Str += ")"

    if Str in m:
        m[Str] += 1
    else:
        m[Str] = 1

    return Str


# Wrapper over inorder()
def find_duplicate_subtrees(root):
    m = {}
    foo = inorder(root, m)

    analyze_more_detailed(m)


def analyze_more_detailed(m):
    table = []
    g = sorted(list(set(m.values())), reverse=True)
    for vals in g:
        counter = 0
        tree_lengths = []
        for k in m:
            if m.get(k) == vals:
                counter += 1
                tree_lengths.append(k.count(")"))

        table.append([vals, counter, max(tree_lengths), str(sorted(tree_lengths, reverse=True))])

    # pretty_printing
    print("\n\n" + tabulate(table, headers=["#Appearences", "#Groups", "Max Subtree Lengths", "All Lengths"], tablefmt="rst")+ "\n\n")



if __name__ == '__main__':
    path = "../decision_trees/aa-logreg/cartpole/aa-logreg.json"

    try:
        f = open(path)
        root = json.load(f)
    except:
        print("Error while parsing occured...shutting down.")
    else:
        tree = reformat_tree(root, None)
        find_duplicate_subtrees(tree)
