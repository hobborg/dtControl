from dtcontrol.classifiers.oc1_parser import OC1Parser
from dtcontrol.dataset.multi_output_dataset import MultiOutputDataset

parser = OC1Parser()
node = parser.parse_dt('oc1_tmp/oc1_dt')

def num_nodes(tree):
    sum = 1
    if tree.left is not None:
        sum += num_nodes(tree.left)
    if tree.right is not None:
        sum += num_nodes(tree.right)
    return sum

print(num_nodes(node))

ds = MultiOutputDataset('examples/vehicle.scs')
ds.load_if_necessary()
ds.get_unique_labels()
node.set_labels(lambda x: ds.map_unique_label_back(x.trained_label), ds.index_to_value)
print(ds.compute_accuracy(node.predict(ds.X_train)))