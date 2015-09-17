# Hetnets in Python

## Background

**Hetnets**: Hetnets, also [called](https://doi.org/10.15363/thinklab.d104) *heterogeneous information networks*, are graphs with multiple node and edge types. Hetnets are both multipartite and multirelational. They provide a scalable, intuitive, and frictionless structure for data integration.

**Purpose**: This package provides data structures for hetnets and algorithms for [edge prediction](http://het.io/hnep/). It only supports hetnets, which is its primary advantage compared to other network software. Node/edge attributes and edge directionality are supported.

**Impetus**: Development originated with a [study](https://doi.org/10.1371/journal.pcbi.1004259) to predict disease-associated genes and continues with a successive [study](https://doi.org/10.15363/thinklab.4) to repurpose drugs.

**Caution**: Documentation is currently lacking, testing coverage is poor, and the API is unstable. Contributions are welcome. Use the [issues](/../../issues) page for feedback or troubleshooting.

## Installation

Python 2 compatibility is unkown, please use Python 3.4 or higher. To install the current version, run

```sh
pip install git+https://github.com/dhimmel/hetio.git#egg=hetio
```

For development, clone or download-and-extract the repository. Then run `pip install -e .` from the repository's root directory. The `-e` flag specifies [editable](https://pythonhosted.org/setuptools/setuptools.html#development-mode) mode, so updating the source updates your installation.

Once installed, tests can be executed by running `py.test test/` from the repository's root directory. 

## Design

A Graph object stores a heterogeneous network and relies on the following classes:

1. Graph
2. MetaGraph
3. Edge
4. MetaEdge
