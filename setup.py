import os
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

version = 'unknown'
if os.path.exists(os.path.join(".", 'version')):
    with open(os.path.join(".", 'version')) as version_file:
        version = version_file.read().strip()

setuptools.setup(
    name="dtcontrol",
    version=version,
    description="A small tool which can convert automatically synthesised formally verified "
                "controllers into concise decision trees.",
    long_description=long_description,
    long_description_content_type="text/markdown",
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
        'tqdm==4.42.0'
    ],
    package_data={
        'dtcontrol': ['config.yml'],
        'dtcontrol.c_templates': ['*.c'],
        'dtcontrol.ui': ['*.js', '*.css', '*.html', '*.py'],
        'dtcontrol.decision_tree.OC1_source': ['*.c', '*.h', 'makefile', '*.readme', 'README'],
    }
)
