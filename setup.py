import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="dtcontrol-tum",
    version="1.0.dev1",
    description="A small tool which can convert automatically synthesised formally verified controllers into concise decision trees.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.lrz.de/pranavashok/dtcontrol",
    packages=['dtcontrol', 'dtcontrol.classifiers', 'dtcontrol.dataset', 'dtcontrol.ui'],
    entry_points={
        'console_scripts': ['dtcontrol=dtcontrol.cli:main'],
    },
    classifiers=[
        "Programming Language :: Python :: 3"
    ],
    python_requires='>=3.6',
)
