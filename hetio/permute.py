import random

from hetio.hetnet import Graph

def permute_graph(graph, multiplier=10, seed=0, metaedge_to_excluded=dict(), verbose=False):
    """
    Shuffle edges within metaedge category. Preserves node degree but randomizes
    edges.
    """

    if verbose:
        print('Creating permuted graph template')
    permuted_graph = Graph(graph.metagraph)
    for (metanode_identifier, node_identifier), node in graph.node_dict.items():
        permuted_graph.add_node(
            metanode_identifier, node_identifier, name=node.name, data=node.data)

    if verbose:
        print('Retrieving graph edges')
    metaedge_to_edges = graph.get_metaedge_to_edges(exclude_inverts=True)

    if verbose:
        print('Adding permuted edges')
    for metaedge, edges in metaedge_to_edges.items():
        if verbose:
            print(metaedge)

        excluded_pair_set = metaedge_to_excluded.get(metaedge, set())
        pair_list = [(edge.source.get_id(), edge.target.get_id()) for edge in edges]
        directed = metaedge.direction != 'both'
        permuted_pair_list = permute_pair_list(
            pair_list, directed=directed, multiplier=multiplier,
            excluded_pair_set=excluded_pair_set, seed=seed, verbose=verbose)

        kind = metaedge.kind
        direction = metaedge.direction
        for pair in permuted_pair_list:
            permuted_graph.add_edge(pair[0], pair[1], kind, direction)

    return permuted_graph


def permute_pair_list(pair_list, directed=False, multiplier=10, excluded_pair_set=set(), seed=0, verbose=False):
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

    if verbose:
        orig_pair_set = pair_set.copy()
        print('{} edges, {} permutations (seed = {}, directed = {}, {} excluded_edges)'.format(
            edge_number, n_perm, seed, directed, len(excluded_pair_set)))
        step = max(1, n_perm // 10)
        print_at = list(range(0, n_perm, step)) + [n_perm - 1]

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

        # print updates
        if verbose and i in print_at:
            percent_done = 100.0 * float(i) / n_perm
            percent_same = 100.0 * float(len(orig_pair_set & pair_set)) / len(pair_set)
            print('{:.1f}% complete: {:.1f}% unchanged'.format(percent_done, percent_same))
            counts = [count_same_edge, count_self_loop, count_duplicate,
                      count_undir_dup, count_excluded]
            index = print_at.index(i)
            iterations = i if index == 0 else print_at[index] - print_at[index - 1]
            if iterations:
                percents = [100.0 * count / float(iterations) for count in counts]
                count_str = 'Counts last {} iterations: same_edge {:.1f}%; self_loop {:.1f}%; ' \
                            'duplicate {:.1f}%; undirected_duplicate {:.1f}%; excluded {:.1f}%'
                print(count_str.format(iterations, *percents))
            count_same_edge = 0
            count_self_loop = 0
            count_duplicate = 0
            count_undir_dup = 0
            count_excluded = 0

    assert len(pair_set) == edge_number
    return pair_list
