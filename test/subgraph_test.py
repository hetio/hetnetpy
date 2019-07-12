import os

import hetnetpy.readwrite

directory = os.path.dirname(os.path.abspath(__file__))


def get_disease_gene_example_hetnet():
    """
    Return the example disease gene example hetnet in
    https://doi.org/10.1371/journal.pcbi.1004259.g002
    """
    path = os.path.join(directory, "data", "disease-gene-example-graph.json")
    graph = hetnetpy.readwrite.read_graph(path)
    return graph


def test_subgraph_copy():
    """
    Test get_subgraph default mode to copy a graph.
    """
    graph = get_disease_gene_example_hetnet()
    subgraph = graph.get_subgraph()
    assert graph.n_nodes == subgraph.n_nodes
    assert graph.n_edges == subgraph.n_edges
    assert graph == subgraph
    assert graph.metagraph.kind_to_abbrev == subgraph.metagraph.kind_to_abbrev


def test_subgraph_node_subset():
    """
    Test get_subgraph with a specified subset of nodes.
    """
    graph = get_disease_gene_example_hetnet()
    nodes = [
        ("Gene", "STAT3"),
        ("Gene", "CXCR4"),
        ("Gene", "ITCH"),
        ("Disease", "Multiple Sclerosis"),
        ("Tissue", "Lung"),
    ]
    nodes = [graph.get_node(node) for node in nodes]
    subgraph = graph.get_subgraph(nodes=nodes)
    assert subgraph.metagraph == graph.metagraph
    assert subgraph.metagraph.kind_to_abbrev == graph.metagraph.kind_to_abbrev
    assert subgraph.n_nodes == 5
    assert subgraph.n_edges == 3


def test_subgraph_metanode_subset():
    """
    Test get_subgraph with a specified subset of metanodes.
    """
    graph = get_disease_gene_example_hetnet()
    metanodes = ["Disease", "Tissue"]
    metanodes = [graph.metagraph.get_node(mn) for mn in metanodes]
    subgraph = graph.get_subgraph(metanodes=metanodes)
    assert subgraph.metagraph.n_nodes == 2
    assert subgraph.metagraph.n_edges == 1
    assert subgraph.metagraph.kind_to_abbrev == {
        "Disease": "D",
        "Tissue": "T",
        "localization": "l",
    }
    assert subgraph.n_nodes == 4
    assert subgraph.n_edges == 1


def test_subgraph_node_metanode_subset():
    """
    Test get_subgraph with a specified subset of nodes.
    """
    graph = get_disease_gene_example_hetnet()
    metanodes = ["Gene", "Disease"]
    metanodes = [graph.metagraph.get_node(mn) for mn in metanodes]
    nodes = [
        ("Gene", "STAT3"),
        ("Gene", "CXCR4"),
        ("Gene", "ITCH"),
        ("Disease", "Multiple Sclerosis"),
    ]
    nodes = [graph.get_node(node) for node in nodes]
    subgraph = graph.get_subgraph(nodes=nodes, metanodes=metanodes)
    assert subgraph.metagraph.n_nodes == 2
    assert subgraph.metagraph.n_edges == 2
    assert subgraph.metagraph.kind_to_abbrev == {
        "Disease": "D",
        "Gene": "G",
        "association": "a",
        "interaction": "i",
    }
    assert subgraph.n_nodes == 4
    assert subgraph.n_edges == 3


def test_subgraph_metaedges_subset():
    """
    Test get_subgraph with a specified subset of metaedges.
    """
    graph = get_disease_gene_example_hetnet()
    metaedges = [("Gene", "Gene", "interaction", "both")]
    metaedges = [graph.metagraph.get_edge(me) for me in metaedges]
    subgraph = graph.get_subgraph(metaedges=metaedges)
    assert subgraph.metagraph.kind_to_abbrev == {"Gene": "G", "interaction": "i"}
    assert subgraph.metagraph.n_nodes == 1
    assert subgraph.metagraph.n_edges == 1
    assert subgraph.n_nodes == 7
    assert subgraph.n_edges == 5
