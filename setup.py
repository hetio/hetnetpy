import os
import re
import subprocess

import setuptools


directory = os.path.dirname(os.path.abspath(__file__))

# version
init_path = os.path.join(directory, 'hetio', '__init__.py')
with open(init_path) as read_file:
    text = read_file.read()
pattern = re.compile(r"^__version__ = ['\"]([^'\"]*)['\"]", re.MULTILINE)
version = pattern.search(text).group(1)

# long_description
readme_path = os.path.join(directory, 'README.md')
try:
    # Try to create an reStructuredText long_description from README.md
    args = 'pandoc', '--from', 'markdown', '--to', 'rst', readme_path
    long_description = subprocess.check_output(args)
    long_description = long_description.decode()
except Exception as error:
    # Fallback to markdown (unformatted on PyPI) long_description
    print('README.md conversion to reStructuredText failed. Error:')
    print(error)
    with open(readme_path) as read_file:
        long_description = read_file.read()

# Testing dependencies
tests_require = [
    'numpy',
    'scipy',
]

setuptools.setup(
    # Package details
    name='hetio',
    version=version,
    url='https://github.com/dhimmel/hetio',
    description='Hetnets in Python',
    long_description=long_description,
    license='CC0 1.0',

    # Author details
    author='Daniel Himmelstein',
    author_email='daniel.himmelstein@gmail.com',

    # Package topics
    keywords='hetnet graph heterogeneous network neo4j hetio',
    classifiers=[
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],

    packages=['hetio'],

    # Specify python version
    python_requires='>=3.4',

    # Run-time dependencies
    install_requires=[
        'regex',
    ],

    # Testing dependencies
    tests_require=tests_require,

    # Additional groups of dependencies
    extras_require={
        'stats': ['pandas', 'matplotlib', 'seaborn'],
        'neo4j': ['pandas', 'py2neo', 'tqdm'],
        'matrix': ['numpy', 'scipy'],
        'test': tests_require,
    }
)
