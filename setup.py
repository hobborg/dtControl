import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="dtcontrol",
    version="1.0.0rc4",
    description="A small tool which can convert automatically synthesised formally verified "
                "controllers into concise decision trees.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Mathias Jackermeier',
    author_email='mathias.jackermeier@outlook.de',
    license='MIT',
    url="https://gitlab.lrz.de/i7/dtcontrol",
    packages=['dtcontrol', 'dtcontrol.classifiers', 'dtcontrol.dataset', 'dtcontrol.ui',
              'dtcontrol.classifiers.OC1_source',
              'dtcontrol.c_templates'
              ],
    entry_points={
        'console_scripts': ['dtcontrol=dtcontrol.cli:main'],
    },
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        'License :: OSI Approved :: MIT License'
    ],
    python_requires='>=3.6',
    install_requires=[
        'Jinja2==2.10.3',
        'pandas>=0.25.2',
        'pydot==1.4.1',
        'scikit-learn>=0.22',
        'tqdm>=4.36.1'
    ],
    package_data={
        'dtcontrol.c_templates': ['*.c'],
        'dtcontrol.ui': ['*.js', '*.css', '*.html', '*.py'],
        'dtcontrol.classifiers.OC1_source': ['*.c', '*.h', 'makefile', '*.readme', 'README'],
    }
)
