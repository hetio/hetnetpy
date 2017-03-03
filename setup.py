import subprocess

import setuptools


# Try to create an rst long_description from README.md
try:
    args = 'pandoc', '--from', 'markdown', '--to', 'rst', 'README.md'
    long_description = subprocess.check_output(args)
    long_description = long_description.decode()
except Exception as error:
    print('README.md conversion to reStructuredText failed. Error:')
    print(error)
    print('Setting long_description to None.')
    long_description = None


setuptools.setup(
    name = 'hetio',
    version = '0.2.3',
    author = 'Daniel Himmelstein',
    author_email = 'daniel.himmelstein@gmail.com',
    url = 'https://github.com/dhimmel/hetio',
    description = 'Hetnets in Python',
    long_description=long_description,
    license = 'CC0 1.0',
    packages = ['hetio'],
    classifiers = [
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

    install_requires = [
        'tqdm'
    ]
)
