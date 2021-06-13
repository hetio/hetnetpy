# Hetnets in Python

[![CI Status](https://img.shields.io/github/workflow/status/hetio/hetnetpy/Build/main?label=actions&logo=github)](https://github.com/manubot/catalog/actions)
[![PyPI](https://img.shields.io/pypi/v/hetnetpy.svg?logo=pypi&logoColor=white)](https://pypi.org/project/hetnetpy/)
[![Latest DOI](https://zenodo.org/badge/14475/dhimmel/hetio.svg)](https://zenodo.org/badge/latestdoi/14475/dhimmel/hetio)
[![GitHub issues](https://img.shields.io/github/issues/hetio/hetnetpy.svg?logo=github)](https://github.com/hetio/hetnetpy/issues)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg?logo=python)](https://github.com/python/black)

## Overview

Hetnetpy is a Python 3 package for creating, querying, and operating on hetnets.
This software provides convenient data structures for hetnets, as well as algorithms for edge prediction.
It is specifically tailored and streamlined for hetnets compared to other more generic network software.
See https://het.io/software for additional software packages designed specifically for hetnets.

## Package relocation

Note that this package was previously named `hetio`, available at the following repositories:

- <https://github.com/hetio/hetnetpy> (current)
- <https://github.com/hetio/hetio> (former)
- <https://github.com/dhimmel/hetio> (former)

In July 2019, the package was [renamed](https://github.com/hetio/hetnetpy/issues/40) to `hetnetpy` to more clearly represent its functionality and disambiguate it from other products.

## Background

**Hetnets**: Hetnets, also [called](https://doi.org/10.15363/thinklab.d104) *heterogeneous information networks*, are graphs with multiple node and edge types. Hetnets are both multipartite and multirelational. They provide a scalable, intuitive, and frictionless structure for data integration.

**Purpose**: This package provides data structures for hetnets and algorithms for [edge prediction](http://het.io/hnep/). It only supports hetnets, which is its primary advantage compared to other network software. Node/edge attributes and edge directionality are supported.

**Impetus**: Development originated with a [study](https://doi.org/10.1371/journal.pcbi.1004259 "Heterogeneous Network Edge Prediction: A Data Integration Approach to Prioritize Disease-Associated Genes") to predict disease-associated genes and continues with a successive [study](https://doi.org/10.7554/eLife.26726 "Systematic integration of biomedical knowledge prioritizes drugs for repurposing") to repurpose drugs.

**Caution**: Documentation is currently spotty, testing coverage is moderate, and the API is not fully stable. Contributions are welcome. Please use [GitHub Issues](https://github.com/hetio/hetnetpy/issues) for feedback, questions, or troubleshooting.

## Installation

[![PyPI](https://img.shields.io/pypi/v/hetnetpy.svg?logo=pypi&logoColor=white)](https://pypi.org/project/hetnetpy/)

Please use Python 3.4 or higher. To install the current PyPI version (recommended), run:

```sh
pip install hetnetpy
```

For the latest GitHub version, run:

```sh
pip install git+https://github.com/hetio/hetnetpy.git#egg=hetnetpy
```

For development, clone or download-and-extract the repository. Then run `pip install --editable .` from the repository's root directory. The `--editable` flag specifies [editable](https://pythonhosted.org/setuptools/setuptools.html#development-mode) mode, so updating the source updates your installation.

Once installed, tests can be executed by running `py.test test/` from the repository's root directory. 

## Design

A Graph object stores a heterogeneous network and relies on the following classes:

1. Graph
2. MetaGraph
3. Edge
4. MetaEdge

## Development

This repo uses pre-commit:

```sh
# run once per local repo before committing
pre-commit install
```

This following is only relevant for maintainers.
Create a new release at <https://github.com/hetio/hetnetpy/releases/new>.
GitHub Actions will build the distribution and upload it to PyPI.
The version information inferred from the Git tag using [setuptools_scm](https://github.com/pypa/setuptools_scm/).

## License

This repository is dual licensed, available under either or both of the following licenses:

1. BSD-2-Clause Plus Patent License at [`LICENSE-BSD.md`](LICENSE-BSD.md)
2. CC0 1.0 Universal Public Domain Dedication at [`LICENSE-CC0.md`](LICENSE-CC0.md)
