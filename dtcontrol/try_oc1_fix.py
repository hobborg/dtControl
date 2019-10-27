from dtcontrol.classifiers.oc1_wrapper import OC1Wrapper
from dtcontrol.dataset.single_output_dataset import SingleOutputDataset

oc1 = OC1Wrapper()
ds = SingleOutputDataset('../XYdatasets/tworooms_large.vector')
ds.load_if_necessary()
ds.get_unique_labels()
pred = oc1.predict(ds)
print(pred)
ds.compute_accuracy(pred)