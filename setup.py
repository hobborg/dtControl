import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="dtcontrol-tum",
    version="1.0.0",
    description="A small tool which can convert automatically synthesised formally verified "
                "controllers into concise decision trees.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='MIT',
    url="https://gitlab.lrz.de/pranavashok/dtcontrol",
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
        'astutils==0.0.3',
        'decorator==4.4.1',
        'Jinja2==2.10.3',
        'joblib==0.14.0',
        'MarkupSafe==1.1.1',
        'networkx==2.4',
        'numpy==1.17.3',
        'pandas==0.25.2',
        'ply==3.10',
        'pydot==1.4.1',
        'pyparsing==2.4.2',
        'python-dateutil==2.8.0',
        'pytz==2019.3',
        'scikit-learn==0.21.3',
        'scipy==1.3.1',
        'six==1.12.0',
        'sklearn==0.0',
        'tqdm==4.36.1'
    ],
    package_data={
        'dtcontrol.c_templates': ['*.c'],
        'dtcontrol.ui': ['*.js', '*.css', '*.html', '*.py'],
        'dtcontrol.classifiers.OC1_source': ['*.c', '*.h', 'makefile', '*.readme', 'README'],
    }
)
