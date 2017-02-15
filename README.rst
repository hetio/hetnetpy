Hetnets in Python
=================

|Latest DOI| |GitHub issues|

Background
----------

**Hetnets**: Hetnets, also
`called <https://doi.org/10.15363/thinklab.d104>`__ *heterogeneous
information networks*, are graphs with multiple node and edge types.
Hetnets are both multipartite and multirelational. They provide a
scalable, intuitive, and frictionless structure for data integration.

**Purpose**: This package provides data structures for hetnets and
algorithms for `edge prediction <http://het.io/hnep/>`__. It only
supports hetnets, which is its primary advantage compared to other
network software. Node/edge attributes and edge directionality are
supported.

**Impetus**: Development originated with a
`study <https://doi.org/10.1371/journal.pcbi.1004259>`__ to predict
disease-associated genes and continues with a successive
`study <https://doi.org/10.15363/thinklab.4>`__ to repurpose drugs.

**Caution**: Documentation is currently lacking, testing coverage is
poor, and the API is unstable. Contributions are welcome. Please use
`GitHub Issues <https://github.com/dhimmel/hetio/issues>`__ for
feedback, questions, or troubleshooting.

Installation
------------

|PyPI|

Please use Python 3.4 or higher. To install the current PyPI version
(recommended), run:

.. code:: sh

    pip install hetio

For the latest GitHub version, run:

.. code:: sh

    pip install git+https://github.com/dhimmel/hetio.git#egg=hetio

For development, clone or download-and-extract the repository. Then run
``pip install -e .`` from the repository's root directory. The ``-e``
flag specifies
`editable <https://pythonhosted.org/setuptools/setuptools.html#development-mode>`__
mode, so updating the source updates your installation.

Once installed, tests can be executed by running ``py.test test/`` from
the repository's root directory.

Design
------

A Graph object stores a heterogeneous network and relies on the
following classes:

1. Graph
2. MetaGraph
3. Edge
4. MetaEdge

.. |Latest DOI| image:: https://zenodo.org/badge/14475/dhimmel/hetio.svg
   :target: https://zenodo.org/badge/latestdoi/14475/dhimmel/hetio
.. |GitHub issues| image:: https://img.shields.io/github/issues/dhimmel/hetio.svg
   :target: https://github.com/dhimmel/hetio/issues
.. |PyPI| image:: https://img.shields.io/pypi/v/hetio.svg
   :target: https://pypi.python.org/pypi/hetio
