import os

import pytest

import hetnetpy.readwrite
from hetnetpy.pathtools import DWPC, paths_between

directory = os.path.dirname(os.path.abspath(__file__))


def test_disease_gene_example_dwpc():
    """
    Test the DWPC computation from
    https://doi.org/10.1371/journal.pcbi.1004259.g002
    """
    path = os.path.join(directory, "data", "disease-gene-example-graph.json")
    graph = hetnetpy.readwrite.read_graph(path)
    metagraph = graph.metagraph

    # Define source and target nodes
    source_id = "Gene", "IRF1"
    target_id = "Disease", "Multiple Sclerosis"

    # Define GeTlD traversal
    metapath = metagraph.metapath_from_abbrev("GeTlD")
    # Test metapath unicode formatting
    unicode_str = "Gene–expression–Tissue–localization–Disease"
    assert unicode_str == metapath.get_unicode_str()
    # Extract paths
    paths = paths_between(graph, source_id, target_id, metapath)
    assert len(paths) == 1
    # Test degree-weighted path count
    dwpc = DWPC(paths, damping_exponent=0.5)
    assert dwpc == pytest.approx(2 ** -0.5)

    # Define GiGaD traversal
    metapath = metagraph.metapath_from_abbrev("GiGaD")
    # Extract paths
    paths = paths_between(graph, source_id, target_id, metapath)
    assert len(paths) == 3
    # Test degree-weighted path count
    dwpc = DWPC(paths, damping_exponent=0.5)
    assert dwpc == pytest.approx(0.25 + 0.25 + 32 ** -0.5)


def test_bupropion_CbGpPWpGaD_traversal():
    """
    Test traveral and degree-weighted walk/path counts for the CbGpPWpGaD
    metapath between bupropion and nicotine dependence.
    """
    # Read Hetionet v1.0 subgraph
    path = os.path.join(directory, "data", "bupropion-CbGpPWpGaD-subgraph.json.xz")
    graph = hetnetpy.readwrite.read_graph(path)
    metagraph = graph.metagraph

    # Define traversal
    source_id = "Compound", "DB01156"  # Bupropion
    target_id = "Disease", "DOID:0050742"  # nicotine dependences
    metapath = metagraph.metapath_from_abbrev("CbGpPWpGaD")

    # Extract walks and compute DWWC
    walks = paths_between(graph, source_id, target_id, metapath, duplicates=True)
    assert len(walks) == 152
    dwwc = DWPC(walks, damping_exponent=0.4)
    assert dwwc == pytest.approx(0.038040121429465001)

    # Extract paths and compute DWPC
    paths = paths_between(graph, source_id, target_id, metapath, duplicates=False)
    assert len(paths) == 142
    dwpc = DWPC(paths, damping_exponent=0.4)
    assert dwpc == pytest.approx(0.03287590886921623)

    # Below is equivalent Cypher for the path count / DWPC test,
    # runnable at https://neo4j.het.io
    """
    MATCH path = (n0:Compound)-[:BINDS_CbG]-(n1)-[:PARTICIPATES_GpPW]-(n2)
      -[:PARTICIPATES_GpPW]-(n3)-[:ASSOCIATES_DaG]-(n4:Disease)
    USING JOIN ON n2
    WHERE n0.identifier = 'DB01156'
      AND n4.identifier = 'DOID:0050742'
      AND n1 <> n3
    WITH
    [
      size((n0)-[:BINDS_CbG]-()),
      size(()-[:BINDS_CbG]-(n1)),
      size((n1)-[:PARTICIPATES_GpPW]-()),
      size(()-[:PARTICIPATES_GpPW]-(n2)),
      size((n2)-[:PARTICIPATES_GpPW]-()),
      size(()-[:PARTICIPATES_GpPW]-(n3)),
      size((n3)-[:ASSOCIATES_DaG]-()),
      size(()-[:ASSOCIATES_DaG]-(n4))
    ] AS degrees, path
    RETURN
      count(path) AS PC,
      sum(reduce(pdp = 1.0, d in degrees| pdp * d ^ -0.4)) AS DWPC
    """
