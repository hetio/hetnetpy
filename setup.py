import subprocess

import setuptools


try:
    # Try to create an reStructuredText long_description from README.md
    args = 'pandoc', '--from', 'markdown', '--to', 'rst', 'README.md'
    long_description = subprocess.check_output(args)
    long_description = long_description.decode()
except Exception as error:
    # Fallback to markdown (unformatted on PyPI) long_description
    print('README.md conversion to reStructuredText failed. Error:')
    print(error)
    with open('README.md') as read_file:
        long_description = read_file.read()


setuptools.setup(
    # Package details
    name='hetio',
    version='0.2.4',
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

    # Run-time dependencies
    install_requires=[
        'regex',
    ],

    # Additional groups of dependencies
    extras_require={
        'stats': ['pandas', 'matplotlib', 'seaborn'],
        'neo4j': ['pandas', 'py2neo', 'tqdm'],
    }
)
