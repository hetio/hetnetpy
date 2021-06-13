import os

import hetnetpy.readwrite

directory = os.path.dirname(os.path.abspath(__file__))

formats = ["json", "pkl"]

extensions = ["", ".gz", ".bz2", ".xz"]


def read_hetionet_v1_0_metagraph(path, extensions=None):
    """
    Test reading Hetionet v1.0 metagraph for extension options
    """
    if extensions is None:
        extensions = [""]
    for ext in extensions:
        metagraph = hetnetpy.readwrite.read_metagraph(path + ext)
        assert metagraph.n_nodes == 11
        assert metagraph.n_edges == 24


def test_metagraph_reading_from_urls():
    """
    Test reading metagraphs from URLs.
    """
    url = "https://github.com/{repo}/raw/{commit}/{path}".format(
        repo="hetio/hetnetpy",
        commit="main",
        path="test/data/hetionet-v1.0-metagraph.json",
    )
    read_hetionet_v1_0_metagraph(url, extensions)


def test_metagraph_reading_from_paths():
    """
    Test reading metagraphs from paths.
    """
    path = os.path.join(directory, "data", "hetionet-v1.0-metagraph.json")
    read_hetionet_v1_0_metagraph(path, extensions)


def test_metagraph_reading_no_abbrev():
    """
    Test reading metagraph without abbreviations from path.
    """
    path = os.path.join(directory, "data", "hetionet-v1.0-metagraph-no-abbrev.json")
    read_hetionet_v1_0_metagraph(path)
