import os

import pytest

import hetio.hetnet
import hetio.readwrite

from .readwrite_test import formats, extensions


def test_creation(tmpdir):
    # Convert py._path.local.LocalPath to a string
    tmpdir = str(tmpdir)

    # Construct metagraph
    metaedge_tuples = [
        ('compound', 'disease', 'treats', 'both'),
        ('disease', 'gene', 'associates', 'both'),
        ('compound', 'gene', 'targets', 'both'),
        ('gene', 'gene', 'interacts', 'both'),
        ('gene', 'gene', 'transcribes', 'forward'),
    ]
    metanode_ids = 'compound', 'disease', 'gene'
    metagraph = hetio.hetnet.MetaGraph.from_edge_tuples(metaedge_tuples)

    # check that nodes got added to metagraph_node_dict
    assert frozenset(metagraph.node_dict) == frozenset(metanode_ids)
    for metanode in metagraph.node_dict.values():
        assert isinstance(metanode, hetio.hetnet.MetaNode)

    # check that metanode.get_id() and hash(metanode) are working as expected
    for metanode_id in metanode_ids:
        metanode = metagraph.node_dict[metanode_id]
        assert metanode.identifier == metanode_id
        assert metanode.get_id() == metanode_id
        assert hash(metanode) == hash(metanode_id)

    # Check metanode and metaedge counts
    assert metagraph.n_nodes == len(metanode_ids)
    assert metagraph.n_edges == len(metaedge_tuples)
    assert metagraph.n_inverts == 4

    # Create a graph
    graph = hetio.hetnet.Graph(metagraph)

    # Create a node for multiple sclerosis
    ms = graph.add_node('disease', 'DOID:2377', 'multiple sclerosis')
    assert ms.metanode.identifier == 'disease'
    assert ms.identifier == 'DOID:2377'
    assert ms.name == 'multiple sclerosis'
    assert ms.get_id() == ('disease', 'DOID:2377')

    # Create gene nodes
    IL7R = graph.add_node('gene', 3575, 'IL7R')
    SPI1 = graph.add_node('gene', 6688, name='SPI1',
                          data={'description': 'Spi-1 proto-oncogene'})

    # Attempt to add a duplicate node
    with pytest.raises(AssertionError):
        graph.add_node('gene', 3575, 'IL7R')

    # Misordered node creation arguments
    with pytest.raises(KeyError):
        graph.add_node('DOID:2377', 'multiple sclerosis', 'disease')

    graph.add_edge(IL7R.get_id(), SPI1.get_id(), 'transcribes', 'forward')
    graph.add_edge(IL7R, SPI1.get_id(), 'interacts', 'both')
    graph.add_edge(ms.get_id(), IL7R, 'associates', 'both')

    # Enable in future to check that creating a duplicate edge throws an error
    with pytest.raises(AssertionError):
        graph.add_edge(IL7R, SPI1, 'transcribes', 'forward')
    # excinfo.match(r'edge already exists') # Disabled since new pytest feature
    with pytest.raises(AssertionError):
        graph.add_edge(SPI1, IL7R, 'transcribes', 'backward')

    # Add bidirectional self loop
    graph.add_edge(IL7R, IL7R, 'interacts', 'both')

    # Test node and edge counts
    assert graph.n_nodes == 3
    assert graph.n_edges == 4
    assert graph.n_inverts == 3
    assert graph.n_nodes == len(list(graph.get_nodes()))
    assert graph.n_edges == len(list(graph.get_edges(exclude_inverts=True)))
    assert (graph.n_edges + graph.n_inverts ==
            len(list(graph.get_edges(exclude_inverts=False))))

    # Test writing then reading graph
    for extension in extensions:
        for format_ in formats:
            ext = '.{}{}'.format(format_, extension)
            # Write metagraph
            path = os.path.join(tmpdir, 'metagraph' + ext)
            hetio.readwrite.write_metagraph(metagraph, path)
            hetio.readwrite.read_metagraph(path)
            # Write graph
            path = os.path.join(tmpdir, 'graph' + ext)
            hetio.readwrite.write_graph(graph, path)
            hetio.readwrite.read_graph(path)


def test_disase_gene_example():
    """
    Recreate hetnet from https://doi.org/10.1371/journal.pcbi.1004259.g002.
    """
    metaedge_id_GaD = 'Gene', 'Disease', 'association', 'both'
    metaedge_tuples = [
        metaedge_id_GaD,
        ('Gene', 'Tissue', 'expression', 'both'),
        ('Disease', 'Tissue', 'localization', 'both'),
        ('Gene', 'Gene', 'interaction', 'both'),
    ]
    metagraph = hetio.hetnet.MetaGraph.from_edge_tuples(metaedge_tuples)

    # Test metagraph getter methods
    # Test metagraph.get_metanode
    gene_metanode = metagraph.node_dict['Gene']
    assert metagraph.get_metanode(gene_metanode) == gene_metanode
    assert metagraph.get_metanode('Gene') == gene_metanode
    assert metagraph.get_metanode('G') == gene_metanode
    # Test metagraph.get_metaedge
    metaedge_GaD = metagraph.get_edge(metaedge_id_GaD)
    assert metagraph.get_metaedge(metaedge_GaD) == metaedge_GaD
    assert metaedge_id_GaD == metaedge_GaD.get_id()
    assert metagraph.get_metaedge(metaedge_id_GaD) == metaedge_GaD
    assert metagraph.get_metaedge('GaD') == metaedge_GaD
    # Test metagraph.get_metapath
    metapath_abbrev = 'TlDaGiG'
    metapath = metagraph.metapath_from_abbrev(metapath_abbrev)
    assert metagraph.get_metapath(metapath) == metapath
    assert metagraph.get_metapath(metapath_abbrev) == metapath
    assert metagraph.get_metapath(metapath.edges) == metapath

    # Create graph
    graph = hetio.hetnet.Graph(metagraph)
    nodes = dict()

    # Add gene nodes
    for symbol in ['STAT3', 'IRF1', 'SUMO1', 'IL2RA', 'IRF8', 'ITCH', 'CXCR4']:
        node = graph.add_node('Gene', symbol)
        nodes[symbol] = node

    # Add tissue nodes
    for tissue in ['Lung', 'Leukocyte']:
        node = graph.add_node('Tissue', tissue)
        nodes[tissue] = node

    # Add disease nodes
    for disease in ["Crohn's Disease", 'Multiple Sclerosis']:
        node = graph.add_node('Disease', disease)
        nodes[disease] = node

    assert graph.n_nodes == 11

    # Add GiG edges
    graph.add_edge(nodes['IRF1'], nodes['SUMO1'], 'interaction', 'both')
    graph.add_edge(nodes['IRF1'], nodes['IL2RA'], 'interaction', 'both')
    graph.add_edge(nodes['IRF1'], nodes['IRF8'], 'interaction', 'both')
    graph.add_edge(nodes['IRF1'], nodes['CXCR4'], 'interaction', 'both')
    graph.add_edge(nodes['ITCH'], nodes['CXCR4'], 'interaction', 'both')

    # Add GaD edges
    meta = 'association', 'both'
    graph.add_edge(nodes['IRF1'], nodes["Crohn's Disease"], *meta)
    graph.add_edge(nodes["Crohn's Disease"], nodes['STAT3'], *meta)
    graph.add_edge(nodes['STAT3'], nodes['Multiple Sclerosis'], *meta)
    graph.add_edge(nodes['IL2RA'], nodes['Multiple Sclerosis'], *meta)
    graph.add_edge(nodes['IRF8'], nodes['Multiple Sclerosis'], *meta)
    graph.add_edge(nodes['CXCR4'], nodes['Multiple Sclerosis'], *meta)

    # Add TeG edges
    graph.add_edge(nodes['IRF1'], nodes["Lung"], 'expression', 'both')
    graph.add_edge(nodes['IRF1'], nodes["Leukocyte"], 'expression', 'both')

    # Add DlT edges
    graph.add_edge(nodes['Multiple Sclerosis'], nodes["Leukocyte"],
                   'localization', 'both')

    assert graph.n_edges == 14
