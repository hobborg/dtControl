from apted import APTED
from apted.helpers import Tree
import re
import sympy as sp


# predicate 1 and 2 are sympy terms
def tree_edit_distance(predicate1, predicate2):
    def helper_formatting(tree):
        tree = sp.srepr(tree)

        formated_tree = re.sub("Integer\(.+?\)|Float\(.+?\)|Rational\(.+?\)", "{Variable}", tree)
        formated_tree = formated_tree.replace("(", "{").replace(")", "}").replace("{'x_", "").replace("{'c_", "").replace("'}", "").replace(
            ", ", "")
        formated_tree = "{" + re.sub("(Symbol\d+)", "{\\1}", formated_tree) + "}"

        return formated_tree

    tree1 = Tree.from_text(helper_formatting(predicate1))
    tree2 = Tree.from_text(helper_formatting(predicate2))

    apted = APTED(tree1, tree2)
    ted = apted.compute_edit_distance()
    # To display mapping between those two predicates
    mapping = apted.compute_edit_mapping()

    print("MAPPING:")
    for i in mapping[1:]:
        print(i)

    print("\nTREE EDIT DISTANCE: {}".format(ted))
    return ted


term1 = sp.sympify("0.5 * (c_0 - c_1) * ((-6 - x_5)/-2)^2 + (x_5 - x_3) * ((-6 - x_5)/-2)")
term2 = sp.sympify("0.5 * (c_0 - c_1) + (x_5 - x_3)")

print(term1.equals(term2))

term4 = sp.sympify("0.5 * c_0")
term5 = sp.sympify("0.5 * c_0 + x_99 * 0")
print(term4.equals(term5))

# term2 = sp.sympify(
#     "x_2 + ((-2-2)/(2)) + (x_5 - x_3) + ((x_5 + 1 * (-2)) - (x_3 + 1 * 2)) * (((-6 - x_5)/(-2))-1) + (((0-(-2))*(((-6-((x_3 + 2) - 2 * ((((-6 - x_5)/(-2))-1))))/(-2)))^2)/(2)) + (-6-((x_3 + 1 * 2) + ((((-6 - x_5)/(-2))-1)) * (-2))) * ((-6-((x_3 + 2) - 2 * ((((-6 - x_5)/(-2))-1))))/(-2))")

tree_edit_distance(term1,term2)



