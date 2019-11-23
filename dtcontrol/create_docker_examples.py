import glob
import os
import shutil
from os.path import join

from src.dataset.single_output_dataset import SingleOutputDataset

for file in glob.glob(join('examples', '*.scs')) + glob.glob(join('examples', '*.dump')):
    ds = SingleOutputDataset(file)
    ds.load_if_necessary()

if os.path.exists('../docker/examples'):
    shutil.rmtree('../docker/examples')

shutil.copytree('examples', '../docker/examples')
