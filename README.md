# Hetnets in Python

[![Latest DOI](https://zenodo.org/badge/14475/dhimmel/hetio.svg)](https://zenodo.org/badge/latestdoi/14475/dhimmel/hetio)
[![GitHub issues](https://img.shields.io/github/issues/dhimmel/hetio.svg)](https://github.com/dhimmel/hetio/issues)
[![Build Status](https://travis-ci.org/dhimmel/hetio.svg?branch=master)](https://travis-ci.org/dhimmel/hetio)

## Background

**Hetnets**: Hetnets, also [called](https://doi.org/10.15363/thinklab.d104) *heterogeneous information networks*, are graphs with multiple node and edge types. Hetnets are both multipartite and multirelational. They provide a scalable, intuitive, and frictionless structure for data integration.

**Purpose**: This package provides data structures for hetnets and algorithms for [edge prediction](http://het.io/hnep/). It only supports hetnets, which is its primary advantage compared to other network software. Node/edge attributes and edge directionality are supported.

**Impetus**: Development originated with a [study](https://doi.org/10.1371/journal.pcbi.1004259 "Heterogeneous Network Edge Prediction: A Data Integration Approach to Prioritize Disease-Associated Genes") to predict disease-associated genes and continues with a successive [study](https://doi.org/10.7554/eLife.26726 "Systematic integration of biomedical knowledge prioritizes drugs for repurposing") to repurpose drugs.

**Caution**: Documentation is currently spotty, testing coverage is moderate, and the API is not fully stable. Contributions are welcome. Please use [GitHub Issues](https://github.com/dhimmel/hetio/issues) for feedback, questions, or troubleshooting.

## Installation

[![PyPI](https://img.shields.io/pypi/v/hetio.svg)](https://pypi.python.org/pypi/hetio)

Please use Python 3.4 or higher. To install the current PyPI version (recommended), run:

```sh
pip install hetio
```

For the latest GitHub version, run:

```sh
pip install git+https://github.com/dhimmel/hetio.git#egg=hetio
```

For development, clone or download-and-extract the repository. Then run `pip install --editable .` from the repository's root directory. The `--editable` flag specifies [editable](https://pythonhosted.org/setuptools/setuptools.html#development-mode) mode, so updating the source updates your installation.

Once installed, tests can be executed by running `py.test test/` from the repository's root directory. 

## Design

A Graph object stores a heterogeneous network and relies on the following classes:

1. Graph
2. MetaGraph
3. Edge
4. MetaEdge

## Release instructions

This section is only relevant for project maintainers.
Travis CI deployments are used to upload releases to [PyPI](https://pypi.org/project/hetio) and [GitHub releases](https://github.com/dhimmel/hetio/releases).
To create a new release, do the following:

1. Bump the version in [`__init__.py`](hetio/__init__.py).

2. Add a release notes file in [`release-notes`](release-notes).
  Format as a commit message that will be used as the GitHub release description.

3. Run the following commands:
    
  ```sh
  TAG=v`python setup.py --version`
  git add hetio/__init__.py release-notes/$TAG.*
  git commit --message "Upgrade to $TAG"
  git push
  git tag --annotate $TAG --file release-notes/$TAG.*
  git push --tags
  ```

4. Recommended: Edit the GitHub release to improve formating and add a Zenodo badge.
