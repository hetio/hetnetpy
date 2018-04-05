import pathlib

import hetio.readwrite


def get_hetionet_metagraph():
    """
    Return the Hetionet v1.0 metagraph
    """
    directory = pathlib.Path(__file__).parent.absolute()
    path = directory.joinpath('data/hetionet-v1.0-metagraph.json')
    return hetio.readwrite.read_metagraph(path)


def test_extract_metapaths():
    """
    Test metapath extraction on the Hetionet v1.0 metagraph.
    """
    metagraph = get_hetionet_metagraph()

    # Test max_length=0
    metapaths = metagraph.extract_metapaths('Compound', 'Disease', max_length=0)
    assert metapaths == []

    # Test source-target-length combination where no metapaths exist
    metapaths = metagraph.extract_metapaths('Symptom', 'Pathway', max_length=2)
    assert metapaths == []

    # Test max_length=4: the metapaths used in Project Rephetio (note that
    # Project Rephetio excluded length 1 metapaths) resulting in 1206 metapaths.
    metapaths = metagraph.extract_metapaths('Compound', 'Disease', max_length=4)
    assert len(metapaths) == 1208
    assert len([m for m in metapaths if len(m) == 1]) == 2
    assert len([m for m in metapaths if len(m) == 2]) == 13
    assert len([m for m in metapaths if len(m) == 3]) == 121
    assert len([m for m in metapaths if len(m) == 4]) == 1072

    # Test unspecified target starting from Compound
    metapaths = metagraph.extract_metapaths('Compound', None, max_length=1)
    assert len(metapaths) == 8

    # Test unspecified target starting from Gene. Note the directed regulates
    # edge should result in two metapaths: Gr>G and G<rG
    metapaths = metagraph.extract_metapaths('Gene', None, max_length=1)
    assert len(metapaths) == 17

    # Test unspecified target starting from Symptom
    metapaths = metagraph.extract_metapaths('Symptom', None, max_length=3)
    assert len(metapaths) == 89
