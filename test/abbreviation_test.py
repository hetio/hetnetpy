import hetio.abbreviation


def test__get_duplicates():
    get_duplicates = hetio.abbreviation.get_duplicates
    assert get_duplicates(range(5)) == set()
    assert get_duplicates('abcd') == set()
    assert get_duplicates('abbccd') == {'b', 'c'}


def test__find_abbrevs():
    """For a list of strings (kinds), find the shortest unique abbreviation."""
    kind_to_abbrevs = [
        {
            'i': 'i',
            'am': 'a',
            'satoshi': 's',
        },
        {
            'plump': 'plu',
            'plaid': 'pla',
            'please': 'ple',
            'pain': 'pa',
        },
        {
            'bump': 'bump',
            'bum': 'bum',
            'blank': 'blan',
            'blast': 'blas',
        },
        {
            'i': 'i',
            'is': 'is',
            'satoshi': 's',
        },
        {
            'CAPS': 'caps',
            'caps_not': 'caps_',
        },
        {
            'A': 'a',
            'B': 'b',
            'C': 'c',
            'd': 'd',
        },
        {
            'PLump': 'plu',
            'plaid': 'pla',
            'PLEase': 'ple',
            'paIn': 'pa',
        },
    ]
    find_abbrevs = hetio.abbreviation.find_abbrevs
    for kind_to_abbrev in kind_to_abbrevs:
        assert kind_to_abbrev == find_abbrevs(kind_to_abbrev.keys())


def test__metaedges_from_metapath():
    """
    Get metaedge subsets from metapath abbreviation
    """
    metapath_to_metaedge = {
            'GpC1': ['GpC1'],
            'GiGpBP': ['GiG', 'GpBP'],
            'XxXyYyyYzzZZzZZZ': ['XxX', 'XyY', 'YyyY', 'YzzZZ', 'ZZzZZZ']
        }

    for metapath in metapath_to_metaedge:
        result = hetio.abbreviation.metaedges_from_metapath(metapath)
        assert result == metapath_to_metaedge[metapath]
