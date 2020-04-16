import os
import subprocess
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

def git(*args):
    return subprocess.check_output(["git"] + list(args))

try:
    # Try to obtain version from the latest tag
    version = git("describe", "--tags").decode().strip()
except subprocess.CalledProcessError:
    # If not git repo or if tags are not available, use the version 'master'
    version = 'master'
# The VERSION file should not be manually edited, it is updated by the CI job
if os.path.exists(os.path.join(".", 'VERSION')):
    with open(os.path.join(".", 'VERSION')) as version_file:
        version = version_file.read().strip()

setuptools.setup(
    name="dtcontrol",
    version=version,
    description="A small tool which can convert automatically synthesised formally verified controllers into concise decision trees.",
    long_description_content_type="text/markdown",
    long_description=long_description,
    author='Mathias Jackermeier',
    author_email='mathias.jackermeier@outlook.de',
    license='MIT',
    url="https://dtcontrol.model.in.tum.de/",
    packages=['dtcontrol',
              'dtcontrol.c_templates',
              'dtcontrol.dataset',
              'dtcontrol.decision_tree',
              'dtcontrol.decision_tree.determinization',
              'dtcontrol.decision_tree.impurity',
              'dtcontrol.decision_tree.pre_processing',
              'dtcontrol.decision_tree.splitting',
              'dtcontrol.decision_tree.OC1_source',
              'dtcontrol.post_processing',
              'dtcontrol.ui',
              ],
    entry_points={
        'console_scripts': ['dtcontrol=dtcontrol.cli:main'],
    },
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        'License :: OSI Approved :: MIT License'
    ],
    python_requires='>=3.6',
    install_requires=[
        'Jinja2==2.10.3',
        'pandas==0.25.2',
        'psutil==5.6.7',
        'pydot==1.4.1',
        'ruamel.yaml==0.16.10',
        'scikit-learn==0.22',
        'tabulate==0.8.6',
        'tqdm==4.42.0'
    ],
    package_data={
        'dtcontrol': ['config.yml'],
        'dtcontrol.c_templates': ['*.c'],
        'dtcontrol.ui': ['*.js', '*.css', '*.html', '*.py'],
        'dtcontrol.decision_tree.OC1_source': ['*.c', '*.h', 'makefile', '*.readme', 'README'],
    }
)
