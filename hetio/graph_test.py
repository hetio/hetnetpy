import graph

def test_creation():
    metaedge_tuples = [
        ('compound', 'disease', 'indication', 'both'),
        ('disease', 'gene', 'association', 'both'),
        ('compound', 'gene', 'target', 'both'),
    ]
    metanode_ids = 'compound', 'disease', 'gene'
    metagraph = graph.MetaGraph.from_edge_tuples(metaedge_tuples)

    # check that nodes got added to metagraph_node_dict
    assert frozenset(metagraph.node_dict) == frozenset(metanode_ids)
    for metanode in metagraph.node_dict.values():
        assert isinstance(metanode, graph.MetaNode)

    # check that metanode.get_id() and hash(metanode) are working as expected
    for metanode_id in metanode_ids:
        metanode = metagraph.node_dict[metanode_id]
        assert metanode.identifier == metanode_id
        assert metanode.get_id() == metanode_id
        assert hash(metanode) == hash(metanode_id)

    g = graph.Graph(metagraph)
    g.add_node('multiple sclerosis', 'disease')
