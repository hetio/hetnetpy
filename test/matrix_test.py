import os

import numpy
import pytest
import scipy.sparse

import hetnetpy.readwrite
from hetnetpy.matrix import metaedge_to_adjacency_matrix, sparsify_or_densify

directory = os.path.dirname(os.path.abspath(__file__))


def get_arrays(edge, dtype, dense_threshold):
    # Dictionary with tuples of matrix and percent nonzero
    adj_dict = {
        "GiG": (
            [
                [0, 0, 1, 0, 1, 0, 0],
                [0, 0, 1, 0, 0, 0, 0],
                [1, 1, 0, 1, 0, 0, 1],
                [0, 0, 1, 0, 0, 0, 0],
                [1, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 1, 0, 0, 0, 0],
            ],
            0.204,
        ),
        "GaD": ([[0, 1], [0, 1], [1, 0], [0, 1], [0, 0], [1, 1], [0, 0]], 0.429),
        "DlT": ([[0, 0], [1, 0]], 0.25),
        "TlD": ([[0, 1], [0, 0]], 0.25),
    }
    node_dict = {
        "G": ["CXCR4", "IL2RA", "IRF1", "IRF8", "ITCH", "STAT3", "SUMO1"],
        "D": ["Crohn's Disease", "Multiple Sclerosis"],
        "T": ["Leukocyte", "Lung"],
    }
    row_names = node_dict[edge[0]]
    col_names = node_dict[edge[-1]]
    matrix, density = adj_dict[edge]
    wrapper = scipy.sparse.csc_matrix if density < dense_threshold else numpy.array
    adj_matrix = wrapper(matrix, dtype=dtype)
    return row_names, col_names, adj_matrix


@pytest.mark.parametrize("dense_threshold", [0, 0.25, 0.5, 1])
@pytest.mark.parametrize("dtype", [numpy.bool_, numpy.int64, numpy.float64])
@pytest.mark.parametrize("test_edge", ["GiG", "GaD", "DlT", "TlD"])
def test_metaedge_to_adjacency_matrix(test_edge, dtype, dense_threshold):
    """
    Test the functionality of metaedge_to_adjacency_matrix in generating
    numpy arrays. Uses same test data as in test_degree_weight.py
    Figure 2D of Himmelstein & Baranzini (2015) PLOS Comp Bio.
    https://doi.org/10.1371/journal.pcbi.1004259.g002
    """
    path = os.path.join(directory, "data", "disease-gene-example-graph.json")
    graph = hetnetpy.readwrite.read_graph(path)
    row_names, col_names, adj_mat = metaedge_to_adjacency_matrix(
        graph, test_edge, dtype=dtype, dense_threshold=dense_threshold
    )
    exp_row, exp_col, exp_adj = get_arrays(test_edge, dtype, dense_threshold)

    assert row_names == exp_row
    assert col_names == exp_col
    assert type(adj_mat) == type(exp_adj)
    assert adj_mat.dtype == dtype
    assert adj_mat.shape == exp_adj.shape
    assert (adj_mat != exp_adj).sum() == 0


@pytest.mark.parametrize(
    "array,dense_threshold,expect_sparse",
    [
        ([[0, 0, 0, 0, 0, 0, 0]], 0, False),
        ([[0, 0, 0, 0, 0, 0, 0]], 0.3, True),
        ([[1, 1, 1, 1, 1, 1, 1]], 1, False),
        ([[1, 1, 1, 1, 1, 1, 1]], 2, True),
    ],
)
def test_sparsify_or_densify(array, dense_threshold, expect_sparse):
    # test with dense input
    array = numpy.array(array, dtype=numpy.bool_)
    output = sparsify_or_densify(array, dense_threshold)
    assert scipy.sparse.issparse(output) == expect_sparse

    # test with sparse input
    array = scipy.sparse.csc_matrix(array)
    output = sparsify_or_densify(array, dense_threshold)
    assert scipy.sparse.issparse(output) == expect_sparse
