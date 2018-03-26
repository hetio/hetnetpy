from collections import OrderedDict

import numpy
import scipy.sparse

import hetio.hetnet


def get_node_to_position(graph, metanode):
    """
    Given a metanode, return a dictionary of node to position
    """
    if not isinstance(metanode, hetio.hetnet.MetaNode):
        # metanode is a name
        metanode = graph.metagraph.node_dict[metanode]
    metanode_to_nodes = graph.get_metanode_to_nodes()
    nodes = sorted(metanode_to_nodes[metanode])
    node_to_position = OrderedDict((n, i) for i, n in enumerate(nodes))
    return node_to_position


def metaedge_to_adjacency_matrix(
        graph, metaedge, dtype=numpy.bool_, dense_threshold=0):
    """
    Returns an adjacency matrix where source nodes are rows and target
    nodes are columns.

    Parameters
    ==========
    graph : hetio.hetnet.graph
    metaedge : hetio.hetnet.MetaEdge
    dtype : type
    dense_threshold : float (0 ≤ dense_threshold ≤ 1)
        minimum proportion of nonzero values at which to output a dense matrix.
        Default of 0 ensures output is always dense.

    Returns
    =======
    row_names : list
    column_names : list
    matrix : numpy.ndarray or scipy.sparse
    """
    if not isinstance(metaedge, hetio.hetnet.MetaEdge):
        # metaedge is an abbreviation
        metaedge = graph.metagraph.metapath_from_abbrev(metaedge)[0]
    source_nodes = list(get_node_to_position(graph, metaedge.source))
    target_node_to_position = get_node_to_position(graph, metaedge.target)
    shape = len(source_nodes), len(target_node_to_position)
    row, col, data = [], [], []
    for i, source_node in enumerate(source_nodes):
        for edge in source_node.edges[metaedge]:
            row.append(i)
            col.append(target_node_to_position[edge.target])
            data.append(1)
    adjacency_matrix = scipy.sparse.csc_matrix(
        (data, (row, col)), shape=shape, dtype=dtype)
    adjacency_matrix = sparsify_or_densify(adjacency_matrix, dense_threshold)
    row_names = [node.identifier for node in source_nodes]
    column_names = [node.identifier for node in target_node_to_position]
    return row_names, column_names, adjacency_matrix


def sparsify_or_densify(matrix, dense_threshold=0.3):
    """
    Automatically convert a scipy.sparse to a numpy.ndarray if the percent
    nonzero is above a given threshold. Automatically convert a numpy.ndarray
    to scipy.sparse if the percent nonzero is below a given threshold.

    Parameters
    ==========
    matrix : numpy.ndarray or scipy.sparse
    dense_threshold : float (0 ≤ dense_threshold ≤ 1)
        minimum proportion of nonzero values at which to output a dense matrix.
        Setting to 0 ensures output is dense. Setting to 1 ensures output is
        sparse, unless matrix has no zero entries (use dense_threshold > 1) to
        guarantee sparse output.

    Returns
    =======
    matrix : numpy.ndarray or scipy.sparse
    """
    density = (matrix != 0).sum() / numpy.prod(matrix.shape)
    densify = density >= dense_threshold
    sparse_input = scipy.sparse.issparse(matrix)
    if sparse_input and densify:
        return matrix.toarray()
    if not sparse_input and not densify:
        return scipy.sparse.csc_matrix(matrix)
    return matrix
