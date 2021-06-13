import collections
import logging
import random

from hetnetpy.hetnet import Graph


def permute_graph(graph, multiplier=10, seed=0, metaedge_to_excluded=dict(), log=False):
    """
    Derive a permuted hetnet from an input hetnet. This method applies the
    XSwap algorithm separately for each metaedge. Hence, node degree is
    preserved for each type of edge. However, edges are randomized / shuffled.

    Users are recommended to interrogate the reported statistics to ensure that
    edges appear to be sufficiently randomized. Primarily, the number of edges
    of a given metaedge that remain unchanged from the original hetnet should
    have reached an assymptote. If the number of unchanged edges has not yet
    stabalized, further randomization is possible with this approach.

    Parameters
    ----------
    graph : hetnetpy.hetnet.Graph
        Input hetnet to create a permuted derivative from
    multiplier : int or float
        This is multiplied by the number of edges for each metaedge to
        determine the number of swaps to attempt.
    seed : int
        Seed to initialize Python random number generator. When creating many
        permuted hetnets, it's recommended to increment this number, such that
        each round of permutation shuffles edges in a different order.
    metaedge_to_excluded : dict (metaedge -> set)
        Edges to exclude. This argument has not been extensively used in
        practice.
    log : bool
        Whether to log diagnostic INFO via python's logging module.

    Returns
    -------
    permuted_graph : hetnetpy.hetnet.Graph
        A permuted hetnet derived from the input graph.
    stats : list of dicts
        A list where each item is a dictionary of permutation statistics at a
        checkpoint for a specific metaedge. These statistics allow tracking the
        progress of the permutation as the number of attempted swaps increases.
    """

    if log:
        logging.info("Creating permuted graph template")
    permuted_graph = Graph(graph.metagraph)
    for (metanode_identifier, node_identifier), node in graph.node_dict.items():
        permuted_graph.add_node(
            metanode_identifier, node_identifier, name=node.name, data=node.data
        )

    if log:
        logging.info("Retrieving graph edges")
    metaedge_to_edges = graph.get_metaedge_to_edges(exclude_inverts=True)

    if log:
        logging.info("Adding permuted edges")

    all_stats = list()
    for metaedge, edges in metaedge_to_edges.items():
        if log:
            logging.info(metaedge)

        excluded_pair_set = metaedge_to_excluded.get(metaedge, set())
        pair_list = [(edge.source.get_id(), edge.target.get_id()) for edge in edges]
        directed = metaedge.direction != "both"
        permuted_pair_list, stats = permute_pair_list(
            pair_list,
            directed=directed,
            multiplier=multiplier,
            excluded_pair_set=excluded_pair_set,
            seed=seed,
            log=log,
        )
        for stat in stats:
            stat["metaedge"] = metaedge
            stat["abbrev"] = metaedge.abbrev
        all_stats.extend(stats)

        for pair in permuted_pair_list:
            permuted_graph.add_edge(pair[0], pair[1], metaedge.kind, metaedge.direction)

    return permuted_graph, all_stats


def permute_pair_list(
    pair_list,
    directed=False,
    multiplier=10,
    excluded_pair_set=set(),
    seed=0,
    log=False,
    inplace=False,
):
    """
    Permute edges (of a single type) in a graph according to the XSwap function
    described in https://doi.org/f3mn58. This method selects two edges and
    attempts to swap their endpoints. If the swap would result in a valid edge,
    the swap proceeds. Otherwise, the swap is skipped. The end result is that
    node degree is preserved, but edges are shuffled, thereby losing their
    original meaning.

    Parameters
    ----------
    pair_list : list of tuples
        List of edges to permute. Each edge is represented as a (source,
        target) tuple. source and target represent nodes and can be any Python
        objects that define __eq__. In other words, this function does not
        assume any specific format for nodes. If the edges are from a bipartite
        or directed graph, then all tuples must have the same alignment. For
        example, if the edges represent the bipartite Compound-binds-Gene
        relationship, all tuples should be of the form (compound, gene) and not
        intermixed with (gene, compound) tuples. The only instance where order
        of the source and target is not important is for an undirected edge
        type where the source and target nodes are of the same type, such as
        Gene-interacts-Gene.
    directed : bool
        Whether the edge should be considered directed. If False, a swap that
        creates an a-b edge will be invalid if a b-a edge already exists.
    multiplier : int or float
        This is multiplied by the number of edges in pair_list to determine the
        number of swaps to attempt.
    excluded_pair_set : set of tuples:
        Set of possible edges to forbid. If a swap would create an edge in this
        set, it would be considered invalid and hence skipped.
    seed : int
        Seed to initialize Python random number generator.
    log : bool
        Whether to log diagnostic INFO via python's logging module.
    inplace : bool
        Whether to modify the edge list in place.

    Returns
    -------
    pair_list : list of tuples
        The permuted edges, derived from the input pair_list.
    stats : list of dicts
        A list where each item is a dictionary of permutation statistics at a
        checkpoint. Statistics are collected at 10 checkpoints, spaced evenly
        by the number of attempts.
    """
    random.seed(seed)

    if not inplace:
        pair_list = pair_list.copy()

    pair_set = set(pair_list)
    assert len(pair_set) == len(pair_list)

    edge_number = len(pair_list)
    n_perm = int(edge_number * multiplier)

    count_same_edge = 0
    count_self_loop = 0
    count_duplicate = 0
    count_undir_dup = 0
    count_excluded = 0

    if log:
        logging.info(
            "{} edges, {} permutations (seed = {}, directed = {}, {} excluded_edges)".format(
                edge_number, n_perm, seed, directed, len(excluded_pair_set)
            )
        )

    orig_pair_set = pair_set.copy()
    step = max(1, n_perm // 10)
    print_at = list(range(step, n_perm, step)) + [n_perm - 1]

    stats = list()
    for i in range(n_perm):

        # Same two random edges
        i_0 = random.randrange(edge_number)
        i_1 = random.randrange(edge_number)

        # Same edge selected twice
        if i_0 == i_1:
            count_same_edge += 1
            continue
        pair_0 = pair_list.pop(i_0)
        pair_1 = pair_list.pop(i_1 - 1 if i_0 < i_1 else i_1)

        new_pair_0 = pair_0[0], pair_1[1]
        new_pair_1 = pair_1[0], pair_0[1]

        valid = False
        for pair in new_pair_0, new_pair_1:
            if pair[0] == pair[1]:
                count_self_loop += 1
                break  # edge is a self-loop
            if pair in pair_set:
                count_duplicate += 1
                break  # edge is a duplicate
            if not directed and (pair[1], pair[0]) in pair_set:
                count_undir_dup += 1
                break  # edge is a duplicate
            if pair in excluded_pair_set:
                count_excluded += 1
                break  # edge is excluded
        else:
            # edge passed all validity conditions
            valid = True

        # If new edges are invalid
        if not valid:
            for pair in pair_0, pair_1:
                pair_list.append(pair)

        # If new edges are valid
        else:
            for pair in pair_0, pair_1:
                pair_set.remove(pair)
            for pair in new_pair_0, new_pair_1:
                pair_set.add(pair)
                pair_list.append(pair)

        if i in print_at:
            stat = collections.OrderedDict()
            stat["cumulative_attempts"] = i
            index = print_at.index(i)
            stat["attempts"] = (
                print_at[index] + 1
                if index == 0
                else print_at[index] - print_at[index - 1]
            )
            stat["complete"] = (i + 1) / n_perm
            stat["unchanged"] = len(orig_pair_set & pair_set) / len(pair_set)
            stat["same_edge"] = count_same_edge / stat["attempts"]
            stat["self_loop"] = count_self_loop / stat["attempts"]
            stat["duplicate"] = count_duplicate / stat["attempts"]
            stat["undirected_duplicate"] = count_undir_dup / stat["attempts"]
            stat["excluded"] = count_excluded / stat["attempts"]
            stats.append(stat)

            count_same_edge = 0
            count_self_loop = 0
            count_duplicate = 0
            count_undir_dup = 0
            count_excluded = 0

    assert len(pair_set) == edge_number
    return pair_list, stats
