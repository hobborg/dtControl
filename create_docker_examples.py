import os
import shutil

from dtcontrol.benchmark_suite import BenchmarkSuite

datasets = [
    'cartpole',
    'cruise-latest',
    'dcdc',
    '10rooms',
    'vehicle'
]

bs = BenchmarkSuite()
bs.add_datasets('examples', include=datasets)
for ds in bs.datasets:
    ds.load_if_necessary()

if os.path.exists('../docker/examples'):
    shutil.rmtree('../docker/examples')

shutil.copytree('examples', 'docker/examples')

# manual cleanup is required! Remove the zip files and all unwanted scs or dump files.
