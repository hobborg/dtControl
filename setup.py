import os
import subprocess
import setuptools

with open("README.rst", "r", encoding='utf-8') as fh:
    long_description = fh.read()


def git(*args):
    return subprocess.check_output(["git"] + list(args))


try:
    # Try to obtain version from the latest tag
    version = git("describe", "--tags").decode().strip()
except subprocess.CalledProcessError:
    # If not git repo or if tags are not available, use the version 'master'
    version = 'master'
except:
    version = 'master'
# The VERSION file should not be manually edited, it is updated by the CI job
if os.path.exists(os.path.join(".", 'VERSION')):
    with open(os.path.join(".", 'VERSION')) as version_file:
        version = version_file.read().strip()

setuptools.setup(
    name="dtcontrol",
    version=version,
    description="A small tool which can convert automatically synthesised formally verified controllers into concise decision trees.",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    author='Christoph Weinhuber',
    author_email='christoph.weinhuber@tum.de',
    license='MIT',
    url="https://dtcontrol.model.in.tum.de/",
    packages=['dtcontrol',
              'dtcontrol.c_templates',
              'dtcontrol.dataset',
              'dtcontrol.decision_tree',
              'dtcontrol.decision_tree.determinization',
              'dtcontrol.decision_tree.impurity',
              'dtcontrol.decision_tree.splitting',
              'dtcontrol.decision_tree.splitting.context_aware',
              'dtcontrol.decision_tree.OC1_source',
              'dtcontrol.frontend',
              'dtcontrol.post_processing',
              'dtcontrol.pre_processing',
              'dtcontrol.ui',
              ],
    entry_points={
        'console_scripts': ['dtcontrol=dtcontrol.cli:main',
                            'dtcontrol-frontend=dtcontrol.frontend.app:start_web_frontend'],
    },
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        'License :: OSI Approved :: MIT License'
    ],
    python_requires='>=3.8',
    install_requires=[
        'dd==0.5.5',
        'astutils==0.0.4',
        'ply==3.10',
        'networkx==2.6.3',
        'psutil==5.9.0',
        'pydot==1.4.1',
        'pyparsing==3.0.7',
        'setuptools==45.2.0',
        'Flask==1.1.2',
        'click==8.0.3',
        'itsdangerous==2.0.1',
        'Jinja2==2.10.3',
        'MarkupSafe==2.0.1',
        'Werkzeug==2.0.2',
        'pandas==0.25.2',
        'numpy==1.22.2',
        'python-dateutil==2.8.2',
        'six==1.14.0',
        'pytz==2021.3',
        'psutil==5.9.0',
        'pydot==1.4.1',
        'pyparsing==3.0.7',
        'ruamel.yaml.clib==0.2.6',
        'ruamel.yaml==0.16.10',
        'scikit-learn==0.22',
        'joblib==1.1.0',
        'numpy==1.22.2',
        'scipy==1.8.0',
        'sympy==1.6.1',
        'mpmath==1.2.1',
        'tabulate==0.8.6',
        'tqdm==4.42.0'
    ],
    package_data={
        'dtcontrol': ['config.yml'],
        'dtcontrol.c_templates': ['*.c'],
        'dtcontrol.ui': ['*.js', '*.css', '*.html', '*.py'],
        'dtcontrol.frontend': ['*/*/*.js', '*/*/*.css', '*/*/*.png', '*/*.html', '*/*/*.otf', '*/*/*.eot', '*/*/*.svg', '*/*/*.ttf', '*/*/*.woff',
                               '*/*/*.woff2'],
        'dtcontrol.decision_tree.OC1_source': ['*.c', '*.h', 'makefile', '*.readme', 'README'],
    }
)
