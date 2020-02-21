import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="dtcontrol",
    version="2.0.0.dev1",
    description="A small tool which can convert automatically synthesised formally verified "
                "controllers into concise decision trees.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Mathias Jackermeier',
    author_email='mathias.jackermeier@outlook.de',
    license='MIT',
    url="https://gitlab.lrz.de/i7/dtcontrol",
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
        'scikit-learn==0.22',
        'tqdm==4.42.0'
    ],
    package_data={
        'dtcontrol.c_templates': ['*.c'],
        'dtcontrol.ui': ['*.js', '*.css', '*.html', '*.py'],
        'dtcontrol.decision_tree.OC1_source': ['*.c', '*.h', 'makefile', '*.readme', 'README'],
    }
)
