import pytest

import hetnetpy.permute


@pytest.mark.parametrize(
    "edges,inplace",
    [
        ([(0, 0), (1, 1), (1, 2), (2, 3)], True),
        ([(0, 0), (1, 1), (1, 2), (2, 3)], False),
    ],
)
def test_permute_inplace(edges, inplace):
    old_edges = edges.copy()
    new_edges, stats = hetnetpy.permute.permute_pair_list(edges, inplace=inplace)
    assert old_edges != new_edges

    if inplace:
        assert edges == new_edges
    else:
        assert edges != new_edges
