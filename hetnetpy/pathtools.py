import functools
import itertools
import operator

from hetnetpy.hetnet import Node, Path


def DWPC(paths, damping_exponent, exclude_edges=set(), exclude_masked=True):
    """
    Calculated the degree-weighted path count of a path.
    https://dx.doi.org/10.1371/journal.pcbi.1004259#article1.body1.sec4.sec3.sec6.p1
    """
    kwargs = {
        "damping_exponent": damping_exponent,
        "exclude_edges": exclude_edges,
        "exclude_masked": exclude_masked,
    }
    degree_products = (path_degree_product(path, **kwargs) for path in paths)
    path_weights = (1.0 / degree_product for degree_product in degree_products)
    dwpc = sum(path_weights)
    return dwpc


def path_degree_product(
    path, damping_exponent, exclude_edges=set(), exclude_masked=True
):
    """
    Calculated the path degree product of a path.
    https://dx.doi.org/10.1371/journal.pcbi.1004259#article1.body1.sec4.sec3.sec6.p1
    """
    degrees = list()
    for edge in path:
        source_edges = edge.source.get_edges(edge.metaedge, exclude_masked)
        target_edges = edge.target.get_edges(edge.metaedge.inverse, exclude_masked)
        if exclude_edges:
            source_edges -= exclude_edges
            target_edges -= exclude_edges
        source_degree = len(source_edges)
        target_degree = len(target_edges)
        degrees.append(source_degree)
        degrees.append(target_degree)

    damped_degrees = [degree ** damping_exponent for degree in degrees]
    degree_product = functools.reduce(operator.mul, damped_degrees)
    return degree_product


def paths_from(
    graph,
    source,
    metapath,
    duplicates=False,
    masked=True,
    exclude_nodes=set(),
    exclude_edges=set(),
):
    """
    Return a list of Paths starting with source and following metapath.
    Setting duplicates False disallows paths with repeated nodes.
    Setting masked False disallows paths which traverse a masked node or edge.
    exclude_nodes and exclude_edges allow specification of additional nodes
    and edges beyond (or independent of) masked nodes and edges.
    """

    if not isinstance(source, Node):
        source = graph.node_dict[source]

    if masked and source.masked:
        return None

    if source in exclude_nodes:
        return None

    paths = list()

    for edge in source.edges[metapath[0]]:
        edge_target = edge.target
        if edge_target in exclude_nodes:
            continue
        if edge in exclude_edges:
            continue
        if not masked and (edge_target.masked or edge.masked):
            continue
        if not duplicates and edge_target == source:
            continue
        path = Path((edge,))
        paths.append(path)

    for i in range(1, len(metapath)):
        current_paths = list()
        metaedge = metapath[i]
        for path in paths:
            nodes = path.get_nodes()
            edges = path.target().edges[metaedge]
            for edge in edges:
                edge_target = edge.target
                if edge_target in exclude_nodes:
                    continue
                if edge in exclude_edges:
                    continue
                if not masked and (edge_target.masked or edge.masked):
                    continue
                if not duplicates and edge_target in nodes:
                    continue
                newpath = Path(path.edges + (edge,))
                current_paths.append(newpath)
        paths = current_paths

    return paths


def paths_between(
    graph,
    source,
    target,
    metapath,
    duplicates=False,
    masked=True,
    exclude_nodes=set(),
    exclude_edges=set(),
):
    """
    Retreive the paths starting with the node source and ending on the
    node target. Future implementations should split the metapath, computing
    paths_from the source and target and look for the intersection at the
    intermediary Node position.
    """

    if not isinstance(source, Node):
        source = graph.get_node(source)
    if not isinstance(target, Node):
        target = graph.get_node(target)

    if len(metapath) <= 1:
        paths = paths_from(
            graph, source, metapath, duplicates, masked, exclude_nodes, exclude_edges
        )
        paths = [path for path in paths if path.target() == target]
        return paths

    split_index = len(metapath) // 2

    get_metapath_from_edges = graph.metagraph.get_metapath_from_edges
    metapath_head = get_metapath_from_edges(metapath[:split_index])
    metapath_tail = get_metapath_from_edges(
        tuple(mp.inverse for mp in reversed(metapath[split_index:]))
    )
    paths_head = paths_from(
        graph, source, metapath_head, duplicates, masked, exclude_nodes, exclude_edges
    )
    paths_tail = paths_from(
        graph, target, metapath_tail, duplicates, masked, exclude_nodes, exclude_edges
    )

    node_intersect = set(path.target() for path in paths_head) & set(
        path.target() for path in paths_tail
    )

    head_dict = dict()
    for path in paths_head:
        path_target = path.target()
        if path_target in node_intersect:
            head_dict.setdefault(path_target, list()).append(path)

    tail_dict = dict()
    for path in paths_tail:
        path_target = path.target()
        if path_target in node_intersect:
            path = Path(path.inverse_edges())
            tail_dict.setdefault(path_target, list()).append(path)

    paths = list()
    for node in node_intersect:
        heads = head_dict[node]
        tails = tail_dict[node]
        for head, tail in itertools.product(heads, tails):
            path = Path(head.edges + tail.edges)
            if not duplicates:
                nodes = path.get_nodes()
                if len(set(nodes)) < len(nodes):
                    continue
            paths.append(path)

    return paths
