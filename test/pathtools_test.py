import os

import pytest

import hetio.readwrite
from hetio.pathtools import paths_between, DWPC

directory = os.path.dirname(os.path.abspath(__file__))


def test_disease_gene_example_dwpc():
    """
    Test the DWPC computation from
    https://doi.org/10.1371/journal.pcbi.1004259.g002
    """
    path = os.path.join(directory, 'data', 'disease-gene-example-graph.json')
    graph = hetio.readwrite.read_graph(path)
    metagraph = graph.metagraph

    # Define source and target nodes
    source_id = 'Gene', 'IRF1'
    target_id = 'Disease', 'Multiple Sclerosis'

    # Define GeTlD traversal
    metapath = metagraph.metapath_from_abbrev('GeTlD')
    # Extract paths
    paths = paths_between(graph, source_id, target_id, metapath)
    assert len(paths) == 1
    # Test degree-weighted path count
    dwpc = DWPC(paths, damping_exponent=0.5)
    assert dwpc == pytest.approx(2**-0.5)

    # Define GiGaD traversal
    metapath = metagraph.metapath_from_abbrev('GiGaD')
    # Extract paths
    paths = paths_between(graph, source_id, target_id, metapath)
    assert len(paths) == 3
    # Test degree-weighted path count
    dwpc = DWPC(paths, damping_exponent=0.5)
    assert dwpc == pytest.approx(0.25 + 0.25 + 32**-0.5)
