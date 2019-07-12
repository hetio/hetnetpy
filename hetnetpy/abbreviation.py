import collections

import regex

import hetnetpy.hetnet


def validate_abbreviations(metagraph):
    """Check that abbreviations are unambigious"""
    valid = True
    metanodes = set(metagraph.get_nodes())
    metaedges = set(metagraph.get_edges(exclude_inverts=False))

    # Duplicated metanode and metaedge kinds
    metanode_kinds = {metanode.identifier for metanode in metanodes}
    metaedge_kinds = {metaedge.kind for metaedge in metaedges}
    duplicated_kinds = metanode_kinds & metaedge_kinds
    if duplicated_kinds:
        msg = "Duplicated kinds between metanodes and metaedges: {}"
        print(msg.format(duplicated_kinds))
        valid = False

    # Check that metanodes do not have any duplicated abbreviations
    kind_to_abbrev = metagraph.kind_to_abbrev
    metanode_kind_to_abbrev = {
        k: v for k, v in kind_to_abbrev.items() if k in metanode_kinds
    }
    duplicated_metanode_abbrevs = get_duplicates(metanode_kind_to_abbrev.values())
    if duplicated_metanode_abbrevs:
        print("Duplicated metanode abbrevs:", duplicated_metanode_abbrevs)
        valid = False

    # Check metanode abbreviation violations
    for metanode in metanodes:
        abbrev = metanode.abbrev
        # metanode abbreviations should be uppercase
        if not abbrev.isupper():
            print("lowercase metanode abbreviation:", abbrev)
            valid = False
        # metanode abbreviation should not start with a digit
        if abbrev[0].isdigit():
            print("digit leading metanode abbreviation:", abbrev)
            valid = False

    # Check metaedge abbreviation violations
    for metaedge in metaedges:
        abbrev = metaedge.kind_abbrev
        # metaedge abbreviations should be lowercase
        if not abbrev.islower():
            print("uppercase metaedge abbreviation:", abbrev)
            valid = False
        # metaedge abbreviations should not contain digits
        if any(character.isdigit() for character in abbrev):
            print("digit in metaedge abbreviation:", abbrev)
            valid = False

    # Check that metaedges are not ambigious
    metaedge_abbrevs = [metaedge.abbrev for metaedge in metaedges]
    duplicated_meataedge_abbrevs = get_duplicates(metaedge_abbrevs)
    if duplicated_meataedge_abbrevs:
        msg = "Duplicated metaedge abbreviations: {}"
        print(msg.format(duplicated_meataedge_abbrevs))
        valid = False

    return valid


def get_duplicates(iterable):
    """Return a set of the elements which appear multiple times in iterable."""
    counter = collections.Counter(iterable)
    return {key for key, count in counter.items() if count > 1}


def find_abbrevs(kinds):
    """
    For a list of strings (kinds), find the shortest unique abbreviation.
    All returned abbrevs are lowercase.
    """
    kind_to_abbrev = {kind: kind[0].lower() for kind in kinds}
    duplicates = get_duplicates(kind_to_abbrev.values())
    while duplicates:
        for kind, abbrev in list(kind_to_abbrev.items()):
            if abbrev in duplicates and len(abbrev) < len(kind):
                abbrev += kind[len(abbrev)].lower()
                kind_to_abbrev[kind] = abbrev
        duplicates = get_duplicates(kind_to_abbrev.values())
    return kind_to_abbrev


def create_abbreviations(metagraph):
    """Creates abbreviations for node and edge kinds."""
    kind_to_abbrev = find_abbrevs(metagraph.node_dict.keys())
    kind_to_abbrev = {kind: abbrev.upper() for kind, abbrev in kind_to_abbrev.items()}

    edge_set_to_keys = dict()
    for edge in list(metagraph.edge_dict.keys()):
        key = frozenset(list(map(str.lower, edge[:2])))
        value = edge[2]
        edge_set_to_keys.setdefault(key, list()).append(value)

    for edge_set, keys in list(edge_set_to_keys.items()):
        key_to_abbrev = find_abbrevs(keys)
        for key, abbrev in list(key_to_abbrev.items()):
            previous_abbrev = kind_to_abbrev.get(key)
            if previous_abbrev and len(abbrev) <= len(previous_abbrev):
                continue
            kind_to_abbrev[key] = abbrev

    return kind_to_abbrev


def metaedges_from_metapath(abbreviation, standardize_by=None):
    """
    Get the abbreviated metaedges for an abbreviated metapath.
    Pass a hetnetpy.MetaGraph object to `standardize_by` to standardize metaedge
    abbreviations based on the non-inverted orietatation. Pass `text` to
    standardize by alphabetical/forward-direction arrangment of the
    abbreviation. Default (`None`) does not standardize.
    """
    if isinstance(standardize_by, hetnetpy.hetnet.MetaGraph):
        metapath = standardize_by.metapath_from_abbrev(abbreviation)
        return [metaedge.get_standard_abbrev() for metaedge in metapath]
    # Note that this is a valid regex module pattern but will not work in the
    # re module due to "look-behind requires fixed-width pattern".
    regex_string = r"(?<=^|[a-z<>])[A-Z][A-Z0-9]*[a-z<>]+[A-Z][A-Z0-9]*"
    pattern = regex.compile(regex_string)
    metaedge_abbrevs = pattern.findall(abbreviation, overlapped=True)
    if standardize_by is None:
        return metaedge_abbrevs
    elif standardize_by == "text":
        metaedge_abbrevs = [arrange_metaedge(x) for x in metaedge_abbrevs]
        return metaedge_abbrevs
    else:
        raise ValueError("Invalid value for standardize_by")


def metaedge_id_from_abbreviation(metagraph, abbreviation):
    """
    Return the metaedge_id corresponding to a metaedge abbreviation.
    """
    source_abbrev, target_abbrev = regex.split("[a-z<>]+", abbreviation)
    edge_abbrev = regex.search("[a-z<>]+", abbreviation).group()
    abbrev_to_kind = {v: k for k, v in metagraph.kind_to_abbrev.items()}
    source_kind = abbrev_to_kind[source_abbrev]
    target_kind = abbrev_to_kind[target_abbrev]
    metanode = metagraph.get_node(source_kind)
    for edge in metanode.edges:
        if edge.target.identifier != target_kind:
            continue
        if edge.kind_abbrev == edge_abbrev:
            kind = edge.kind
            break
    else:
        raise KeyError("edge abbreviation not found: {}".format(edge_abbrev))
    if ">" in abbreviation:
        direction = "forward"
    elif "<" in abbreviation:
        direction = "backward"
    else:
        direction = "both"
    return source_kind, target_kind, kind, direction


def arrange_metaedge(abbreviation):
    """
    Return the same metaedge abbreviation for a metaedge and its inverse. Uses
    alphabetical order for undirected metaedges. Uses forward direction for
    directed edges. Removes direction indicators (`<` or `>`).

    Referred to as the `text` method because it standardizes abbreviations
    using only the abbreviation text without requiring a metagraph.

    Deprecated::
    Use :func:`hetnet.MetaEdge.get_standard_abbrev` instead
    """
    source, target = regex.split("[a-z<>]+", abbreviation)
    edge = regex.search("[a-z]+", abbreviation).group()
    if "<" in abbreviation or (source > target):
        source, target = target, source
    return "{}{}{}".format(source, edge, target)
