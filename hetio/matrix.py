from collections import OrderedDict

import hetio.hetnet
import numpy
from scipy import sparse


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


def metaedge_to_adjacency_matrix(graph, metaedge, dtype=numpy.bool_,
                                 sparse_threshold=0):
    """
    Returns an adjacency matrix where source nodes are rows and target
    nodes are columns.

    Parameters
    ==========
    graph : hetio.hetnet.graph
    metaedge : hetio.hetnet.MetaEdge
    dtype : type
    sparse_threshold : float (0 < sparse_threshold < 1)
        sets the density threshold above which a sparse matrix will be
        converted to a dense automatically.
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
    adjacency_matrix = sparse.csc_matrix((data, (row, col)), shape=shape,
                                         dtype=dtype)
    adjacency_matrix = auto_convert(adjacency_matrix, sparse_threshold)
    row_names = [node.identifier for node in source_nodes]
    column_names = [node.identifier for node in target_node_to_position]
    return row_names, column_names, adjacency_matrix


def normalize(matrix, vector, axis, damping_exponent):
    """
    Normalize a 2D numpy.ndarray.

    Parameters
    ==========
    matrix : numpy.ndarray or scipy.sparse
    vector : numpy.ndarray
        Vector used for row or column normalization of matrix.
    axis : str
        'rows' or 'columns' for which axis to normalize
    damping_exponent : float
        exponent to use in scaling a node's row or column
    """
    assert matrix.ndim == 2
    assert vector.ndim == 1
    if damping_exponent == 0:
        return matrix
    with numpy.errstate(divide='ignore'):
        vector **= -damping_exponent
    vector[numpy.isinf(vector)] = 0
    vector = sparse.diags(vector)
    if axis == 'rows':
        # equivalent to `vector @ matrix` but returns sparse.csc not sparse.csr
        matrix = (matrix.transpose() @ vector).transpose()
    else:
        matrix = matrix @ vector
    return matrix


def auto_convert(matrix, threshold):
    """
    Automatically convert a scipy.sparse to a numpy.ndarray if the percent
    nonzero is above a given threshold. Automatically convert a numpy.ndarray
    to scipy.sparse if the percent nonzero is below a given threshold.

    Parameters
    ==========
    matrix : numpy.ndarray or scipy.sparse
    threshold : float (0 < threshold < 1)
        percent nonzero above which the matrix is converted to dense

    Returns
    =======
    matrix : numpy.ndarray or scipy.sparse
    """
    above_thresh = (matrix != 0).sum() / numpy.prod(matrix.shape) >= threshold
    if sparse.issparse(matrix) and above_thresh:
        return matrix.toarray()
    elif not above_thresh:
        return sparse.csc_matrix(matrix)
    return matrix


def copy_array(matrix, copy=True):
    """Returns a newly allocated array if copy is True"""
    assert matrix.ndim == 2
    assert matrix.dtype != 'O'  # Ensures no empty row
    if not sparse.issparse(matrix):
        assert numpy.isfinite(matrix).all()  # Checks NaN and Inf
    try:
        matrix[0, 0]  # Checks that there is a value in the matrix
    except IndexError:
        raise AssertionError("Array may have empty rows")

    mat_type = type(matrix)
    if mat_type == numpy.ndarray:
        mat_type = numpy.array
    matrix = mat_type(matrix, dtype=numpy.float64, copy=copy)
    return matrix
