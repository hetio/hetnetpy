import pytest

import hetio.hetnet


def test_creation():
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
    graph.add_edge(IL7R.get_id(), SPI1.get_id(), 'interacts', 'both')
    graph.add_edge(ms.get_id(), IL7R.get_id(), 'associates', 'both')

    # Enable in future to check that creating a duplicate edge throws an error
    with pytest.raises(AssertionError) as excinfo:
        graph.add_edge(IL7R.get_id(), SPI1.get_id(), 'transcribes', 'forward')
    excinfo.match(r'edge already exists')
    with pytest.raises(AssertionError):
        graph.add_edge(SPI1.get_id(), IL7R.get_id(), 'transcribes', 'backward')

    # Add bidirectional self loop
    graph.add_edge(IL7R.get_id(), IL7R.get_id(), 'interacts', 'both')

    # Test node and edge counts
    assert graph.n_nodes == 3
    assert graph.n_edges == 4
    assert graph.n_inverts == 3
    assert graph.n_nodes == len(list(graph.get_nodes()))
    assert graph.n_edges == len(list(graph.get_edges(exclude_inverts=True)))
    assert (graph.n_edges + graph.n_inverts == 
        len(list(graph.get_edges(exclude_inverts=False))))
