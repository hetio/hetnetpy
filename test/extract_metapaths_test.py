import pathlib

import pytest

import hetnetpy.readwrite


def get_hetionet_metagraph():
    """
    Return the Hetionet v1.0 metagraph
    """
    directory = pathlib.Path(__file__).parent.absolute()
    path = directory.joinpath("data/hetionet-v1.0-metagraph.json")
    return hetnetpy.readwrite.read_metagraph(path)


def test_extract_metapaths():
    """
    Test metapath extraction on the Hetionet v1.0 metagraph.
    """
    metagraph = get_hetionet_metagraph()

    # Test max_length=0
    metapaths = metagraph.extract_metapaths("Compound", "Disease", max_length=0)
    assert metapaths == []

    # Test source-target-length combination where no metapaths exist
    metapaths = metagraph.extract_metapaths("Symptom", "Pathway", max_length=2)
    assert metapaths == []

    # Test max_length=4: the metapaths used in Project Rephetio (note that
    # Project Rephetio excluded length 1 metapaths resulting in 1206 metapaths).
    metapaths = metagraph.extract_metapaths("Compound", "Disease", max_length=4)
    assert len(metapaths) == 1208
    assert len([m for m in metapaths if len(m) == 1]) == 2
    assert len([m for m in metapaths if len(m) == 2]) == 13
    assert len([m for m in metapaths if len(m) == 3]) == 121
    assert len([m for m in metapaths if len(m) == 4]) == 1072

    # Test metapaths are sorted
    abbreviations = [str(metapath) for metapath in metapaths]
    assert abbreviations[:6] == ["CpD", "CtD", "CrCpD", "CrCtD", "CpDrD", "CtDrD"]

    # Test unspecified target starting from Compound
    metapaths = metagraph.extract_metapaths("Compound", None, max_length=1)
    assert len(metapaths) == 8

    # Test unspecified target starting from Gene. Note the directed regulates
    # edge should result in two metapaths: Gr>G and G<rG
    metapaths = metagraph.extract_metapaths("Gene", None, max_length=1)
    assert len(metapaths) == 17

    # Test unspecified target starting from Symptom
    metapaths = metagraph.extract_metapaths("Symptom", None, max_length=3)
    assert len(metapaths) == 89


@pytest.mark.parametrize(
    "max_length,exclude_inverts,n_metapaths",
    [
        (0, False, 0),
        (0, True, 0),
        (1, False, 44),
        (1, True, 24),
        (2, False, 484),
        (2, True, 266),
        (3, False, 4312),
        (3, True, 2205),
    ],
)
def test_extract_all_metapaths(max_length, exclude_inverts, n_metapaths):
    """
    Test metapath extraction on the Hetionet v1.0 metagraph. Note the expected
    values were computed using the extract_all_metapaths function and have not
    been independently verified.
    """
    metagraph = get_hetionet_metagraph()
    metapaths = metagraph.extract_all_metapaths(max_length, exclude_inverts)
    assert len(metapaths) == n_metapaths
