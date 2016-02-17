import collections
import random
import logging

from hetio.hetnet import Graph

def permute_graph(graph, multiplier=10, seed=0, metaedge_to_excluded=dict(), log=False):
    """
    Shuffle edges within metaedge category. Preserves node degree but randomizes
    edges.
    """

    if log:
        logging.info('Creating permuted graph template')
    permuted_graph = Graph(graph.metagraph)
    for (metanode_identifier, node_identifier), node in graph.node_dict.items():
        permuted_graph.add_node(
            metanode_identifier, node_identifier, name=node.name, data=node.data)

    if log:
        logging.info('Retrieving graph edges')
    metaedge_to_edges = graph.get_metaedge_to_edges(exclude_inverts=True)

    if log:
        logging.info('Adding permuted edges')

    all_stats = list()
    for metaedge, edges in metaedge_to_edges.items():
        if log:
            logging.info(metaedge)

        excluded_pair_set = metaedge_to_excluded.get(metaedge, set())
        pair_list = [(edge.source.get_id(), edge.target.get_id()) for edge in edges]
        directed = metaedge.direction != 'both'
        permuted_pair_list, stats = permute_pair_list(
            pair_list, directed=directed, multiplier=multiplier,
            excluded_pair_set=excluded_pair_set, seed=seed, log=log)
        for stat in stats:
            stat['metaedge'] = metaedge
            stat['abbrev'] = metaedge.get_abbrev()
        all_stats.extend(stats)

        for pair in permuted_pair_list:
            permuted_graph.add_edge(pair[0], pair[1], metaedge.kind, metaedge.direction)

    return permuted_graph, all_stats


def permute_pair_list(pair_list, directed=False, multiplier=10, excluded_pair_set=set(), seed=0, log=False):
    """
    If n_perm is not specific, perform 10 times the number of edges of permutations
    May not work for directed edges
    """
    random.seed(seed)

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
        logging.info('{} edges, {} permutations (seed = {}, directed = {}, {} excluded_edges)'.format(
            edge_number, n_perm, seed, directed, len(excluded_pair_set)))

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
            stat['cumulative_attempts'] = i
            index = print_at.index(i)
            stat['attempts'] = print_at[index] + 1 if index == 0 else print_at[index] - print_at[index - 1]
            stat['complete'] = (i + 1) / n_perm
            stat['unchanged'] = len(orig_pair_set & pair_set) / len(pair_set)
            stat['same_edge'] = count_same_edge / stat['attempts']
            stat['self_loop'] = count_self_loop / stat['attempts']
            stat['duplicate'] = count_duplicate / stat['attempts']
            stat['undirected_duplicate'] = count_undir_dup / stat['attempts']
            stat['excluded'] = count_excluded / stat['attempts']
            stats.append(stat)

            count_same_edge = 0
            count_self_loop = 0
            count_duplicate = 0
            count_undir_dup = 0
            count_excluded = 0

    assert len(pair_set) == edge_number
    return pair_list, stats
